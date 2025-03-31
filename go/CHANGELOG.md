# Changelog

## [0.1.1](https://github.com/google/dotprompt/compare/dotprompt-go-v0.1.0...dotprompt-go-v0.1.1) (2025-03-31)


### Features

* go: Fix pico schema parser issues ([#96](https://github.com/google/dotprompt/issues/96)) ([d938205](https://github.com/google/dotprompt/commit/d938205f28c96cd42a399797c121961d1d146344))
* **go/dotprompt:** Add comments for functions ([#99](https://github.com/google/dotprompt/issues/99)) ([e44ce35](https://github.com/google/dotprompt/commit/e44ce350803f67b39e006106656423e21ed2d850))
* **go/dotprompt:** Add template as a parameter for dotprompt type ([#136](https://github.com/google/dotprompt/issues/136)) ([bf5d6a3](https://github.com/google/dotprompt/commit/bf5d6a36d5999493e090be848014bf3f5a7ca54e))
* **go/dotprompt:** add types.go implementation ([#82](https://github.com/google/dotprompt/issues/82)) ([6514fbf](https://github.com/google/dotprompt/commit/6514fbf27c35ab60dea6968f167b103236da7a77))
* **go/dotprompt:** Export define helper and partial functions ([#119](https://github.com/google/dotprompt/issues/119)) ([481ed50](https://github.com/google/dotprompt/commit/481ed5034233f9158407a38a348c7b0a8cd88ff6))
* **go/dotprompt:** Metadata and Partials specs test implementation  ([#89](https://github.com/google/dotprompt/issues/89)) ([2e5edba](https://github.com/google/dotprompt/commit/2e5edbaec59923e2136472302ae5bc5c29d31957))
* **go/dotprompt:** Modify the dotprompt files to pass the spec tests similar to js ([#98](https://github.com/google/dotprompt/issues/98)) ([d9f9f65](https://github.com/google/dotprompt/commit/d9f9f6510b4612049c2a004dd530cae60ebd0398))
* **go/dotprompt:** Modify the JSONSchema to jsonschema.Schema type ([#111](https://github.com/google/dotprompt/issues/111)) ([340ec1b](https://github.com/google/dotprompt/commit/340ec1b1c36554043cf9ac0ad7c423161971f202))
* **go/parse:** parse.go implementation [#62](https://github.com/google/dotprompt/issues/62) ([#87](https://github.com/google/dotprompt/issues/87)) ([d5dc13c](https://github.com/google/dotprompt/commit/d5dc13c0bf0437875a3b133511ffed474a8b3bf9))
* **go:** initialize go module ([#59](https://github.com/google/dotprompt/issues/59)) ([5aea7d5](https://github.com/google/dotprompt/commit/5aea7d5bb8ffe030b9dc267156886b1c946f693d))
* **py/dotpromptz:** implement helpers in terms of the rust implementation of handlebars-rust and fix go flakiness ([#115](https://github.com/google/dotprompt/issues/115)) ([314c0b5](https://github.com/google/dotprompt/commit/314c0b5182aaad25bf4cfccb8207faa60f63256f))
* **python:** add OpenAI adapter implementation for dotprompt [#38](https://github.com/google/dotprompt/issues/38) ([#97](https://github.com/google/dotprompt/issues/97)) ([d171f87](https://github.com/google/dotprompt/commit/d171f8792ecf08f446e18ea3bbd5309cafa1d8a3))
* **py:** utility to remove undefined fields from dicts/lists recursively ([#105](https://github.com/google/dotprompt/issues/105)) ([d25c911](https://github.com/google/dotprompt/commit/d25c911bc1e84e5691b961a4c38a8bcd73c80aa0))
* script to update all deps in one go and update deps ([#130](https://github.com/google/dotprompt/issues/130)) ([09ac58e](https://github.com/google/dotprompt/commit/09ac58e4512fae817a63f731ac0db80967842436))
* use the more maintained YAML parsing lib at https://github.com/goccy/go-yaml ([#151](https://github.com/google/dotprompt/issues/151)) ([910b3a7](https://github.com/google/dotprompt/commit/910b3a72f3756296c3b01b96936a5bc4c9fa88ef))


### Bug Fixes

* **deps:** switch to version 1.23 of go; update pnpm deps ([#153](https://github.com/google/dotprompt/issues/153)) ([672b8da](https://github.com/google/dotprompt/commit/672b8da68e784abd17a14f9f1f292d9b65b88a80))
* **go,py:** type fixes and ensure we build/lint the go code in hooks and ci ([#83](https://github.com/google/dotprompt/issues/83)) ([19a8257](https://github.com/google/dotprompt/commit/19a8257f4f73b776229d5324a0366fd9a79c20aa))
* **go/dotprompt:** Add partials and helpers parameters ([#166](https://github.com/google/dotprompt/issues/166)) ([e5e8fba](https://github.com/google/dotprompt/commit/e5e8fba19c9a2d5f2b9b73c758f759883baf79e4))
* **license:** use the full license header in source code ([#142](https://github.com/google/dotprompt/issues/142)) ([64894ef](https://github.com/google/dotprompt/commit/64894ef898876b861c6c244d522f634cd8fcc842))
* remove spurious role type `assistant` ([#169](https://github.com/google/dotprompt/issues/169)) ([1b5142c](https://github.com/google/dotprompt/commit/1b5142c4a7ad20ef722d438cefa0b93a82d7adbb))
