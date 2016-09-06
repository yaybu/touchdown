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

import datetime
import logging
import time

import jmespath
from botocore.exceptions import ClientError

from touchdown.core import errors, resource, serializers
from touchdown.core.action import Action
from touchdown.core.plan import Present

logger = logging.getLogger(__name__)


class Resource(resource.Resource):

    def matches(self, runner, remote):
        d = serializers.Resource().diff(runner, self, remote)
        return d.matches()


class Waiter(Action):

    def __init__(self, plan, description, waiter, eventual_consistency_threshold):
        super(Waiter, self).__init__(plan)
        self.description = description
        self.waiter = self.plan.client.get_waiter(waiter)
        self.eventual_consistency_threshold = eventual_consistency_threshold

    def get_waiter_filters(self):
        ''' Allow subclasses to use a different filter for their waiter to their describer '''
        return self.plan.get_describe_filters()

    def get_filtered_response(self, response):
        ''' Allow subclasses to filter out unrelated responses '''
        return response

    def poll(self):
        filters = self.get_waiter_filters()
        logger.debug('Polling with waiter {} and filters {}'.format(self.waiter, filters))
        return self.get_filtered_response(self.waiter._operation_method(**filters))

    def ready(self):
        acceptors = list(self.waiter.config.acceptors)
        for i in range(self.eventual_consistency_threshold):
            current_state = 'waiting'
            response = self.poll()
            for acceptor in acceptors:
                if acceptor.matcher_func(response):
                    current_state = acceptor.state
                    break
            else:
                if 'Error' in response:
                    raise errors.Error('Unexpected error encountered. {}'.format(response['Error']))

            if current_state == 'failure':
                raise errors.Error('Waiter encountered a terminal failure state')

            if current_state != 'success':
                return False

        return True

    def run(self):
        last = datetime.datetime.now()
        for i in range(self.waiter.config.max_attempts):
            if self.ready():
                break

            now = datetime.datetime.now()
            if (now - last).total_seconds() > 60:
                attempts_remaining = self.waiter.config.max_attempts - i
                time_remaining = attempts_remaining * self.waiter.config.delay

                self.plan.ui.echo('Still waiting for {}. {} till timeout occurs.'.format(
                    self.plan.resource,
                    datetime.timedelta(seconds=time_remaining),
                ))
                last = now

            time.sleep(self.waiter.config.delay)

        else:
            raise errors.Error('Operation took too long to complete')


class GenericAction(Action):

    is_creation_action = False

    def __init__(self, plan, description, func, serializer=None, **kwargs):
        super(GenericAction, self).__init__(plan)
        self.func = func
        self._description = description
        if serializer:
            self.serializer = serializer
        else:
            self.serializer = serializers.Dict(
                **{k: v if isinstance(v, serializers.Serializer) else serializers.Const(v) for (k, v) in kwargs.items()}
            )

    @property
    def description(self):
        if isinstance(self._description, list):
            return self._description
        return [self._description]

    def get_arguments(self):
        return self.serializer.render(self.runner, self.resource)

    def run(self):
        logger.debug('Calling {}'.format(self.func))

        params = self.get_arguments()
        logger.debug('Invoking with params {}'.format(params))

        return self.func(**params)


class CreateAction(Action):

    def __init__(self, plan, action):
        self.plan = plan
        self.action = action

    @property
    def description(self):
        return self.action.description

    def run(self):
        result = self.action.run()

        if self.plan.create_response == 'full-description':
            self.plan.object = jmespath.search(
                getattr(self.plan, 'create_envelope', self.plan.describe_envelope[:-1]),
                result,
            )
        elif self.plan.create_response == 'id-only':
            self.plan.object = {
                self.plan.key: result[self.plan.key]
            }
        else:
            self.plan.object = self.plan.describe_object()

        return result


class RetryAction(Action):

    def __init__(self, plan, action):
        self.plan = plan
        self.action = action

    @property
    def description(self):
        return self.action.description

    def should_retry(self, response):
        retryable = getattr(self.plan, 'retryable', {})
        if not response['Error']['Code'] in retryable:
            return False
        msgs = retryable[response['Error']['Code']]
        if not msgs:
            return True
        for msg in msgs:
            if msg == response['Error']['Message']:
                return True
        return False

    def run(self):
        for i in range(10):
            try:
                return self.action.run()
            except ClientError as e:
                if not self.should_retry(e.response):
                    raise
            time.sleep(i)
        raise e


class PostCreation(Action):

    description = ['Sanity check created resource']

    def run(self):
        self.plan.object = self.plan.get_object_by_id(self.plan.resource_id)
        if not self.plan.object:
            raise errors.Error('Object creation failed')


