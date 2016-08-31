# Copyright 2015 Isotoma Limited
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

import unittest

import mock

from touchdown.core import errors, goals, workspace
from touchdown.core.map import SerialMap
from touchdown.frontends import ConsoleFrontend


class TestNewRelicNotifications(unittest.TestCase):

    def setUp(self):
        self.workspace = workspace.Workspace()

    def apply(self):
        self.apply_runner = goals.create(
            'apply',
            self.workspace,
            ConsoleFrontend(interactive=False),
            map=SerialMap
        )
        self.apply_runner.execute()

    def test_validation_apikey(self):
        self.workspace.add_newrelic_deployment_notification(
            name='foo',
            revision='foo',
        )
        with mock.patch('touchdown.notifications.newrelic.requests'):
            self.assertRaises(
                errors.Error,
                self.apply,
            )

    def test_validation_name(self):
        self.workspace.add_newrelic_deployment_notification(
            apikey='foo',
            revision='foo',
        )
        with mock.patch('touchdown.notifications.newrelic.requests'):
            self.assertRaises(
                errors.Error,
                self.apply,
            )

    def test_validation_revision(self):
        self.workspace.add_newrelic_deployment_notification(
            apikey='foo',
            name='foo',
        )
        with mock.patch('touchdown.notifications.newrelic.requests'):
            self.assertRaises(
                errors.Error,
                self.apply,
            )

    def test_apikey_and_name_and_revision(self):
        self.workspace.add_newrelic_deployment_notification(
            apikey='foo',
            name='myapp',
            revision='myrevision',
        )
        with mock.patch('touchdown.notifications.newrelic.requests') as r:
            r.post.return_value.status_code = 201
            self.apply()
            r.post.assert_called_with(
                'https://api.newrelic.com/deployments.xml',
                headers={'X-API-Key': 'foo'},
                data={
                    'deployment[app_name]': 'myapp',
                    'deployment[revision]': 'myrevision',
                }
            )

    def test_description(self):
        self.workspace.add_newrelic_deployment_notification(
            apikey='foo',
            name='myapp',
            revision='myrevision',
            description='A deployment'
        )
        with mock.patch('touchdown.notifications.newrelic.requests') as r:
            r.post.return_value.status_code = 201
            self.apply()
            r.post.assert_called_with(
                'https://api.newrelic.com/deployments.xml',
                headers={'X-API-Key': 'foo'},
                data={
                    'deployment[app_name]': 'myapp',
                    'deployment[description]': 'A deployment',
                    'deployment[revision]': 'myrevision',
                }
            )

    def test_changelog(self):
        self.workspace.add_newrelic_deployment_notification(
            apikey='foo',
            name='myapp',
            revision='myrevision',
            changelog='Something changed'
        )
        with mock.patch('touchdown.notifications.newrelic.requests') as r:
            r.post.return_value.status_code = 201
            self.apply()
            r.post.assert_called_with(
                'https://api.newrelic.com/deployments.xml',
                headers={'X-API-Key': 'foo'},
                data={
                    'deployment[app_name]': 'myapp',
                    'deployment[changelog]': 'Something changed',
                    'deployment[revision]': 'myrevision',
                }
            )

    def test_user(self):
        self.workspace.add_newrelic_deployment_notification(
            apikey='foo',
            name='myapp',
            revision='myrevision',
            user='duck',
        )
        with mock.patch('touchdown.notifications.newrelic.requests') as r:
            r.post.return_value.status_code = 201
            self.apply()
            r.post.assert_called_with(
                'https://api.newrelic.com/deployments.xml',
                headers={'X-API-Key': 'foo'},
                data={
                    'deployment[app_name]': 'myapp',
                    'deployment[user]': 'duck',
                    'deployment[revision]': 'myrevision',
                }
            )

    def test_application_id(self):
        self.workspace.add_newrelic_deployment_notification(
            apikey='foo',
            name='myapp',
            revision='myrevision',
            application_id=1,
        )
        with mock.patch('touchdown.notifications.newrelic.requests') as r:
            r.post.return_value.status_code = 201
            self.apply()
            r.post.assert_called_with(
                'https://api.newrelic.com/deployments.xml',
                headers={'X-API-Key': 'foo'},
                data={
                    'deployment[app_name]': 'myapp',
                    'deployment[revision]': 'myrevision',
                    'deployment[application_id]': '1',
                }
            )
