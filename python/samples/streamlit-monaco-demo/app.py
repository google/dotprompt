# Copyright 2026 Google LLC
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

import json

import streamlit as st
from dotprompt_grammar import LANGUAGE_ID, language_configuration, monarch_language
from streamlit_monaco import st_monaco

st.set_page_config(layout='wide')
st.title('Dotprompt Monaco Editor Demo')

st.markdown("""
This example demonstrates syntax highlighting for **Dotprompt** files using the Monaco Editor.
""")

# Sample Dotprompt content
DEFAULT_CONTENT = """---
model: gemini-2.5-flash
config:
  temperature: 0.7
  topP: 0.95
---

{{#role "system"}}
You are a helpful AI assistant specialized in coding tasks.
{{/role}}

{{#role "user"}}
Can you help me write a Python script to parse JSON?
{{/role}}

{{#role "model"}}
Certainly! Here is a simple example using the `json` module:

```python
import json

data = '{"name": "Alice", "age": 30}'
parsed = json.loads(data)
print(parsed["name"])
```
{{/role}}
"""

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader('Editor')
    # Note: Streamlit-Monaco may not strictly support custom language injection via Python arguments
    # out-of-the-box depending on the version.
    # If 'dotprompt' is not registered, Monaco falls back to plain text.
    # To get partial highlighting immediately, 'handlebars' can be used as a fallback.
    # However, for this demo, we attempt to use the 'dotprompt' ID assuming the environment
    # or component might support it or it's a placeholder for full integration.
    content = st_monaco(
        value=DEFAULT_CONTENT,
        height='600px',
        language=LANGUAGE_ID,  # defined in dotprompt_grammar.py
        theme='vs-dark',
        options={
            'minimap': {'enabled': False},
            'wordWrap': 'on',
        },
    )

with col2:
    st.subheader('Preview / Output')
    st.text_area('Raw Content', value=content, height=600, disabled=True)