class PrintMetadata(Action):

    @property
    def description(self):
        if not self.plan.resource_id:
            yield 'Display resource metadata'
            return
        yield 'Resource metadata:'
        yield '{} = {}'.format(self.plan.key, self.plan.resource_id)

    def run(self):
        pass


class RefreshMetadata(Action):

    description = ['Refresh resource metadata']

    def run(self):
        self.plan.object = self.plan.get_object_by_id(self.plan.resource_id)


class SetTags(Action):

    def __init__(self, plan, tags):
        super(SetTags, self).__init__(plan)
        self.tags = tags

    @property
    def description(self):
        yield 'Set tags on resource {}'.format(self.resource.name)
        for k, v in self.tags.items():
            yield '{} = {}'.format(k, v)

    def run(self):
        self.plan.client.create_tags(
            Resources=[self.plan.resource_id],
            Tags=[{'Key': k, 'Value': v} for k, v in self.tags.items()],
        )


class SimplePlan(object):

    _client = None
    api_version = None

    @property
    def session(self):
        return self.parent.session

    @property
    def client(self):
        session = self.session
        if not self._client:
            self._client = session.create_client(self.service_name, self.api_version)
        return self._client


class SimpleDescribe(SimplePlan):

    name = 'describe'

    describe_filters = None
    describe_notfound_exception = None

    signature = (
        Present('name'),
    )

    GenericAction = GenericAction

    def __init__(self, runner, resource):
        super(SimpleDescribe, self).__init__(runner, resource)
        self.object = {}

    def get_describe_filters(self):
        return {
            self.key: self.resource.name
        }

    def get_paginated(self, action, **filters):
        '''
        Some ``botocore`` API's have paginators, some do not. This wrapper just
        gives them all a consistent API.

        Where a ``botocore`` paginator is available call it. In this case the
        function will return an iterator of pages. Otherwise return a list of 1
        that contains the results of calling the API directly.
        '''
        if self.client.can_paginate(action):
            paginator = self.client.get_paginator(self.describe_action)
            return paginator.paginate(**filters)
        return [getattr(self.client, self.describe_action)(**filters)]

    def unwrap(self, paginated, expression):
        '''
        Unwinds a paginator and applies a jmespath expression to each page.
        '''
        try:
            for page in paginated:
                for row in jmespath.search(expression, page) or []:
                    yield row
        except ClientError as e:
            if e.response['Error']['Code'] == self.describe_notfound_exception:
                raise StopIteration

    def get_possible_objects(self):
        '''
        Apply server side filters to retrieve a list of objects that might
        match ``self.resource``.
        '''

        logger.debug('Trying to find AWS objects for resource {} using {}'.format(self.resource, self.describe_action))

        if self.describe_filters is not None:
            filters = self.describe_filters
        else:
            filters = self.get_describe_filters()

        if filters is None:
            logger.debug('Could not generate valid filters - this generally means we\'ve determined the object cant exist!')
            return []

        logger.debug('Filters are: {}'.format(filters))

        try:
            results = self.unwrap(
                self.get_paginated(self.describe_action, **filters),
                self.describe_envelope,
            )
        except ClientError as e:
            if e.response['Error']['Code'] == self.describe_notfound_exception:
                return []
            raise
        except Exception as e:
            raise errors.Error('{}: {}'.format(self.resource, e))

        return results or []

    def describe_object_matches(self, object):
        '''
        Client side filtering of objects. Not all AWS API's support server side
        filtering, and those that do sometimes only have partial filtering. For
        those API's you must subclass and implement this hook - and return
        ``False`` for objects that should be ignored.

        :param: ``obj`` is a ``dict`` as returned by the ``describe_action`` API that
        represents a single AWS resource.
        '''
        return True

    def describe_object(self):
        '''
        Invokes the API specified as ``describe_action`` and do any filtering
        neccesary to return a single object that matches the locally defined
        resource (``self.resource``).
        '''
        objects = list(filter(self.describe_object_matches, self.get_possible_objects()))

        if len(objects) > 1:
            raise errors.Error('Expecting to find one {}, but found {}'.format(self.resource, len(objects)))

        if len(objects) == 1:
            logger.debug('Found object {}'.format(objects[0]))
            return self.annotate_object(objects[0])

        return {}

    def annotate_object(self, obj):
        '''
        Sometimes the API specified as ``describe_action`` does not return
        enough information on its own to be useful. Implement this hook in your
        subclass to collect more information about a resource.
        '''
        return obj

    def get_object_by_id(self, key):
        for obj in self.get_possible_objects():
            if obj.get(self.key, '') == key:
                return self.annotate_object(obj)
        return {}

    def generic_action(self, description, callable, serializer=None, **kwargs):
        ga = self.GenericAction(
            self,
            description,
            callable,
            serializer,
            **kwargs
        )
        return RetryAction(self, ga)

    def get_waiter(self, description, waiter, eventual_consistency_threshold=1):
        return Waiter(self, description, waiter, eventual_consistency_threshold)

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            raise errors.NotFound('Object "{}" could not be found, and is not scheduled to be created'.format(self.resource))

        return []

    @property
    def resource_id(self):
        if self.key and self.key in self.object:
            return self.object[self.key]
        return None


