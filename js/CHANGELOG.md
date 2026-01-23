# Changelog

## [0.2.10](https://github.com/google/dotprompt/compare/dotprompt-0.2.9...dotprompt-0.2.10) (2026-01-23)


### Features

* add implementation of helpers and util modules; move interfaces into dotpromptz project ([#73](https://github.com/google/dotprompt/issues/73)) ([8c7aea1](https://github.com/google/dotprompt/commit/8c7aea1faffaf823d01b132e55cb175a4fca5ccb))
* adds renderMetadata method to render metadata without prompt inputs ([#11](https://github.com/google/dotprompt/issues/11)) ([7706cb7](https://github.com/google/dotprompt/commit/7706cb7e6bce0fede5c8e2f2285be8f9aa3230ab))
* cargo workspace configuration and bazel build files for hermetic environment ([#257](https://github.com/google/dotprompt/issues/257)) ([aef822e](https://github.com/google/dotprompt/commit/aef822ed484d256ba95a3544e132a9b33e0dc02d))
* **go/parse:** parse.go implementation [#62](https://github.com/google/dotprompt/issues/62) ([#87](https://github.com/google/dotprompt/issues/87)) ([d5dc13c](https://github.com/google/dotprompt/commit/d5dc13c0bf0437875a3b133511ffed474a8b3bf9))
* **java:** parsers ([#383](https://github.com/google/dotprompt/issues/383)) ([a5fdd61](https://github.com/google/dotprompt/commit/a5fdd612d248637f791c6108cae2eb59c76c659e))
* **js:** switch to typescript-go preview ([#300](https://github.com/google/dotprompt/issues/300)) ([a6d09f1](https://github.com/google/dotprompt/commit/a6d09f1c3cce2c1a6b3221dcdf772ec16ceda212))
* **packages/vscode:** add initial implementation of vscode extension ([#407](https://github.com/google/dotprompt/issues/407)) ([13917de](https://github.com/google/dotprompt/commit/13917de802145e17f865c61be04e0407f3cc60a0))
* parseDocument python ([#80](https://github.com/google/dotprompt/issues/80)) ([82ebc36](https://github.com/google/dotprompt/commit/82ebc3672e8de051dfbdd92968ed3f84c79a247f))
* partial test runner implementation now loads tests ([#139](https://github.com/google/dotprompt/issues/139)) ([b09dd2f](https://github.com/google/dotprompt/commit/b09dd2f9b8029317ce484d6f32d5a3fb89f5f7e1))
* **py/dotprompt:** render and compile implementations ([#263](https://github.com/google/dotprompt/issues/263)) ([961d0db](https://github.com/google/dotprompt/commit/961d0dbbd9c2ce522252bc3d92f6dde4b7fe9cc1))
* **py/dotpromptz:** _resolve_metadata for dotprompt ([#226](https://github.com/google/dotprompt/issues/226)) ([cfcc87b](https://github.com/google/dotprompt/commit/cfcc87b57e49785c2356b03fbc5b7bf773472683))
* **py/dotpromptz:** add initial Dotprompt._resolve_tools implementation and raise ValueError when resolver is None ([#214](https://github.com/google/dotprompt/issues/214)) ([57caf5d](https://github.com/google/dotprompt/commit/57caf5d9a9f4fe720c67f99fd10439d5ebe434dc))
* **py/dotpromptz:** simpler spec test runner harness ([#266](https://github.com/google/dotprompt/issues/266)) ([89378bf](https://github.com/google/dotprompt/commit/89378bfded004f3b246c90f6474c2fb972037956))
* **py/dotpromptz:** translate render_metadata for dotprompt.py from ts ([#227](https://github.com/google/dotprompt/issues/227)) ([ae1919b](https://github.com/google/dotprompt/commit/ae1919b3457824241c734fdf8328f61279fb6710))
* **py:** implement identify_partials in terms of regexps since we do not have an AST to walk [#90](https://github.com/google/dotprompt/issues/90) ([#150](https://github.com/google/dotprompt/issues/150)) ([f802275](https://github.com/google/dotprompt/commit/f8022755d7eef716bbb54dd08a2c3a061250d393))
* **py:** implementation of parse.py; refactor parse.ts and update tests. ([#79](https://github.com/google/dotprompt/issues/79)) ([47e7245](https://github.com/google/dotprompt/commit/47e7245c0aae710b102178019d1f3449c2f1af66))
* **python:** add OpenAI adapter implementation for dotprompt [#38](https://github.com/google/dotprompt/issues/38) ([#97](https://github.com/google/dotprompt/issues/97)) ([d171f87](https://github.com/google/dotprompt/commit/d171f8792ecf08f446e18ea3bbd5309cafa1d8a3))
* script to update all deps in one go and update deps ([#130](https://github.com/google/dotprompt/issues/130)) ([09ac58e](https://github.com/google/dotprompt/commit/09ac58e4512fae817a63f731ac0db80967842436))
* use the HEAD version of addlicense ([#280](https://github.com/google/dotprompt/issues/280)) ([bdf0d36](https://github.com/google/dotprompt/commit/bdf0d36a430a363de4163f48394546cba884eaaf))


### Bug Fixes

* changed handlebars import to fix downstream libCheck errors ([#18](https://github.com/google/dotprompt/issues/18)) ([c43bf8d](https://github.com/google/dotprompt/commit/c43bf8d83c81a6a61421c95ebba7a733e9ebc4e4))
* **deps:** switch to version 1.23 of go; update pnpm deps ([#153](https://github.com/google/dotprompt/issues/153)) ([672b8da](https://github.com/google/dotprompt/commit/672b8da68e784abd17a14f9f1f292d9b65b88a80))
* Ensure helper behavior parity across all runtimes ([#395](https://github.com/google/dotprompt/issues/395)) ([76de7ba](https://github.com/google/dotprompt/commit/76de7ba6065e07667dda5d3acb8b57ce36b48662))
* formatting and license headers for source and commit messages [#32](https://github.com/google/dotprompt/issues/32) ([#33](https://github.com/google/dotprompt/issues/33)) ([4ba47de](https://github.com/google/dotprompt/commit/4ba47de715d26e5b5abe4d4ba7210662c5894fc4))
* **go,py:** type fixes and ensure we build/lint the go code in hooks and ci ([#83](https://github.com/google/dotprompt/issues/83)) ([19a8257](https://github.com/google/dotprompt/commit/19a8257f4f73b776229d5324a0366fd9a79c20aa))
* **js:** add unit tests to ensure we cover {CR, CRLF, LF} line endings ([#253](https://github.com/google/dotprompt/issues/253)) ([2c9f33b](https://github.com/google/dotprompt/commit/2c9f33b83390c76916da52bfed206d664fc3431f))
* **js:** an issue with loose equality for helpers; add missing tests for some helpers [#53](https://github.com/google/dotprompt/issues/53) [#54](https://github.com/google/dotprompt/issues/54) ([#55](https://github.com/google/dotprompt/issues/55)) ([f645628](https://github.com/google/dotprompt/commit/f645628a50def0b661009311ac7ed84fb358e0f0))
* **js:** clean up redundant call to register helpers that have already been registered ([#261](https://github.com/google/dotprompt/issues/261)) ([84e3c0c](https://github.com/google/dotprompt/commit/84e3c0cfd8da3b0292eebb2fe8a771fe41d09038))
* **js:** clean up some variable names and types to make their meaning clearer ([#262](https://github.com/google/dotprompt/issues/262)) ([55aff53](https://github.com/google/dotprompt/commit/55aff5331fae18fe8b4c0f02e1456f143003fa5b))
* **js:** Don't escape HTML in handlebars tags. ([#159](https://github.com/google/dotprompt/issues/159)) ([ac66a24](https://github.com/google/dotprompt/commit/ac66a244c31690d2fe1ce4f0d34cbf6e6fcb8374))
* **js:** Fixes broken "LoadOptions" type, bumps to v1.1.1 ([#168](https://github.com/google/dotprompt/issues/168)) ([45346e7](https://github.com/google/dotprompt/commit/45346e76badfbd5e448657f098fdb069de069c52))
* **js:** keep tsc as primary compiler for now ([#313](https://github.com/google/dotprompt/issues/313)) ([417a534](https://github.com/google/dotprompt/commit/417a534d0fc6612786a0a0eb9dc420fdbd29361b))
* **js:** line-separator matching ([#249](https://github.com/google/dotprompt/issues/249)) ([54e3873](https://github.com/google/dotprompt/commit/54e387393af2dc46ecd782cc7109f7c4d502a883))
* **js:** make dotprompt.renderPicoschema resolve and convert input and output schemas concurrently ([#225](https://github.com/google/dotprompt/issues/225)) ([42ea434](https://github.com/google/dotprompt/commit/42ea43444d004e32cbe3930cd730de3478b385ec))
* **js:** some lint ([#299](https://github.com/google/dotprompt/issues/299)) ([46c1283](https://github.com/google/dotprompt/commit/46c1283c542e661347c69d6c9bdfb38116fb0980))
* **license:** use the full license header in source code ([#142](https://github.com/google/dotprompt/issues/142)) ([64894ef](https://github.com/google/dotprompt/commit/64894ef898876b861c6c244d522f634cd8fcc842))
* only set description on the resolve schema if available (avoid null description being set) ([#16](https://github.com/google/dotprompt/issues/16)) ([1fc648c](https://github.com/google/dotprompt/commit/1fc648c9834b63ff0dc36272521229abf66c0155))
* **py/dotpromptz:** register initial helpers and partials correctly ([#260](https://github.com/google/dotprompt/issues/260)) ([0752865](https://github.com/google/dotprompt/commit/0752865b415c6cc90c87e3113b537632a52e3423))
* remove spurious role type `assistant` ([#169](https://github.com/google/dotprompt/issues/169)) ([1b5142c](https://github.com/google/dotprompt/commit/1b5142c4a7ad20ef722d438cefa0b93a82d7adbb))
* Resolve webpack warnings with handlebar ([#320](https://github.com/google/dotprompt/issues/320)) ([765220a](https://github.com/google/dotprompt/commit/765220ab4257a35f8b108eda5fed2bebfb73953b))
* **scripts/setup:** update the location for the captainhook binary; minor formatting fixes for biome ([#328](https://github.com/google/dotprompt/issues/328)) ([f9183f8](https://github.com/google/dotprompt/commit/f9183f819725891cae16bd3452fea389aac9664d))
