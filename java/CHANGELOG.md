# Changelog

## [0.1.1](https://github.com/google/dotprompt/compare/dotprompt-java-0.1.0...dotprompt-java-0.1.1) (2026-02-27)


### Features

* cargo workspace configuration and bazel build files for hermetic environment ([#257](https://github.com/google/dotprompt/issues/257)) ([aef822e](https://github.com/google/dotprompt/commit/aef822ed484d256ba95a3544e132a9b33e0dc02d))
* **java:** add basic types used elsewhere ([#381](https://github.com/google/dotprompt/issues/381)) ([1e51a69](https://github.com/google/dotprompt/commit/1e51a690a839ac84d50f627c88784617c08e1ebc))
* **java:** add bazel defs to run spec tests ([#386](https://github.com/google/dotprompt/issues/386)) ([32bf3bf](https://github.com/google/dotprompt/commit/32bf3bf0fb399d89e95e6d3d22580211f99acc5c))
* **java:** add dotprompt implementation ([#389](https://github.com/google/dotprompt/issues/389)) ([4464332](https://github.com/google/dotprompt/commit/4464332b5249530bdcfa1198847c677a9c388d74))
* **java:** add handlebars helpers implementation ([#380](https://github.com/google/dotprompt/issues/380)) ([56579b7](https://github.com/google/dotprompt/commit/56579b794e0053b8c00780cd3e2680a7f102844f))
* **java:** add java formatter ([#270](https://github.com/google/dotprompt/issues/270)) ([00add2e](https://github.com/google/dotprompt/commit/00add2edf72babfbae3f391a84b521f142fc947d))
* **java:** add store implementation ([#387](https://github.com/google/dotprompt/issues/387)) ([16a241a](https://github.com/google/dotprompt/commit/16a241aba6fa7e132bc03e0f313081f5aafd5716))
* **java:** parsers ([#383](https://github.com/google/dotprompt/issues/383)) ([a5fdd61](https://github.com/google/dotprompt/commit/a5fdd612d248637f791c6108cae2eb59c76c659e))
* **java:** resolver and store types ([#382](https://github.com/google/dotprompt/issues/382)) ([27931e1](https://github.com/google/dotprompt/commit/27931e14c6bb3199ff0fbd7afc8a732c0150a6b9))
* **promptly:** add lsp, fmt, and check implementations ([#438](https://github.com/google/dotprompt/issues/438)) ([27fd3d4](https://github.com/google/dotprompt/commit/27fd3d4c7aa96e09c46cb54546da1783be2f6a6e))
* **rs:** store implementation for rust and go ([#430](https://github.com/google/dotprompt/issues/430)) ([ea798c2](https://github.com/google/dotprompt/commit/ea798c216c55cedfa052e528f0e36c5ad01a9273))
* **rules_dart,rules_flutter:** enhance Bazel rules with workers and linting fixes ([#513](https://github.com/google/dotprompt/issues/513)) ([5369b40](https://github.com/google/dotprompt/commit/5369b4046eea9805f7dbcf026434035d55e2b095))
* use the HEAD version of addlicense ([#280](https://github.com/google/dotprompt/issues/280)) ([bdf0d36](https://github.com/google/dotprompt/commit/bdf0d36a430a363de4163f48394546cba884eaaf))


### Bug Fixes

* add cycle detection to partial resolution across all runtimes ([#431](https://github.com/google/dotprompt/issues/431)) ([4e23d44](https://github.com/google/dotprompt/commit/4e23d44865415c13ab1a5b52c2930e32d26eac5d))
* compile render issue ([#404](https://github.com/google/dotprompt/issues/404)) ([7152799](https://github.com/google/dotprompt/commit/71527994142de94f7897ce296d31581519e97fe8))
* **docs:** update deprecated model references to Gemini 2.5/3 ([#541](https://github.com/google/dotprompt/issues/541)) ([fce691c](https://github.com/google/dotprompt/commit/fce691c831abddfcfc8bcdeee79d564c141298d0))
* Ensure helper behavior parity across all runtimes ([#395](https://github.com/google/dotprompt/issues/395)) ([76de7ba](https://github.com/google/dotprompt/commit/76de7ba6065e07667dda5d3acb8b57ce36b48662))
* **java:** consistent synchronization in resolveTools ([#429](https://github.com/google/dotprompt/issues/429)) ([ad4f33d](https://github.com/google/dotprompt/commit/ad4f33d5e7e48d4d67c316a9a2d9134526a78cbd))
* **java:** pin version for handlebars v4.4.0 ([#309](https://github.com/google/dotprompt/issues/309)) ([17a510f](https://github.com/google/dotprompt/commit/17a510ff51fdc49c8e696fa3798b55243830e558))
* path traversal security hardening (CWE-22) ([#413](https://github.com/google/dotprompt/issues/413)) ([5be598e](https://github.com/google/dotprompt/commit/5be598e9dcd617924150500974173fb0dbbc7acf))
* update lock file ([#258](https://github.com/google/dotprompt/issues/258)) ([13a4b25](https://github.com/google/dotprompt/commit/13a4b2592a71aa0585af6ce6f42d92e0da9a8f3c))
