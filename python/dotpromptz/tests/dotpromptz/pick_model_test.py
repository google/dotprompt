# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

from dotpromptz.dotprompt import _pick_model


def test_pick_model_returns_the_first_real_name() -> None:
    """A later layer's name wins over the file and the instance default."""
    assert _pick_model('gemini-call', 'gemini-file', 'gemini-default') == 'gemini-call'


def test_pick_model_skips_blank_and_none() -> None:
    """None and '' are the same skip, so the next named layer is used."""
    assert _pick_model('', 'gemini-file') == 'gemini-file'
    assert _pick_model(None, 'gemini-file') == 'gemini-file'
    assert _pick_model(None, '', 'gemini-default') == 'gemini-default'


def test_pick_model_empty_when_nothing_named() -> None:
    """No layer named a model: the leftover is ''."""
    assert _pick_model() == ''
    assert _pick_model(None, '') == ''
