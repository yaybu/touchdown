# Copyright 2014-2015 Isotoma Limited
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

import hashlib
import mimetypes
import os

from touchdown.core import argument
from touchdown.core.plan import Plan
from touchdown.core.resource import Resource

from ..common import SimpleApply, SimpleDescribe
from .bucket import Bucket


class Folder(Resource):

    resource_name = 'folder'

    name = argument.String()
    source = argument.String()

    acl = argument.String(
        default='private',
        choices=['private', 'public-read', 'public-read-write', 'authenticated-read', 'bucket-owner-read', 'bucket-owner-full-control'],
        field='ACL',
    )

    bucket = argument.Resource(Bucket, field='Bucket')


class Describe(SimpleDescribe, Plan):

    resource = Folder
    service_name = 's3'
    api_version = '2006-03-01'
    key = 'Name'
    describe_action = None

    def get_folder_contents(self):
        paginator = self.client.get_paginator('list_objects')
        pages = paginator.paginate(
            Bucket=self.resource.bucket.name,
            Prefix=self.resource.name
        )

        for page in pages:
            for key in page.get('Contents', []):
                if key['Key'].startswith(self.resource.name):
                    yield key['Key'][len(self.resource.name):].lstrip('/'), {
                        'LastModified': key['LastModified'],
                        'ETag': key['ETag'],
                        'Md5': key['ETag'].strip('"'),
                        'Size': key['Size'],
                    }

    def describe_object(self):
        return {
            'Name': self.resource.name,
            'Arn': 's3:aws:s3:::{}{}'.format(
                self.resource.bucket.name,
                self.resource.source,
            ),
        }


class Apply(SimpleApply, Describe):

    create_action = 'put_object'
    create_response = 'not-that-useful'

    default_content_type = 'application/octet-stream'

    def update_object(self):
        remote = {}
        local = {}

        base = self.resource.source
        for root, dirs, files in os.walk(base):
            for f in files:
                path = os.path.join(root, f)
                with open(path) as fp:
                    h = hashlib.md5(fp.read())
                local[os.path.relpath(path, base)] = {
                    'Md5': h.hexdigest(),
                }

        if self.runner.get_plan(self.resource.bucket).resource_id:
            remote = {k: v for k, v in self.get_folder_contents()}

        for path in local:
            contenttype = mimetypes.guess_type(path)[0] or self.default_content_type

            if path not in remote:
                yield self.generic_action(
                    'Add {} ({})'.format(path, contenttype),
                    self.client.put_object,
                    Key=os.path.join(self.resource.name, path),
                    Body=open(os.path.join(base, path)).read(),
                    ACL=self.resource.acl,
                    Bucket=self.resource.bucket.name,
                    CacheControl='max-age=0',
                    ContentType=contenttype,
                )
            elif local[path]['Md5'] != remote[path]['Md5']:
                yield self.generic_action(
                    'Update {} ({})'.format(path, contenttype),
                    self.client.put_object,
                    Key=os.path.join(self.resource.name, path),
                    Body=open(os.path.join(base, path)).read(),
                    ACL=self.resource.acl,
                    Bucket=self.resource.bucket.name,
                    CacheControl='max-age=0',
                    ContentType=contenttype,
                )

        for path in remote:
            if path not in local:
                yield self.generic_action(
                    'Remove {}'.format(path),
                    self.client.delete_object,
                    Bucket=self.resource.bucket.name,
                    Key=os.path.join(self.resource.name, path),
                )
