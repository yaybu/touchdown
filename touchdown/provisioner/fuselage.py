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

import six

from touchdown.core import argument, errors, resource, serializers
from . import provisioner

try:
    import fuselage
    from fuselage import argument as f_args, builder, bundle, resources
except ImportError:
    raise errors.Error("You need the fuselage package to use the fuselage_bundle resource")


def underscore(title):
    return re.sub(r'(?<=[a-z])(?=[A-Z])', u'_', title).lower()


class FuselageResource(resource.Resource):

    @classmethod
    def adapt(base_klass, resource_type):
        args = {
            "resource_name": underscore(resource_type.__resource_name__),
            "fuselage_class": resource_type,
            "root": argument.Resource(Bundle),
        }

        for arg, klass in resource_type.__args__.items():
            args[arg] = argument.String(field=arg)

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
        for resource in value:
            b.add(resource.fuselage_class(
                **serializers.Resource().render(runner, resource)
            ))
        return builder.build(b)


class Bundle(provisioner.Provisioner):

    resource_name = "fuselage_bundle"

    resources = argument.List(
        argument.Resource(FuselageResource),
        field='script',
        serializer=BundleSerializer(),
    )
    sudo = argument.Boolean(field='sudo', default=True)


class Apply(provisioner.Apply):

    resource = Bundle


for attr, value in vars(resources).items():
    if type(value) == fuselage.resource.ResourceType:
        locals()[attr] = FuselageResource.adapt(value)
