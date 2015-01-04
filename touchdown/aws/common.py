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

from touchdown.core import argument, errors
from touchdown.core.action import Action
from touchdown.core.renderable import ResourceId, render
from touchdown.core.target import Present


logger = logging.getLogger(__name__)


class hd(dict):

    def __hash__(self):
        return hash(frozenset(self.items()))


def resource_to_dict(runner, resource, mode="create"):
    params = {}
    for name, arg in resource.arguments:
        if not arg.present(resource):
            continue
        if not hasattr(arg, "aws_field"):
            continue
        if mode == "create" and not getattr(arg, "aws_create", True):
            continue
        if mode == "update" and not getattr(arg, "aws_update", True):
            continue

        value = getattr(resource, name)
        if isinstance(arg, argument.Resource):
            value = ResourceId(resource)
        elif isinstance(arg, argument.ResourceList):
            value = [ResourceId(r) for r in value]
        elif isinstance(arg, argument.IPNetwork):
            value = str(value)

        params[arg.aws_field] = value

    return params


class GenericAction(Action):

    def __init__(self, runner, target, description, func, waiter, *args, **kwargs):
        super(GenericAction, self).__init__(runner, target)
        self.func = func
        self._description = description
        self.waiter = waiter
        self.args = args
        self.kwargs = kwargs

    @property
    def description(self):
        yield self._description

    def run(self):
        params = {}
        for k, v in self.kwargs.items():
            params[k] = render(self.runner, v)
        self.func(**params)

        if self.waiter:
            waiter = self.target.client.get_waiter(self.waiter)
            waiter.wait(**self.target.get_describe_filters())


class SetTags(Action):

    def __init__(self, runner, target, tags):
        super(SetTags, self).__init__(runner, target)
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


class SimpleApply(object):

    """
    A simple data-driven resource for AWS api's that a moderately well behaved.

    For example::

        cache CacheClusterApply(SimplyApply, Target):
            resource = CacheCluster
            create_action = "create_cache_cluster"
            describe_action = "describe_cache_cluster"
            describe_list_key = "CacheClusters"
            key = 'CacheClusterId'
    """

    name = "apply"
    default = True

    waiter = None
    get_action = None
    update_action = None
    describe_notfound_exception = None
    create_serializer = None

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
                # aws_session_token
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

    def get_create_args(self):
        return resource_to_dict(self.runner, self.resource)

    def create_object(self):
        return self.generic_action(
            "Creating {}".format(self.resource),
            getattr(self.client, self.create_action),
            self.waiter,
            **self.get_create_args()
        )

    def generic_action(self, description, callable, *args, **kwargs):
        return GenericAction(
            self.runner,
            self,
            description,
            callable,
            None,
            *args,
            **kwargs
        )

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            logger.debug("Cannot find AWS object for resource {} - creating one".format(self.resource))
            self.object = {}
            yield self.create_object()

        logger.debug("Looking for changes to apply")
        for action in self.update_object():
            yield action

    def update_object(self):
        if self.update_action and self.object:
            logger.debug("Checking resource {} for changes".format(self.resource))

            description = ["Updating {}".format(self.resource)]
            local = resource_to_dict(self.runner, self.resource, mode="update")
            for k, v in local.items():
                if k not in self.object:
                    continue
                v = render(self.runner, v)
                if v != self.object[k]:
                    logger.debug("Resource field {} has changed ({} != {})".format(k, v, self.object[k]))
                    # FIXME: Make this smarter... Where referring to
                    # renderables can show a hint
                    # Instead of Foo => None it should show
                    # Foo => ResourceId(some_subnet)
                    description.append("{} => {}".format(k, v))

            logger.debug("Resource has {} differences".format(len(description) - 1))

            if len(description) > 1:
                yield self.generic_action(
                    description,
                    getattr(self.client, self.update_action),
                    **local
                )

        if hasattr(self.resource, "tags"):
            local_tags = dict(self.resource.tags)
            local_tags['name'] = self.resource.name

            remote_tags = dict((v["Key"], v["Value"]) for v in self.object.get('Tags', []))

            tags = {}
            for k, v in local_tags.items():
                if k not in remote_tags or remote_tags[k] != v:
                    tags[k] = v

            if tags:
                yield SetTags(
                    self.runner,
                    self,
                    tags={"name": self.resource.name}
                )

    @property
    def resource_id(self):
        if self.key in self.object:
            return self.object[self.key]
        return None
