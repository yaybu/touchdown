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

from touchdown.core import (
    action,
    argument,
    errors,
    plan,
    resource,
    serializers,
    workspace,
)

try:
    import jinja2
except ImportError:
    jinja2 = None


class JinjaTemplate(resource.Resource):

    resource_name = 'jinja2_template'

    name = argument.String()
    source = argument.String(field='source')
    context = argument.Dict(field='context')
    root = argument.Resource(workspace.Workspace)


class JinjaRenderAction(action.Action):

    @property
    def description(self):
        yield 'Render Jinja2 template "{}"'.format(self.resource.name)

    def run(self):
        output = serializers.Resource().render(self.runner, self.resource)
        env = jinja2.Environment()
        template = env.from_string(output['source'])
        self.plan.object = {
            'Rendered': template.render(**output['context']),
        }


class Apply(plan.Plan):

    name = 'apply'
    resource = JinjaTemplate

    def get_actions(self):
        if not jinja2:
            raise errors.Error('Jinja2 templates are not available. Please install \'jinja2\'.')
        yield JinjaRenderAction(self)


class TemplateAsString(serializers.Serializer):

    def __init__(self, resource):
        self.resource = resource

    def render(self, runner, object):
        return runner.get_service(self.resource, 'apply').object['Rendered']

    def dependencies(self, object):
        return frozenset((self.resource, ))


argument.String.register_adapter(JinjaTemplate, lambda r: TemplateAsString(r))
