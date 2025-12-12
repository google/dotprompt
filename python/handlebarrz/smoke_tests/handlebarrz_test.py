# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Test code for smoke tests."""

from handlebarrz import HelperOptions, Template


def loud_helper(params: list[str], options: HelperOptions) -> str:
    """Test helper."""
    # Get the first parameter or use an empty string
    text = params[0] if params else ''
    return text.upper()


template = Template()
template.register_helper('loud', loud_helper)
template_string = '{{loud name}}'
template.register_template('test', template_string)
print(template.render('test', {'name': 'world'}))