class SimpleApply(SimpleDescribe):

    name = 'apply'
    default = True

    waiter = None
    update_action = None
    create_serializer = None
    create_response = 'full-description'

    def get_create_serializer(self):
        return serializers.Resource()

    def get_create_name(self):
        return self.resource.name

    def get_update_serializer(self):
        return serializers.Resource(mode='update')

    def prepare_to_create(self):
        # This is a hook for changes you want to make *before* creating an object
        # For example, you want to delete old launch configurations before creating new ones
        return []

    def create_object(self):
        g = self.generic_action(
            'Creating {}'.format(self.resource),
            getattr(self.client, self.create_action),
            self.get_create_serializer(),
        )
        return CreateAction(self, g)

    def name_object(self):
        if 'name' not in self.resource.meta.fields:
            return
        name = self.get_create_name()
        argument = self.resource.meta.fields['name'].argument
        if getattr(argument, 'group', '') == 'tags':
            yield self.generic_action(
                ['Name newly created resource {} (via tags)'.format(name)],
                self.client.create_tags,
                Resources=serializers.ListOfOne(serializers.Identifier()),
                Tags=serializers.ListOfOne(serializers.Dict(
                    Key=argument.field,
                    Value=name,
                ))
            )

    def update_object(self):
        if self.update_action and self.object:
            logger.debug('Checking resource {} for changes'.format(self.resource))

            ds = serializers.Resource().diff(self.runner, self.resource, self.object)
            if not ds.matches():
                logger.debug('Resource has {} differences'.format(len(ds)))
                yield self.generic_action(
                    ['Updating {}'.format(self.resource)] + list(ds.lines()),
                    getattr(self.client, self.update_action),
                    self.get_update_serializer(),
                )

    def get_actions(self):
        self.object = self.describe_object()

        for change in self.prepare_to_create():
            yield change

        created = False

        if not self.object:
            logger.debug('Cannot find AWS object for resource {} - creating one'.format(self.resource))
            self.object = {}
            yield self.create_object()
            for action in self.name_object():
                yield action
            created = True

        if created:
            if self.waiter:
                waiter = self.get_waiter(
                    ['Waiting for resource to exist'],
                    self.waiter,
                    getattr(self, 'waiter_eventual_consistency_threshold', 1)
                )
                if created or not waiter.ready():
                    yield waiter
                    yield RefreshMetadata(self)
            elif self.create_response != 'full-description':
                yield RefreshMetadata(self)

            if self.create_response != 'full-description' and not self.waiter:
                yield PostCreation(self)

            yield PrintMetadata(self)

        logger.debug('Looking for changes to apply')
        for action in self.update_object():
            yield action


class TagsMixin(object):

    def update_tags(self):
        if getattr(self.resource, 'immutable_tags', False) and self.object:
            return

        if hasattr(self.resource, 'tags'):
            local_tags = dict(self.resource.tags)
            remote_tags = dict((v['Key'], v['Value']) for v in self.object.get('Tags', []))

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
        for action in super(TagsMixin, self).update_object():
            yield action
        for action in self.update_tags():
            yield action


class SimpleDestroy(SimpleDescribe):

    name = 'destroy'

    waiter = None

    def get_destroy_serializer(self):
        return serializers.Dict(**{self.key: self.resource_id})

    def destroy_object(self):
        yield self.generic_action(
            'Destroy {}'.format(self.resource),
            getattr(self.client, self.destroy_action),
            self.get_destroy_serializer(),
        )

        if self.waiter:
            yield self.get_waiter(
                ['Waiting for resource to go away'],
                self.waiter,
            )

    def can_delete(self):
        return True

    def get_actions(self):
        self.object = self.describe_object()

        if not self.object:
            logger.debug('Resource "{}" not found - assuming already destroyed'.format(self.resource))
            return

        if not self.can_delete():
            logger.debug('Resource "{}" cannot be deleted'.format(self.resource))
            return

        for action in self.destroy_object():
            yield action
