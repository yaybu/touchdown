# Copyright 2014 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from inspect import isgeneratorfunction
import logging

from botocore.exceptions import ClientError

import jmespath

from touchdown.core import errors, serializers, resource
from touchdown.core.action import Action
from touchdown.core.plan import Present
from touchdown.core.diff import DiffSet


logger = logging.getLogger(__name__)


class Resource(resource.Resource):

    def matches(self, runner, remote):
        return DiffSet(runner, self, remote).matches()


class Waiter(Action):

    def __init__(self, plan, description, waiter):
        super(Waiter, self).__init__(plan)
        self.description = description
        self.waiter = waiter

    def ready(self):
        waiter = self.plan.get_waiter(self.waiter)
        filters = self.plan.get_describe_filters()
        acceptors = list(waiter.config.acceptors)
        response = waiter._operation_method(**filters)

        current_state = 'waiting'

        for acceptor in acceptors:
            if acceptor.matcher_func(response):
                current_state = acceptor.state
                break
        else:
            if 'Error' in response:
                raise errors.Error('Unexpected error encountered.')

        if current_state == 'success':
            return True

        if current_state == 'failure':
            raise errors.Error('Waiter encountered a terminal failure state')

        return False

    def run(self):
        filters = self.plan.get_describe_filters()
        logger.debug("Waiting with waiter {} and filters {}".format(self.waiter, filters))
        waiter = self.plan.client.get_waiter(self.waiter)
        waiter.wait(**filters)
        self.plan.object = self.plan.describe_object()


class GenericAction(Action):

    is_creation_action = False

    def __init__(self, plan, description, func, serializer=None, **kwargs):
        super(GenericAction, self).__init__(plan)
        self.func = func
        self._description = description
        if serializer:
            self.serializer = serializer
        else:
            self.serializer = serializers.Dict(**{k: v if isinstance(v, serializers.Serializer) else serializers.Const(v) for (k, v) in kwargs.items()})

    @property
    def description(self):
        yield self._description

    def run(self):
        logger.debug("Calling {}".format(self.func))

        params = self.serializer.render(self.runner, self.resource)
        logger.debug("Invoking with params {}".format(params))

        object = self.func(**params)

        if self.is_creation_action:
            if self.plan.create_response == "full-description":
                self.plan.object = jmespath.search(
                    getattr(self.plan, "create_envelope", self.plan.describe_envelope[:-1]),
                    object,
                )
            else:
                if self.plan.create_response == "id-only":
                    self.plan.object = {
                        self.plan.key: object[self.plan.key]
                    }
                self.plan.object = self.plan.describe_object()


class PostCreation(Action):

    description = ["Sanity check created resource"]

    def run(self):
        self.plan.object = self.plan.describe_object()
        if not self.plan.object:
            raise errors.Error("Object creation failed")


class SetTags(Action):

    def __init__(self, plan, tags):
        super(SetTags, self).__init__(plan)
        self.tags = tags

    @property
    def description(self):
        yield "Set tags on resource {}".format(self.resource.name)
        for k, v in self.tags.items():
            yield "{} = {}".format(k, v)

    def run(self):
        self.plan.client.create_tags(
            Resources=[self.plan.resource_id],
            Tags=[{"Key": k, "Value": v} for k, v in self.tags.items()],
        )


