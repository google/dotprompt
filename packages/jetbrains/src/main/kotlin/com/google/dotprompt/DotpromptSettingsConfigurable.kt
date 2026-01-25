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

import com.intellij.openapi.fileChooser.FileChooserDescriptorFactory
import com.intellij.openapi.options.Configurable
import com.intellij.openapi.ui.TextFieldWithBrowseButton
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBLabel
import com.intellij.util.ui.FormBuilder
import javax.swing.JComponent
import javax.swing.JPanel

/**
 * Settings UI for the Dotprompt plugin.
 * Accessible via Settings > Languages & Frameworks > Dotprompt.
 */
class DotpromptSettingsConfigurable : Configurable {

    private var promptlyPathField: TextFieldWithBrowseButton? = null
    private var formatOnSaveCheckbox: JBCheckBox? = null
    private var enableLspCheckbox: JBCheckBox? = null

    override fun getDisplayName(): String = "Dotprompt"

    override fun createComponent(): JComponent {
        promptlyPathField = TextFieldWithBrowseButton().apply {
            addBrowseFolderListener(
                "Select Promptly Executable",
                "Select the path to the promptly executable",
                null,
                FileChooserDescriptorFactory.createSingleFileDescriptor()
            )
        }

        formatOnSaveCheckbox = JBCheckBox("Format on save")
        enableLspCheckbox = JBCheckBox("Enable LSP features (diagnostics, formatting, hover)")

        return FormBuilder.createFormBuilder()
            .addLabeledComponent(
                JBLabel("Promptly path:"),
                promptlyPathField!!,
                1,
                false
            )
            .addComponent(
                JBLabel("<html><small>Leave empty to auto-detect from PATH or ~/.cargo/bin</small></html>"),
                0
            )
            .addSeparator()
            .addComponent(enableLspCheckbox!!, 1)
            .addComponent(formatOnSaveCheckbox!!, 1)
            .addComponentFillVertically(JPanel(), 0)
            .panel
    }

    override fun isModified(): Boolean {
        val settings = DotpromptSettings.getInstance()
        return promptlyPathField?.text != settings.promptlyPath ||
                formatOnSaveCheckbox?.isSelected != settings.formatOnSave ||
                enableLspCheckbox?.isSelected != settings.enableLsp
    }

    override fun apply() {
        val settings = DotpromptSettings.getInstance()
        settings.promptlyPath = promptlyPathField?.text ?: ""
        settings.formatOnSave = formatOnSaveCheckbox?.isSelected ?: true
        settings.enableLsp = enableLspCheckbox?.isSelected ?: true
    }

    override fun reset() {
        val settings = DotpromptSettings.getInstance()
        promptlyPathField?.text = settings.promptlyPath
        formatOnSaveCheckbox?.isSelected = settings.formatOnSave
        enableLspCheckbox?.isSelected = settings.enableLsp
    }

    override fun disposeUIResources() {
        promptlyPathField = null
        formatOnSaveCheckbox = null
        enableLspCheckbox = null
    }
}
