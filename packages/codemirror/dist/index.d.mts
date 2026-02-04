import * as _codemirror_state from '@codemirror/state';
import { Extension } from '@codemirror/state';
import { CompletionContext, CompletionResult } from '@codemirror/autocomplete';
import { StreamLanguage, StringStream, HighlightStyle } from '@codemirror/language';

/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Completion source for Dotprompt files.
 */
declare function dotpromptCompletions(context: CompletionContext): CompletionResult | null;

/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Token types for Dotprompt syntax.
 */
type TokenType = 'comment' | 'keyword' | 'string' | 'number' | 'atom' | 'variable' | 'variable-2' | 'variable-3' | 'meta' | 'bracket' | 'tag' | 'attribute' | 'property' | 'operator' | null;
/**
 * Parser state for the Dotprompt StreamLanguage.
 */
interface DotpromptState {
    /** Current parsing context */
    context: 'root' | 'frontmatter' | 'template' | 'handlebars';
    /** Whether we're in a block comment */
    inBlockComment: boolean;
    /** Depth of nested handlebars blocks */
    blockDepth: number;
}
/**
 * StreamLanguage mode for Dotprompt.
 */
declare const dotpromptStreamParser: {
    name: string;
    startState(): DotpromptState;
    token(stream: StringStream, state: DotpromptState): TokenType;
};
/**
 * CodeMirror StreamLanguage instance for Dotprompt.
 */
declare const dotpromptLanguage: StreamLanguage<DotpromptState>;

/**
 * Dark theme highlighting for Dotprompt.
 * Uses colors similar to VS Code's dark theme.
 */
declare const dotpromptDarkHighlighting: HighlightStyle;
/**
 * Light theme highlighting for Dotprompt.
 */
declare const dotpromptLightHighlighting: HighlightStyle;
/**
 * Dark theme extension for Dotprompt.
 */
declare const dotpromptDarkTheme: _codemirror_state.Extension;
/**
 * Light theme extension for Dotprompt.
 */
declare const dotpromptLightTheme: _codemirror_state.Extension;

/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Dotprompt language support for CodeMirror.
 * Includes language definition and completion.
 */
declare function dotprompt(): Extension;

export { dotprompt, dotpromptCompletions, dotpromptDarkHighlighting, dotpromptDarkTheme, dotpromptLanguage, dotpromptLightHighlighting, dotpromptLightTheme, dotpromptStreamParser };