class SimpleDescribe(object):

    name = "describe"

    describe_filters = None
    describe_notfound_exception = None

    signature = (
        Present('name'),
    )

    _client = None

    def __init__(self, runner, resource):
        super(SimpleDescribe, self).__init__(runner, resource)
        self.object = {}

    @property
    def session(self):
        return self.parent.session

    @property
    def client(self):
        session = self.session
        if not self._client:
            self._client = session.create_client(
                service_name=self.service_name,
                region_name=session.region,
                aws_access_key_id=session.access_key_id,
                aws_secret_access_key=session.secret_access_key,
                aws_session_token=session.session_token,
            )
        return self._client

    def get_describe_filters(self):
        return {
            self.key: self.resource.name
        }

    def describe_object_matches(self, object):
        return True

    def describe_object(self):
        logger.debug("Trying to find AWS object for resource {} using {}".format(self.resource, self.describe_action))

        if self.describe_filters is not None:
            filters = self.describe_filters
        else:
            filters = self.get_describe_filters()

        if filters is None:
            logger.debug("Could not generate valid filters - this generally means we've determined the object cant exist!")
            return {}

        logger.debug("Filters are: {}".format(filters))

        if self.client.can_paginate(self.describe_action):
            paginator = self.client.get_paginator(self.describe_action)

            def _():
                try:
                    for page in paginator.paginate(**filters):
                        for result in jmespath.search(self.describe_envelope, page):
                            yield result
                except ClientError as e:
                    if e.response['Error']['Code'] == self.describe_notfound_exception:
                        raise StopIteration
                    raise errors.Error("{}: {}".format(self.resource, e))
                except Exception as e:
                    raise errors.Error("{}: {}".format(self.resource, e))

            results = _()
        else:
            try:
                results = getattr(self.client, self.describe_action)(**filters)
            except ClientError as e:
                if e.response['Error']['Code'] == self.describe_notfound_exception:
                    return {}
                raise errors.Error("{}: {}".format(self.resource, e))
            except Exception as e:
                raise errors.Error("{}: {}".format(self.resource, e))

            results = jmespath.search(self.describe_envelope, results)
            if not isgeneratorfunction(results) and not isinstance(results, list):
                results = [results]

        objects = list(filter(self.describe_object_matches, results))

        if len(objects) > 1:
            raise errors.Error("Expecting to find one {}, but found {}".format(self.resource, len(objects)))

        if len(objects) == 1:
            logger.debug("Found object {}".format(objects[0]))
            return objects[0]

        return {}

    def generic_action(self, description, callable, serializer=None, **kwargs):
        return GenericAction(
            self,
            description,
            callable,
            serializer,
            **kwargs
        )

    def get_waiter(self, description, waiter):
        return Waiter(self, description, waiter)

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            raise errors.NotFound("Object '{}' could not be found, and is not scheduled to be created".format(self.resource))

        return []

    @property
    def resource_id(self):
        if self.key in self.object:
            return self.object[self.key]
        return None


class SimpleApply(SimpleDescribe):

    name = "apply"
    default = True

    waiter = None
    update_action = None
    create_serializer = None
    create_response = "full-description"

    def get_create_serializer(self):
        return serializers.Resource()

    def create_object(self):
        g = self.generic_action(
            "Creating {}".format(self.resource),
            getattr(self.client, self.create_action),
            self.get_create_serializer(),
        )
        g.is_creation_action = True
        return g

    def update_tags(self):
        if getattr(self.resource, "immutable_tags", False) and self.object:
            return

        if hasattr(self.resource, "tags"):
            local_tags = dict(self.resource.tags)
            local_tags['Name'] = self.resource.name
            remote_tags = dict((v["Key"], v["Value"]) for v in self.object.get('Tags', []))

            tags = {}
            for k, v in local_tags.items():
                if k not in remote_tags or remote_tags[k] != v:
                    tags[k] = v

            if tags:
                yield SetTags(
                    self,
                    tags=tags,
                )

    def update_object(self):
        if self.update_action and self.object:
            logger.debug("Checking resource {} for changes".format(self.resource))

            description = ["Updating {}".format(self.resource)]
            local = serializers.Resource(mode="update")
            for k, v in local.render(self.runner, self.resource).items():
                if k not in self.object:
                    continue
                if v != self.object[k]:
                    logger.debug("Resource field {} has changed ({} != {})".format(k, v, self.object[k]))
                    description.append("{} => {}".format(k, v))

            logger.debug("Resource has {} differences".format(len(description) - 1))

            if len(description) > 1:
                yield self.generic_action(
                    description,
                    getattr(self.client, self.update_action),
                    serializer=local
                )

    def get_actions(self):
        self.object = self.describe_object()

        created = False

        if not self.object:
            logger.debug("Cannot find AWS object for resource {} - creating one".format(self.resource))
            self.object = {}
            yield self.create_object()
            created = True

        if created:
            if self.waiter:
                waiter = self.get_waiter(
                    ["Waiting for resource to exist"],
                    self.waiter,
                )
                if created or not waiter.ready():
                    yield waiter

            if self.create_response != "full-description" and not self.waiter:
                yield PostCreation(self)

        for change in self.update_tags():
            yield change

        logger.debug("Looking for changes to apply")
        for action in self.update_object():
            yield action


class SimpleDestroy(SimpleDescribe):

    name = "destroy"

    waiter = None

    def get_destroy_serializer(self):
        return serializers.Dict(**{self.key: self.resource_id})

    def destroy_object(self):
        yield self.generic_action(
            "Destroy {}".format(self.resource),
            getattr(self.client, self.destroy_action),
            self.get_destroy_serializer(),
        )

        if self.waiter:
            yield self.get_waiter(
                ["Waiting for resource to go away"],
                self.waiter,
            )

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            logger.debug("Resource '{}' not found - assuming already destroyed".format(self.resource))
            return

        for action in self.destroy_object():
            yield action
