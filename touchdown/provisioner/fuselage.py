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

from __future__ import absolute_import

import re

from touchdown.core import argument, errors, resource, serializers

from . import provisioner

try:
    import fuselage
    from fuselage import argument as f_args, builder, bundle, resources
except ImportError:
    raise errors.Error('You need the fuselage package to use the fuselage_bundle resource')


def underscore(title):
    return re.sub(r'(?<=[a-z])(?=[A-Z])', u'_', title).lower()


arguments = {
    f_args.Boolean: lambda resource_type, klass, arg: argument.Boolean(field=arg),
    f_args.String: lambda resource_type, klass, arg: argument.String(field=arg),
    f_args.FullPath: lambda resource_type, klass, arg: argument.String(field=arg),
    f_args.File: lambda resource_type, klass, arg: argument.String(field=arg),
    f_args.Integer: lambda resource_type, klass, arg: argument.Integer(field=arg),
    f_args.Octal: lambda resource_type, klass, arg: argument.Integer(field=arg),
    f_args.Dict: lambda resource_type, klass, arg: argument.Dict(field=arg),
    f_args.List: lambda resource_type, klass, arg: argument.List(field=arg),
    f_args.SubscriptionArgument: lambda resource_type, klass, arg: argument.List(field=arg),
    f_args.PolicyArgument: lambda resource_type, klass, arg: argument.String(field=arg, choices=resource_type.policies.keys()),
}


class FuselageResource(resource.Resource):

    @classmethod
    def adapt(base_klass, resource_type):
        args = {
            'resource_name': underscore(resource_type.__resource_name__),
            'fuselage_class': resource_type,
            'root': argument.Resource(Bundle),
        }

        for arg, klass in resource_type.__args__.items():
            args[arg] = arguments[klass.__class__](resource_type, klass, arg)

        cls = type(
            resource_type.__resource_name__,
            (base_klass, ),
            args
        )

        def _(self, **kwargs):
            arguments = {'parent': self}
            arguments.update(kwargs)
            resource = cls(**arguments)
            if not self.resources:
                self.resources = []
            self.resources.append(resource)
            self.add_dependency(resource)
            return resource
        setattr(Bundle, 'add_%s' % cls.resource_name, _)

        return cls


class BundleSerializer(serializers.Serializer):

    def render(self, runner, value):
        b = bundle.ResourceBundle()
        for res in value:
            b.add(res.fuselage_class(
                **serializers.Resource().render(runner, res)
            ))
        return builder.build(b)

    def pending(self, runner, value):
        for res in value:
            if serializers.Resource().pending(runner, res):
                return True
        return False


class Bundle(provisioner.Provisioner):

    resource_name = 'fuselage_bundle'

    always_apply = argument.Boolean()
    resources = argument.List(
        argument.Resource(FuselageResource),
        field='script',
        serializer=BundleSerializer(),
    )
    sudo = argument.Boolean(field='sudo', default=True)


class Describe(provisioner.Describe):

    name = 'describe'
    resource = Bundle

    def describe_object(self):
        if self.resource.always_apply:
            return {'Results': 'Pending'}

        if not self.resource.target:
            # If target is not set we are probably dealing with an AMI... YUCK
            # Bail out
            return {'Result': 'Pending'}

        serializer = serializers.Resource()
        if serializer.pending(self.runner, self.resource):
            return {'Result': 'Pending'}

        kwargs = serializer.render(self.runner, self.resource)

        try:
            client = self.runner.get_plan(self.resource.target).get_client()
        except errors.ServiceNotReady:
            return {'Result': 'Pending'}

        try:
            client.run_script(kwargs['script'], ['-s'])
        except errors.CommandFailed as e:
            if e.exit_code == 254:
                return {'Result': 'Success'}

        return {'Result': 'Pending'}


class Apply(provisioner.Apply):

    resource = Bundle


for attr, value in vars(resources).items():
    if type(value) == fuselage.resource.ResourceType:
        locals()[attr] = FuselageResource.adapt(value)
