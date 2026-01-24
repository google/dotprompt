" Copyright 2026 Google LLC
"
" Licensed under the Apache License, Version 2.0 (the "License");
" you may not use this file except in compliance with the License.
" You may obtain a copy of the License at
"
"     http://www.apache.org/licenses/LICENSE-2.0
"
" Unless required by applicable law or agreed to in writing, software
" distributed under the License is distributed on an "AS IS" BASIS,
" WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
" See the License for the specific language governing permissions and
" limitations under the License.
"
" SPDX-License-Identifier: Apache-2.0

" Vim syntax file
" Language: Dotprompt
" Maintainer: Google
" License: Apache 2.0

if exists("b:current_syntax")
  finish
endif

" Define Dotprompt specifics
syntax match dotpromptMarker "<<<dotprompt:[^>]\+>>>"
syntax match dotpromptPartial "{{>.\\+}}"

" License header comments (lines starting with #)
syntax match dotpromptHeaderComment "^#.*$"
highlight default link dotpromptHeaderComment Comment

" Handlebars/Dotprompt tags
syntax region dotpromptTag start="{{" end="}}" contains=dotpromptKeyword,dotpromptString,dotpromptNumber,dotpromptBoolean

" Keywords inside tags
syntax keyword dotpromptKeyword contained if unless each with log lookup else
syntax keyword dotpromptKeyword contained json role history section media ifEquals unlessEquals

" Data types inside tags
syntax region dotpromptString start=/"/ skip=/\\"/ end=/"/ contained
syntax region dotpromptString start=/'/ skip=/\\'/ end=/'/ contained
syntax match dotpromptNumber "\d\+" contained
syntax keyword dotpromptBoolean contained true false null undefined

" Highlight links
highlight default link dotpromptMarker PreProc
highlight default link dotpromptPartial Structure
highlight default link dotpromptTag Delimiter
highlight default link dotpromptKeyword Keyword
highlight default link dotpromptString String
highlight default link dotpromptNumber Number
highlight default link dotpromptBoolean Boolean

" Handle Frontmatter (YAML) - include standard YAML syntax
" Match --- anywhere (not just at file start) to support license headers
let s:current_syntax = b:current_syntax
unlet b:current_syntax
syntax include @Yaml syntax/yaml.vim
syntax region dotpromptFrontmatter start="^---$" end="^---$" contains=@Yaml keepend
let b:current_syntax = s:current_syntax

let b:current_syntax = "dotprompt"

