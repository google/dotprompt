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

import com.redhat.devtools.lsp4ij.LanguageServerFactory
import com.redhat.devtools.lsp4ij.server.StreamConnectionProvider
import com.redhat.devtools.lsp4ij.server.ProcessStreamConnectionProvider
import com.intellij.openapi.project.Project
import java.io.File

/**
 * Factory for creating the Promptly LSP server connection.
 */
class PromptlyServerFactory : LanguageServerFactory {

    override fun createConnectionProvider(project: Project): StreamConnectionProvider {
        val promptlyPath = findPromptlyExecutable()
        val commands = listOf(promptlyPath, "lsp")
        return ProcessStreamConnectionProvider(commands)
    }

    /**
     * Finds the promptly executable in common locations.
     */
    private fun findPromptlyExecutable(): String {
        // Check PATH first
        val pathDirs = System.getenv("PATH")?.split(File.pathSeparator) ?: emptyList()
        for (dir in pathDirs) {
            val promptly = File(dir, "promptly")
            if (promptly.exists() && promptly.canExecute()) {
                return promptly.absolutePath
            }
        }

        // Check cargo bin directory
        val home = System.getProperty("user.home")
        val cargoPromptly = File(home, ".cargo/bin/promptly")
        if (cargoPromptly.exists() && cargoPromptly.canExecute()) {
            return cargoPromptly.absolutePath
        }

        // Fall back to just "promptly" and hope it's in PATH
        return "promptly"
    }
}
