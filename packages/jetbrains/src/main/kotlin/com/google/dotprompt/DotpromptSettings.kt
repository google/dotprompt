// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

package com.google.dotprompt

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage

/**
 * Persistent settings for the Dotprompt plugin.
 */
@Service(Service.Level.APP)
@State(
    name = "DotpromptSettings",
    storages = [Storage("dotprompt.xml")]
)
class DotpromptSettings : PersistentStateComponent<DotpromptSettings.State> {

    /**
     * Settings state data class.
     */
    data class State(
        /** Custom path to the promptly executable. */
        var promptlyPath: String = "",
        /** Whether to enable format on save. */
        var formatOnSave: Boolean = true,
        /** Whether to enable LSP features. */
        var enableLsp: Boolean = true
    )

    private var myState = State()

    override fun getState(): State = myState

    override fun loadState(state: State) {
        myState = state
    }

    /** Custom path to the promptly executable. Empty string means auto-detect. */
    var promptlyPath: String
        get() = myState.promptlyPath
        set(value) { myState.promptlyPath = value }

    /** Whether to enable format on save. */
    var formatOnSave: Boolean
        get() = myState.formatOnSave
        set(value) { myState.formatOnSave = value }

    /** Whether to enable LSP features. */
    var enableLsp: Boolean
        get() = myState.enableLsp
        set(value) { myState.enableLsp = value }

    companion object {
        fun getInstance(): DotpromptSettings =
            ApplicationManager.getApplication().getService(DotpromptSettings::class.java)
    }
}
