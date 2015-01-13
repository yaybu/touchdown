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

import logging

from botocore.exceptions import ClientError

from touchdown.core import errors, serializers
from touchdown.core.action import Action
from touchdown.core.target import Present


logger = logging.getLogger(__name__)


class GenericAction(Action):

    is_creation_action = False

    def __init__(self, target, description, func, waiter=None, serializer=None, **kwargs):
        super(GenericAction, self).__init__(target)
        self.func = func
        self._description = description
        self.waiter = waiter
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

        self.func(**params)

        if self.waiter:
            filters = self.target.get_describe_filters()
            logger.debug("Waiting with waiter {} and filters {}".format(self.waiter, filters))
            waiter = self.target.client.get_waiter(self.waiter)
            waiter.wait(**filters)

        if self.is_creation_action:
            self.target.object = self.target.describe_object()
            if not self.target.object:
                raise errors.Error("Object creation failed")


class SetTags(Action):

    def __init__(self, target, tags):
        super(SetTags, self).__init__(target)
        self.tags = tags

    @property
    def description(self):
        yield "Set tags on resource {}".format(self.resource.name)
        for k, v in self.tags.items():
            yield "{} = {}".format(k, v)

    def run(self):
        self.target.client.create_tags(
            Resources=[self.target.resource_id],
            Tags=[{"Key": k, "Value": v} for k, v in self.tags.items()],
        )


class SimpleDescribe(object):

    name = "describe"

    get_action = None
    describe_notfound_exception = None

    signature = (
        Present('name'),
    )

    _client = None

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

    def describe_object(self):
        if self.get_action:
            logger.debug("Trying to find AWS object for resource {} using {}".format(self.resource, self.get_action))
            return getattr(self.client, self.get_action)(**{self.key: self.resource.name})

        logger.debug("Trying to find AWS object for resource {} using {}".format(self.resource, self.describe_action))

        filters = self.get_describe_filters()
        logger.debug("Filters are: {}".format(filters))

        try:
            results = getattr(self.client, self.describe_action)(**filters)
        except ClientError as e:
            if e.response['Error']['Code'] == self.describe_notfound_exception:
                return {}
            raise

        objects = results[self.describe_list_key]

        if len(objects) > 1:
            raise errors.Error("Expecting to find one {}, but found {}".format(self.resource, len(objects)))

        if len(objects) == 1:
            logger.debug("Found object {}".format(objects[0][self.key]))
            return objects[0]

        return {}

    def generic_action(self, description, callable, waiter=None, serializer=None, **kwargs):
        return GenericAction(
            self,
            description,
            callable,
            waiter,
            serializer,
            **kwargs
        )

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            raise errors.NotFound("Object '{}' could not be found, and is not scheduled to be created")

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

    def get_create_serializer(self):
        return serializers.Resource()

    def create_object(self):
        g = self.generic_action(
            "Creating {}".format(self.resource),
            getattr(self.client, self.create_action),
            self.waiter,
            self.get_create_serializer(),
        )
        g.is_creation_action = True
        return g

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

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            logger.debug("Cannot find AWS object for resource {} - creating one".format(self.resource))
            self.object = {}
            yield self.create_object()

        logger.debug("Current state for {} is {}".format(self.resource, self.object))

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
            self.waiter,
            self.get_destroy_serializer(),
        )

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            logger.debug("Resource '{}' not found - assuming already destroyed".format(self.resource))
            return

        for action in self.destroy_object():
            yield action
