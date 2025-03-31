# Changelog

## [0.1.1](https://github.com/google/dotprompt/compare/dotpromptz-v0.1.0...dotpromptz-v0.1.1) (2025-03-31)


### Features

* add implementation of helpers and util modules; move interfaces into dotpromptz project ([#73](https://github.com/google/dotprompt/issues/73)) ([8c7aea1](https://github.com/google/dotprompt/commit/8c7aea1faffaf823d01b132e55cb175a4fca5ccb))
* add stub spec_test.py and script to monitor tests. ([#138](https://github.com/google/dotprompt/issues/138)) ([65966e9](https://github.com/google/dotprompt/commit/65966e9bfc077e85d0b83d04d0384150470dbfd3))
* **go/parse:** parse.go implementation [#62](https://github.com/google/dotprompt/issues/62) ([#87](https://github.com/google/dotprompt/issues/87)) ([d5dc13c](https://github.com/google/dotprompt/commit/d5dc13c0bf0437875a3b133511ffed474a8b3bf9))
* parseDocument python ([#80](https://github.com/google/dotprompt/issues/80)) ([82ebc36](https://github.com/google/dotprompt/commit/82ebc3672e8de051dfbdd92968ed3f84c79a247f))
* partial test runner implementation now loads tests ([#139](https://github.com/google/dotprompt/issues/139)) ([b09dd2f](https://github.com/google/dotprompt/commit/b09dd2f9b8029317ce484d6f32d5a3fb89f5f7e1))
* Port JS types to Python  ([#65](https://github.com/google/dotprompt/issues/65)) ([edcb037](https://github.com/google/dotprompt/commit/edcb03765f3cb6e5743d107a35cf255a60ab0369))
* **py/dotpromptz:** configure handlebars to not escape by default ([#163](https://github.com/google/dotprompt/issues/163)) ([f7c33e1](https://github.com/google/dotprompt/commit/f7c33e1303476fd473e803f930ac1e1f9e1d87c9))
* **py/dotpromptz:** directory-based async and sync implementations of PromptStore and PromptStoreWritable ([#164](https://github.com/google/dotprompt/issues/164)) ([ac92fbf](https://github.com/google/dotprompt/commit/ac92fbf3af7ac3207102c94c20d294d8c54b9dd4))
* **py/dotpromptz:** implement helpers in terms of the rust implementation of handlebars-rust and fix go flakiness ([#115](https://github.com/google/dotprompt/issues/115)) ([314c0b5](https://github.com/google/dotprompt/commit/314c0b5182aaad25bf4cfccb8207faa60f63256f))
* **py/dotpromptz:** initial bits of Dotprompt class ([#148](https://github.com/google/dotprompt/issues/148)) ([90f7838](https://github.com/google/dotprompt/commit/90f78384a958d41d78dee48497a78dfde11f4476))
* **py:** add SafeString implementation that works with js2py ([#104](https://github.com/google/dotprompt/issues/104)) ([1ebeca3](https://github.com/google/dotprompt/commit/1ebeca3976faf2dc91d8d7f4a74c218824aac353))
* **py:** implement identify_partials in terms of regexps since we do not have an AST to walk [#90](https://github.com/google/dotprompt/issues/90) ([#150](https://github.com/google/dotprompt/issues/150)) ([f802275](https://github.com/google/dotprompt/commit/f8022755d7eef716bbb54dd08a2c3a061250d393))
* **py:** implementation of parse.py; refactor parse.ts and update tests. ([#79](https://github.com/google/dotprompt/issues/79)) ([47e7245](https://github.com/google/dotprompt/commit/47e7245c0aae710b102178019d1f3449c2f1af66))
* python implementations of helpers ([#129](https://github.com/google/dotprompt/issues/129)) ([79c6ef3](https://github.com/google/dotprompt/commit/79c6ef3e9cc472fed3a832c00a1515ceef0981da))
* python: picoschema support  ISSUE: [#36](https://github.com/google/dotprompt/issues/36)  CHANGELOG: - [x] Port relevant functionality - [x] Add tests ([#95](https://github.com/google/dotprompt/issues/95)) ([0da188c](https://github.com/google/dotprompt/commit/0da188c52540f041309e39fa6bc798eaf7fd7a81))
* **python:** add OpenAI adapter implementation for dotprompt [#38](https://github.com/google/dotprompt/issues/38) ([#97](https://github.com/google/dotprompt/issues/97)) ([d171f87](https://github.com/google/dotprompt/commit/d171f8792ecf08f446e18ea3bbd5309cafa1d8a3))
* **py:** utility function to unquote a string literal coming from js2py handlebars helpers ([#107](https://github.com/google/dotprompt/issues/107)) ([b3672ca](https://github.com/google/dotprompt/commit/b3672ca6192de4895585b28b8bbd301f8294090f))
* **py:** utility to remove undefined fields from dicts/lists recursively ([#105](https://github.com/google/dotprompt/issues/105)) ([d25c911](https://github.com/google/dotprompt/commit/d25c911bc1e84e5691b961a4c38a8bcd73c80aa0))


### Bug Fixes

* **docs:** update docs for helpers.py functions ([#118](https://github.com/google/dotprompt/issues/118)) ([40f74d4](https://github.com/google/dotprompt/commit/40f74d4cf75a47d8b7f9f85801a1bb5969bae082))
* **docs:** update helper docs ([#132](https://github.com/google/dotprompt/issues/132)) ([9b84245](https://github.com/google/dotprompt/commit/9b842459e8faa5f4afe7d389deb6c351ab1271be))
* **go,py:** type fixes and ensure we build/lint the go code in hooks and ci ([#83](https://github.com/google/dotprompt/issues/83)) ([19a8257](https://github.com/google/dotprompt/commit/19a8257f4f73b776229d5324a0366fd9a79c20aa))
* **helpers:** use ctx instead of hash to get the fn and inverse ([#131](https://github.com/google/dotprompt/issues/131)) ([8749d1f](https://github.com/google/dotprompt/commit/8749d1f78ee754742ae7fcc9247854021178bdbc))
* **license:** use the full license header in source code ([#142](https://github.com/google/dotprompt/issues/142)) ([64894ef](https://github.com/google/dotprompt/commit/64894ef898876b861c6c244d522f634cd8fcc842))
* **py/spec_test:** hex-encoded SHA-256 digest rather than base64-encoded SHA-256 digest for module IDs ([#140](https://github.com/google/dotprompt/issues/140)) ([796c644](https://github.com/google/dotprompt/commit/796c6442a3c1836de2170c466966382a0577a940))
* remove spurious role type `assistant` ([#169](https://github.com/google/dotprompt/issues/169)) ([1b5142c](https://github.com/google/dotprompt/commit/1b5142c4a7ad20ef722d438cefa0b93a82d7adbb))


### Documentation

* add initial mkdocs documentation for eng [#43](https://github.com/google/dotprompt/issues/43) ([#44](https://github.com/google/dotprompt/issues/44)) ([31be336](https://github.com/google/dotprompt/commit/31be336d14899acf7ea1cefb4b782f5b2d1c31d1))
