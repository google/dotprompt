-- Copyright 2026 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--
-- SPDX-License-Identifier: Apache-2.0

--- Dotprompt Neovim module for LSP setup
--- @module dotprompt
local M = {}

--- Default configuration
M.config = {
  --- Path to promptly binary (empty = auto-detect)
  promptly_path = "",
  --- Enable format on save
  format_on_save = true,
  --- Enable LSP diagnostics
  diagnostics = true,
}

--- Find promptly executable in common locations
--- @return string|nil path to promptly or nil if not found
local function find_promptly()
  -- Check user config first
  if M.config.promptly_path ~= "" then
    if vim.fn.executable(M.config.promptly_path) == 1 then
      return M.config.promptly_path
    end
  end

  -- Check PATH
  if vim.fn.executable("promptly") == 1 then
    return "promptly"
  end

  -- Check cargo bin
  local home = vim.env.HOME or vim.env.USERPROFILE
  if home then
    local cargo_path = home .. "/.cargo/bin/promptly"
    if vim.fn.executable(cargo_path) == 1 then
      return cargo_path
    end
  end

  return nil
end

--- Setup LSP for Dotprompt files
--- @param opts table|nil Optional configuration overrides
function M.setup(opts)
  -- Merge user options
  M.config = vim.tbl_deep_extend("force", M.config, opts or {})

  -- Register filetype
  vim.filetype.add({
    extension = {
      prompt = "dotprompt",
    },
  })

  -- Find promptly
  local promptly_path = find_promptly()
  if not promptly_path then
    vim.notify(
      "Dotprompt: promptly not found. Install with: cargo install --path rs/promptly",
      vim.log.levels.WARN
    )
    return
  end

  -- Setup LSP using nvim-lspconfig if available
  local ok, lspconfig = pcall(require, "lspconfig")
  if not ok then
    vim.notify(
      "Dotprompt: nvim-lspconfig not found. Install it for LSP features.",
      vim.log.levels.WARN
    )
    return
  end

  local configs = require("lspconfig.configs")

  -- Register promptly as an LSP server
  if not configs.promptly then
    configs.promptly = {
      default_config = {
        cmd = { promptly_path, "lsp" },
        filetypes = { "dotprompt" },
        root_dir = lspconfig.util.find_git_ancestor,
        single_file_support = true,
        settings = {},
      },
    }
  end

  -- Start the server with user callbacks
  lspconfig.promptly.setup({
    on_attach = function(client, bufnr)
      -- Enable format on save if configured
      if M.config.format_on_save then
        vim.api.nvim_create_autocmd("BufWritePre", {
          buffer = bufnr,
          callback = function()
            vim.lsp.buf.format({ async = false })
          end,
        })
      end

      -- Set up keymaps
      local bufopts = { noremap = true, silent = true, buffer = bufnr }
      vim.keymap.set("n", "<leader>f", function()
        vim.lsp.buf.format({ async = true })
      end, bufopts)
      vim.keymap.set("n", "K", vim.lsp.buf.hover, bufopts)
      vim.keymap.set("n", "gd", vim.lsp.buf.definition, bufopts)
      vim.keymap.set("n", "gr", vim.lsp.buf.references, bufopts)
      vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, bufopts)
      vim.keymap.set("n", "<leader>ca", vim.lsp.buf.code_action, bufopts)
    end,

    capabilities = vim.lsp.protocol.make_client_capabilities(),
  })

  vim.notify("Dotprompt: LSP configured with " .. promptly_path, vim.log.levels.INFO)
end

--- Manually trigger document formatting
function M.format()
  vim.lsp.buf.format({ async = true })
end

--- Restart the LSP server
function M.restart()
  vim.cmd("LspRestart promptly")
end

return M
