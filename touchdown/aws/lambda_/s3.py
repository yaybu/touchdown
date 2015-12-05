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

from touchdown.core.resource import Resource
from touchdown.core import argument

from touchdown.aws.s3 import NotificationConfiguration
from .function import Function


class S3LambdaNotification(Resource, NotificationConfiguration):

    function = argument.Resource(
        Function,
        field="LambdaFunctionArn",
    )

    def __init__(self, parent, **kwargs):
        super(S3LambdaNotification, self).__init__(parent, **kwargs)
        self.function.add_permission(
            name="s3-{}-lambda-{}".format(parent.name, self.function.name),
            action="lambda:Invoke",
            principal="s3.amazonaws.com",
            source_arn=parent.arn,
        )
