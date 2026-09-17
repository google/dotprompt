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

"""Tests for model name selection and normalization."""

from typing import Any

from dotpromptz.dotprompt import _drop_blank_model, _pick_model


def test_pick_model_returns_the_first_named_layer() -> None:
    """A later layer's name wins over the file and the instance default."""
    assert _pick_model('gemini-call', 'gemini-file', 'gemini-default') == 'gemini-call'


def test_pick_model_skips_blank_and_none() -> None:
    """None and '' are the same skip, so the next named layer is used."""
    assert _pick_model('', 'gemini-file') == 'gemini-file'
    assert _pick_model(None, 'gemini-file') == 'gemini-file'
    assert _pick_model(None, '', 'gemini-default') == 'gemini-default'


def test_pick_model_none_when_nothing_named() -> None:
    """No layer named a model, so there is nothing to carry forward."""
    assert _pick_model() is None
    assert _pick_model(None, '') is None


def test_pick_model_keeps_names_that_only_look_empty() -> None:
    """Only '' is blank; whitespace and '0' are names a registry could hold."""
    assert _pick_model('   ') == '   '
    assert _pick_model('0') == '0'


def test_drop_blank_model_removes_the_key() -> None:
    """A blank model must not reach the overlay, where it would win the key."""
    assert _drop_blank_model({'model': ''}) == {}
    assert _drop_blank_model({'model': None}) == {}


def test_drop_blank_model_keeps_a_real_name() -> None:
    """A named model stays put so the overlay can hand it to the next layer."""
    assert _drop_blank_model({'model': 'gemini-file'}) == {'model': 'gemini-file'}


def test_drop_blank_model_leaves_other_keys_alone() -> None:
    """Normalizing the model must not disturb the rest of the dump."""
    dumped: dict[str, Any] = {'model': '', 'config': {'topK': 40}, 'description': 'hi'}
    assert _drop_blank_model(dumped) == {'config': {'topK': 40}, 'description': 'hi'}


def test_drop_blank_model_tolerates_a_missing_key() -> None:
    """Most layers never mention a model at all."""
    assert _drop_blank_model({}) == {}
