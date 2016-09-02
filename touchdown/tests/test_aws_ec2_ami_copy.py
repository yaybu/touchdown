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

from touchdown.tests.aws import StubberTestCase
from touchdown.tests.stubs.aws import ImageCopyStubber


class TestCreateImageCopy(StubberTestCase):

    def test_create_image_copy(self):
        goal = self.create_goal('apply')

        image = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.get_image(
                    name='test-image',
                ),
                'describe',
            )
        ))
        image.add_describe_images_one_response()

        image_copy = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.add_image_copy(
                    name='test-image_copy',
                    source=image.resource,
                ),
                'apply',
            )
        ))
        image_copy.add_describe_images_empty_response()
        image_copy.add_copy_image()
        image_copy.add_describe_images_one_response()
        image_copy.add_describe_images_one_response()

        goal.execute()

    def test_create_image_copy_idempotent(self):
        goal = self.create_goal('apply')

        image = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.get_image(
                    name='test-image',
                ),
                'describe',
            )
        ))
        image.add_describe_images_one_response()

        image_copy = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.add_image_copy(
                    name='test-image_copy',
                    source=image.resource,
                ),
                'apply',
            )
        ))
        image_copy.add_describe_images_one_response()
        image_copy.add_describe_image_attribute()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(image_copy.resource)), 0)


class TestDestroyImageCopy(StubberTestCase):

    def test_destroy_image_copy(self):
        goal = self.create_goal('destroy')

        image = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.get_image(
                    name='test-image',
                ),
                'describe',
            )
        ))
        image.add_describe_images_one_response()

        image_copy = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.add_image_copy(
                    name='test-image_copy',
                    source=image.resource,
                ),
                'destroy',
            )
        ))
        image_copy.add_describe_images_one_response()
        image_copy.add_deregister_image()

        goal.execute()

    def test_destroy_image_copy_idempotent(self):
        goal = self.create_goal('destroy')

        image = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.get_image(
                    name='test-image',
                ),
                'describe',
            )
        ))
        image.add_describe_images_one_response()

        image_copy = self.fixtures.enter_context(ImageCopyStubber(
            goal.get_service(
                self.aws.add_image_copy(
                    name='test-image_copy',
                    source=image.resource,
                ),
                'destroy',
            )
        ))
        image_copy.add_describe_images_empty_response()

        self.assertEqual(len(list(goal.plan())), 0)
        self.assertEqual(len(goal.get_changes(image_copy.resource)), 0)
