# Changelog

## [0.1.7](https://github.com/google/dotprompt/compare/dotpromptz-handlebars-0.1.6...dotpromptz-handlebars-0.1.7) (2026-01-30)


### Bug Fixes

* **ci:** auto-update lockfiles and label release PRs ([#483](https://github.com/google/dotprompt/issues/483)) ([3ae17e4](https://github.com/google/dotprompt/commit/3ae17e44b9acbd4efe5aab53b30a5c81694cbe4e))

## [0.1.6](https://github.com/google/dotprompt/compare/dotpromptz-handlebars-0.1.5...dotpromptz-handlebars-0.1.6) (2026-01-30)


### Bug Fixes

* **handlebarrz:** add toggleable platform flags and Unicode tests ([#481](https://github.com/google/dotprompt/issues/481)) ([7130b4c](https://github.com/google/dotprompt/commit/7130b4ce172bf70513d55417f6bcc309511d83f0))

## [0.1.5](https://github.com/google/dotprompt/compare/dotpromptz-handlebars-0.1.4...dotpromptz-handlebars-0.1.5) (2026-01-30)


### Bug Fixes

* **ci:** add RUSTUP_MAX_RETRIES and use native ARM64 runners ([#479](https://github.com/google/dotprompt/issues/479)) ([aefd33a](https://github.com/google/dotprompt/commit/aefd33a7a595ae4fc31a7f1b1f28692d7addc046))

## [0.1.4](https://github.com/google/dotprompt/compare/dotpromptz-handlebars-0.1.3...dotpromptz-handlebars-0.1.4) (2026-01-30)


### Features

* **dotpromptz-handlebars:** add package_name function for smoke testing ([#457](https://github.com/google/dotprompt/issues/457)) ([681cc52](https://github.com/google/dotprompt/commit/681cc527dfd2d534ba5e0b6b2d73c52ead267b59))
* **py:** add bazel build/test support and automate requirements ([#399](https://github.com/google/dotprompt/issues/399)) ([efd7fe0](https://github.com/google/dotprompt/commit/efd7fe0592e2491c34e8fd399e756de375c802eb))
* **py:** switch to using ty for type checking ([#376](https://github.com/google/dotprompt/issues/376)) ([7f1c026](https://github.com/google/dotprompt/commit/7f1c0268e5de5a2d6d887ac590d110dea7d3ed07))


### Bug Fixes

* **dotpromptz-handlebars:** version mismatch in handlebarrz ([#428](https://github.com/google/dotprompt/issues/428)) ([1cf8e01](https://github.com/google/dotprompt/commit/1cf8e019a1c4b94254c5819ceb312df2b8c1e889))
* **handlebarrz:** correct register_helper type stub signature ([#434](https://github.com/google/dotprompt/issues/434)) ([7bc7e2a](https://github.com/google/dotprompt/commit/7bc7e2a72f792940481fdf180961c7508b3ae389))
* update package name references to dotpromptz-handlebars ([#403](https://github.com/google/dotprompt/issues/403)) ([8bbd99d](https://github.com/google/dotprompt/commit/8bbd99debe511a5b7327d80aeb40b6a854d57630)), closes [#344](https://github.com/google/dotprompt/issues/344)

## [0.1.3](https://github.com/google/dotprompt/compare/handlebarrz-0.1.2...handlebarrz-0.1.3) (2025-12-12)


### Features

* **py:** add support for python 3.14 ([#365](https://github.com/google/dotprompt/issues/365)) ([53db722](https://github.com/google/dotprompt/commit/53db722352d360c9097028d63eb1b7e9576d3d24))


### Bug Fixes

* **py/handlebarrz:** remove redundant lock file ([#360](https://github.com/google/dotprompt/issues/360)) ([db5416a](https://github.com/google/dotprompt/commit/db5416a4f7ce508a3d684b7c56ea8a50f46ee65d))

## [0.1.2](https://github.com/google/dotprompt/compare/handlebarrz-0.1.1...handlebarrz-0.1.2) (2025-11-13)


### Features

* cargo workspace configuration and bazel build files for hermetic environment ([#257](https://github.com/google/dotprompt/issues/257)) ([aef822e](https://github.com/google/dotprompt/commit/aef822ed484d256ba95a3544e132a9b33e0dc02d))
* **handlebarrz:** CI to publish rust python package ([#152](https://github.com/google/dotprompt/issues/152)) ([20765d8](https://github.com/google/dotprompt/commit/20765d83c50537cf935fe461a24f5c86d970d787))
* **handlebarrz:** native ifEquals, unlessEquals, and json helpers ([#121](https://github.com/google/dotprompt/issues/121)) ([e3619e9](https://github.com/google/dotprompt/commit/e3619e906cd0b69d854ca50d798e36cf44c130bd))
* partial test runner implementation now loads tests ([#139](https://github.com/google/dotprompt/issues/139)) ([b09dd2f](https://github.com/google/dotprompt/commit/b09dd2f9b8029317ce484d6f32d5a3fb89f5f7e1))
* **py/dotprompt:** render and compile implementations ([#263](https://github.com/google/dotprompt/issues/263)) ([961d0db](https://github.com/google/dotprompt/commit/961d0dbbd9c2ce522252bc3d92f6dde4b7fe9cc1))
* **py/dotpromptz:** add initial Dotprompt._resolve_partials implementation ([#215](https://github.com/google/dotprompt/issues/215)) ([03a161c](https://github.com/google/dotprompt/commit/03a161c3440a680bc0df472f35efa155fe0d5151))
* **py/dotpromptz:** configure handlebars to not escape by default ([#163](https://github.com/google/dotprompt/issues/163)) ([f7c33e1](https://github.com/google/dotprompt/commit/f7c33e1303476fd473e803f930ac1e1f9e1d87c9))
* **py/dotpromptz:** construct test-specific dotprompt instance with partials and partial resolver set up ([#275](https://github.com/google/dotprompt/issues/275)) ([0af9a64](https://github.com/google/dotprompt/commit/0af9a64acf50278bdffda337e19c66fbb97e43a3))
* **py/dotpromptz:** implement helpers in terms of the rust implementation of handlebars-rust and fix go flakiness ([#115](https://github.com/google/dotprompt/issues/115)) ([314c0b5](https://github.com/google/dotprompt/commit/314c0b5182aaad25bf4cfccb8207faa60f63256f))
* **py/dotpromptz:** initial bits of Dotprompt class ([#148](https://github.com/google/dotprompt/issues/148)) ([90f7838](https://github.com/google/dotprompt/commit/90f78384a958d41d78dee48497a78dfde11f4476))
* **py/handlebarrz:** add a Template.compile method to the Python wrapper to make it easier to port the JS implementation ([#201](https://github.com/google/dotprompt/issues/201)) ([9295972](https://github.com/google/dotprompt/commit/92959720fbf2e8ee410d5b8c0c174c6ef464e667))
* **py/handlebarrz:** Python bindings for handlebars-rust ([#113](https://github.com/google/dotprompt/issues/113)) ([6b6a97e](https://github.com/google/dotprompt/commit/6b6a97e01acc49f53586eb5b8b2b410ae82ce6ce))
* **py:** local variables support workaround ([#318](https://github.com/google/dotprompt/issues/318)) ([d09598b](https://github.com/google/dotprompt/commit/d09598b969d5dbeaed3ca4136e903b4a2dc80531))
* python implementations of helpers ([#129](https://github.com/google/dotprompt/issues/129)) ([79c6ef3](https://github.com/google/dotprompt/commit/79c6ef3e9cc472fed3a832c00a1515ceef0981da))
* **python:** support lower versions of python (&gt;=3.10) ([#187](https://github.com/google/dotprompt/issues/187)) ([4240f9d](https://github.com/google/dotprompt/commit/4240f9d720891e350f9116aa4401ce6ea7fac5a3))
* use the HEAD version of addlicense ([#280](https://github.com/google/dotprompt/issues/280)) ([bdf0d36](https://github.com/google/dotprompt/commit/bdf0d36a430a363de4163f48394546cba884eaaf))
* use the more maintained YAML parsing lib at https://github.com/goccy/go-yaml ([#151](https://github.com/google/dotprompt/issues/151)) ([910b3a7](https://github.com/google/dotprompt/commit/910b3a72f3756296c3b01b96936a5bc4c9fa88ef))


### Bug Fixes

* change project name for pypi publish ([#200](https://github.com/google/dotprompt/issues/200)) ([2c07132](https://github.com/google/dotprompt/commit/2c0713264fb2c30bdc43f1bd9e51d416f96d1b7e))
* **docs:** update docs for handlebarrz ([#116](https://github.com/google/dotprompt/issues/116)) ([ce643b1](https://github.com/google/dotprompt/commit/ce643b1f5299ba2a6b214fb57965980d412c1a7b))
* **handlebarrz:** Compatibility tests for python 3.10 ([#190](https://github.com/google/dotprompt/issues/190)) ([e459e9c](https://github.com/google/dotprompt/commit/e459e9ce94f76d42615593987f99221b0f55a0d3))
* **license:** add license header to stub types file ([#144](https://github.com/google/dotprompt/issues/144)) ([0abd498](https://github.com/google/dotprompt/commit/0abd49848548f2148a37ec686d703126d8fe8504))
* **license:** use the full license header in rust source, script files and yaml spec files ([#143](https://github.com/google/dotprompt/issues/143)) ([77ccec9](https://github.com/google/dotprompt/commit/77ccec93a4bf5ccd65932a701676554866e68c6f))
* **license:** use the full license header in source code ([#142](https://github.com/google/dotprompt/issues/142)) ([64894ef](https://github.com/google/dotprompt/commit/64894ef898876b861c6c244d522f634cd8fcc842))
* **py/dotpromptz:** address compatibility with python 3.10 and add tox configuration for parallelized tests ([#188](https://github.com/google/dotprompt/issues/188)) ([d2ba21f](https://github.com/google/dotprompt/commit/d2ba21ff3e54f4ca4328b7e574bb6492699095bc))
* **py/handlebarrz:** helpers support in handlebarrz ([#291](https://github.com/google/dotprompt/issues/291)) ([d5d66a3](https://github.com/google/dotprompt/commit/d5d66a35858a068c2995b82fe54b62f0be4d057f))
* **scripts:** do not allow running scripts as root; prevent accidental mishaps; update rust checks ([#259](https://github.com/google/dotprompt/issues/259)) ([5cc067d](https://github.com/google/dotprompt/commit/5cc067dc44eaacab2e2dfa387bc79aa3f23d62c8))
* some lint in the rust code ([#250](https://github.com/google/dotprompt/issues/250)) ([3ef3dd8](https://github.com/google/dotprompt/commit/3ef3dd8ed98c0f5402b22fdba0e852074d2923e7))

## [0.1.1](https://github.com/google/dotprompt/compare/handlebarrz-v0.1.0...handlebarrz-0.1.1) (2025-10-24)


### Features

* cargo workspace configuration and bazel build files for hermetic environment ([#257](https://github.com/google/dotprompt/issues/257)) ([aef822e](https://github.com/google/dotprompt/commit/aef822ed484d256ba95a3544e132a9b33e0dc02d))
* **handlebarrz:** CI to publish rust python package ([#152](https://github.com/google/dotprompt/issues/152)) ([20765d8](https://github.com/google/dotprompt/commit/20765d83c50537cf935fe461a24f5c86d970d787))
* **handlebarrz:** native ifEquals, unlessEquals, and json helpers ([#121](https://github.com/google/dotprompt/issues/121)) ([e3619e9](https://github.com/google/dotprompt/commit/e3619e906cd0b69d854ca50d798e36cf44c130bd))
* partial test runner implementation now loads tests ([#139](https://github.com/google/dotprompt/issues/139)) ([b09dd2f](https://github.com/google/dotprompt/commit/b09dd2f9b8029317ce484d6f32d5a3fb89f5f7e1))
* **py/dotprompt:** render and compile implementations ([#263](https://github.com/google/dotprompt/issues/263)) ([961d0db](https://github.com/google/dotprompt/commit/961d0dbbd9c2ce522252bc3d92f6dde4b7fe9cc1))
* **py/dotpromptz:** add initial Dotprompt._resolve_partials implementation ([#215](https://github.com/google/dotprompt/issues/215)) ([03a161c](https://github.com/google/dotprompt/commit/03a161c3440a680bc0df472f35efa155fe0d5151))
* **py/dotpromptz:** configure handlebars to not escape by default ([#163](https://github.com/google/dotprompt/issues/163)) ([f7c33e1](https://github.com/google/dotprompt/commit/f7c33e1303476fd473e803f930ac1e1f9e1d87c9))
* **py/dotpromptz:** construct test-specific dotprompt instance with partials and partial resolver set up ([#275](https://github.com/google/dotprompt/issues/275)) ([0af9a64](https://github.com/google/dotprompt/commit/0af9a64acf50278bdffda337e19c66fbb97e43a3))
* **py/dotpromptz:** implement helpers in terms of the rust implementation of handlebars-rust and fix go flakiness ([#115](https://github.com/google/dotprompt/issues/115)) ([314c0b5](https://github.com/google/dotprompt/commit/314c0b5182aaad25bf4cfccb8207faa60f63256f))
* **py/dotpromptz:** initial bits of Dotprompt class ([#148](https://github.com/google/dotprompt/issues/148)) ([90f7838](https://github.com/google/dotprompt/commit/90f78384a958d41d78dee48497a78dfde11f4476))
* **py/handlebarrz:** add a Template.compile method to the Python wrapper to make it easier to port the JS implementation ([#201](https://github.com/google/dotprompt/issues/201)) ([9295972](https://github.com/google/dotprompt/commit/92959720fbf2e8ee410d5b8c0c174c6ef464e667))
* **py/handlebarrz:** Python bindings for handlebars-rust ([#113](https://github.com/google/dotprompt/issues/113)) ([6b6a97e](https://github.com/google/dotprompt/commit/6b6a97e01acc49f53586eb5b8b2b410ae82ce6ce))
* **py:** local variables support workaround ([#318](https://github.com/google/dotprompt/issues/318)) ([d09598b](https://github.com/google/dotprompt/commit/d09598b969d5dbeaed3ca4136e903b4a2dc80531))
* python implementations of helpers ([#129](https://github.com/google/dotprompt/issues/129)) ([79c6ef3](https://github.com/google/dotprompt/commit/79c6ef3e9cc472fed3a832c00a1515ceef0981da))
* **python:** support lower versions of python (&gt;=3.10) ([#187](https://github.com/google/dotprompt/issues/187)) ([4240f9d](https://github.com/google/dotprompt/commit/4240f9d720891e350f9116aa4401ce6ea7fac5a3))
* use the HEAD version of addlicense ([#280](https://github.com/google/dotprompt/issues/280)) ([bdf0d36](https://github.com/google/dotprompt/commit/bdf0d36a430a363de4163f48394546cba884eaaf))
* use the more maintained YAML parsing lib at https://github.com/goccy/go-yaml ([#151](https://github.com/google/dotprompt/issues/151)) ([910b3a7](https://github.com/google/dotprompt/commit/910b3a72f3756296c3b01b96936a5bc4c9fa88ef))


### Bug Fixes

* change project name for pypi publish ([#200](https://github.com/google/dotprompt/issues/200)) ([2c07132](https://github.com/google/dotprompt/commit/2c0713264fb2c30bdc43f1bd9e51d416f96d1b7e))
* **docs:** update docs for handlebarrz ([#116](https://github.com/google/dotprompt/issues/116)) ([ce643b1](https://github.com/google/dotprompt/commit/ce643b1f5299ba2a6b214fb57965980d412c1a7b))
* **handlebarrz:** Compatibility tests for python 3.10 ([#190](https://github.com/google/dotprompt/issues/190)) ([e459e9c](https://github.com/google/dotprompt/commit/e459e9ce94f76d42615593987f99221b0f55a0d3))
* **license:** add license header to stub types file ([#144](https://github.com/google/dotprompt/issues/144)) ([0abd498](https://github.com/google/dotprompt/commit/0abd49848548f2148a37ec686d703126d8fe8504))
* **license:** use the full license header in rust source, script files and yaml spec files ([#143](https://github.com/google/dotprompt/issues/143)) ([77ccec9](https://github.com/google/dotprompt/commit/77ccec93a4bf5ccd65932a701676554866e68c6f))
* **license:** use the full license header in source code ([#142](https://github.com/google/dotprompt/issues/142)) ([64894ef](https://github.com/google/dotprompt/commit/64894ef898876b861c6c244d522f634cd8fcc842))
* **py/dotpromptz:** address compatibility with python 3.10 and add tox configuration for parallelized tests ([#188](https://github.com/google/dotprompt/issues/188)) ([d2ba21f](https://github.com/google/dotprompt/commit/d2ba21ff3e54f4ca4328b7e574bb6492699095bc))
* **py/handlebarrz:** helpers support in handlebarrz ([#291](https://github.com/google/dotprompt/issues/291)) ([d5d66a3](https://github.com/google/dotprompt/commit/d5d66a35858a068c2995b82fe54b62f0be4d057f))
* **scripts:** do not allow running scripts as root; prevent accidental mishaps; update rust checks ([#259](https://github.com/google/dotprompt/issues/259)) ([5cc067d](https://github.com/google/dotprompt/commit/5cc067dc44eaacab2e2dfa387bc79aa3f23d62c8))
* some lint in the rust code ([#250](https://github.com/google/dotprompt/issues/250)) ([3ef3dd8](https://github.com/google/dotprompt/commit/3ef3dd8ed98c0f5402b22fdba0e852074d2923e7))
