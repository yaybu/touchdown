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
from touchdown.core.plan import Plan
from touchdown.core import argument

from ..account import Account
from ..common import SimpleDescribe, SimpleApply

from .database import Database


class PointInTimeRestore(Resource):

    resource_name = "point_in_time_restore"

    name = argument.String(field="SourceDBInstanceIdentifier")
    from_database = argument.Resource(Database, field="TargetDBInstanceIdentifier")
    restore_time = argument.String(field="RestoreTime")

    account = argument.Resource(Account)


class Describe(SimpleDescribe, Plan):

    resource = PointInTimeRestore
    service_name = 'rds'
    describe_action = "describe_db_instances"
    describe_notfound_exception = "DBInstanceNotFound"
    describe_envelope = "DBInstances"
    key = 'DBInstanceIdentifier'


class Apply(SimpleApply, Describe):

    create_action = "restore_db_instance_to_point_in_time"
    waiter = "db_instance_available"
