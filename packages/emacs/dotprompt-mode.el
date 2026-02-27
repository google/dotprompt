;;; dotprompt-mode.el --- Major mode for Dotprompt files  -*- lexical-binding: t; -*-

;; Copyright 2026 Google LLC
;;
;; Licensed under the Apache License, Version 2.0 (the "License");
;; you may not use this file except in compliance with the License.
;; You may obtain a copy of the License at
;;
;;     http://www.apache.org/licenses/LICENSE-2.0
;;
;; Unless required by applicable law or agreed to in writing, software
;; distributed under the License is distributed on an "AS IS" BASIS,
;; WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
;; See the License for the specific language governing permissions and
;; limitations under the License.

;; Author: Google
;; Version: 0.3.0
;; Keywords: languages, dotprompt
;; URL: https://github.com/google/dotprompt
;; Package-Requires: ((emacs "27.1"))

;;; Commentary:

;; Major mode for editing Dotprompt files (.prompt).
;; Provides syntax highlighting for markers, helpers, and partials.
;; Includes LSP integration via eglot or lsp-mode for diagnostics,
;; formatting, and hover documentation when `promptly` is installed.
;;
;; Features:
;; - Syntax highlighting for Handlebars templates
;; - LSP integration via eglot (Emacs 29+) or lsp-mode
;; - Format buffer command
;; - Format on save (optional)
;;
;; For best results with frontmatter, consider using polymode or mmm-mode.

;;; Code:

(defgroup dotprompt nil
  "Major mode for editing Dotprompt files."
  :prefix "dotprompt-"
  :group 'languages)

(defcustom dotprompt-promptly-path "promptly"
  "Path to the promptly executable for LSP features."
  :type 'string
  :group 'dotprompt)

(defcustom dotprompt-format-on-save nil
  "When non-nil, format the buffer before saving."
  :type 'boolean
  :group 'dotprompt)

(defvar dotprompt-mode-hook nil
  "Hook run after entering `dotprompt-mode'.")

(defvar dotprompt-font-lock-keywords
  (list
   ;; YAML frontmatter delimiters
   '("^---$" . font-lock-preprocessor-face)
   
   ;; YAML keys in frontmatter (word followed by colon at start of line or after indentation)
   '("^\\s-*\\([a-zA-Z_][a-zA-Z0-9_-]*\\):" 1 font-lock-keyword-face)
   
   ;; YAML string values (unquoted, after colon and space)
   '(":\\s-+\\([a-zA-Z][a-zA-Z0-9._/-]*\\)$" 1 font-lock-string-face)
   
   ;; YAML numeric values
   '(":\\s-+\\([0-9]+\\.?[0-9]*\\)$" 1 font-lock-constant-face)
   
   ;; Handlebars block comments {{!-- ... --}}
   '("{{!--\\(.\\|\n\\)*?--}}" . font-lock-comment-face)
   
   ;; Handlebars inline comments {{! ... }}
   '("{{![^}]*}}" . font-lock-comment-face)
   
   ;; Partials {{> partialName}} - highlight partial indicator and name
   '("{{\\(>\\)\\s-*\\([a-zA-Z0-9_.-]+\\)"
     (1 font-lock-keyword-face)
     (2 font-lock-builtin-face))
   
   ;; Block opening helpers {{#each items}} - highlight # + keyword AND the argument
   '("{{\\(#\\)\\(if\\|unless\\|each\\|with\\|log\\|lookup\\|ifEquals\\|unlessEquals\\)\\(?:\\s-+\\([a-zA-Z0-9_.-]+\\)\\)?"
     (1 font-lock-keyword-face)
     (2 font-lock-keyword-face)
     (3 font-lock-variable-name-face nil t))
   
   ;; Block closing helpers {{/each}} - highlight / and keyword
   '("{{\\(/\\)\\(if\\|unless\\|each\\|with\\|log\\|lookup\\|ifEquals\\|unlessEquals\\)}}"
     (1 font-lock-keyword-face)
     (2 font-lock-keyword-face))
   
   ;; Else keyword {{else}}
   '("{{\\(else\\)}}" 1 font-lock-keyword-face)
   
   ;; Dotprompt helpers {{json this indent=2}}
   '("{{\\(json\\|role\\|history\\|section\\|media\\|ifEquals\\|unlessEquals\\)"
     1 font-lock-function-name-face)
   
   ;; Helper named parameters (param=value)
   '("\\b\\([a-zA-Z_][a-zA-Z0-9_]*\\)=" 1 font-lock-type-face)
   
   ;; Quoted strings inside handlebars
   '("{{[^}]*\\([\"'][^\"']*[\"']\\)" 1 font-lock-string-face)
   
   ;; Boolean and null constants inside handlebars
   '("{{[^}]*\\b\\(true\\|false\\|null\\|undefined\\)\\b" 1 font-lock-constant-face)
   
   ;; Numbers inside handlebars
   '("{{[^}]*\\b\\([0-9]+\\)\\b" 1 font-lock-constant-face)
   
   ;; Simple variable references {{variableName}} or {{this}}
   '("{{\\([a-zA-Z_][a-zA-Z0-9_.]*\\)}}" 1 font-lock-variable-name-face)
   
   ;; The handlebars delimiters themselves
   '("\\({{\\)" 1 font-lock-constant-face)
   '("\\(}}\\)" 1 font-lock-constant-face)
   
   ;; License header comments (lines starting with #)
   ;; This is at the END with override flag `t` to ensure entire comment lines
   ;; are highlighted uniformly, overriding any patterns that matched within them
   '("^#.*$" 0 font-lock-comment-face t)
   )
  "Syntax highlighting for Dotprompt templates.")

(defvar dotprompt-mode-map
  (let ((map (make-sparse-keymap)))
    (define-key map (kbd "C-c C-f") #'dotprompt-format-buffer)
    map)
  "Keymap for `dotprompt-mode'.")

;;;###autoload
(define-derived-mode dotprompt-mode prog-mode "Dotprompt"
  "Major mode for editing Dotprompt files."
  
  ;; Comments
  (setq-local comment-start "{{! ")
  (setq-local comment-end " }}")
  
  ;; Indentation
  (setq-local indent-tabs-mode nil)
  (setq-local tab-width 2)
  
  ;; Font lock
  (setq-local font-lock-defaults '(dotprompt-font-lock-keywords))
  
  ;; Format on save hook
  (when dotprompt-format-on-save
    (add-hook 'before-save-hook #'dotprompt-format-buffer nil t)))

;;;###autoload
(add-to-list 'auto-mode-alist '("\\.prompt\\'" . dotprompt-mode))

;;; Format Command

(defun dotprompt-format-buffer ()
  "Format the current buffer using promptly or LSP.
If an LSP client is connected, use LSP formatting.
Otherwise, call promptly fmt directly."
  (interactive)
  (cond
   ;; Try eglot first (Emacs 29+)
   ((and (fboundp 'eglot-managed-p) (eglot-managed-p))
    (eglot-format-buffer))
   ;; Try lsp-mode
   ((and (fboundp 'lsp-workspaces) (lsp-workspaces))
    (lsp-format-buffer))
   ;; Fall back to direct promptly call
   (t
    (dotprompt--format-with-promptly))))

(defun dotprompt--format-with-promptly ()
  "Format the current buffer using promptly fmt."
  (let ((temp-file (make-temp-file "dotprompt-format" nil ".prompt"))
        (original-point (point)))
    (unwind-protect
        (progn
          (write-region (point-min) (point-max) temp-file nil 'silent)
          (let ((exit-code (call-process dotprompt-promptly-path nil nil nil
                                         "fmt" temp-file)))
            (when (zerop exit-code)
              (erase-buffer)
              (insert-file-contents temp-file)
              (goto-char (min original-point (point-max))))))
      (delete-file temp-file))))

;;; LSP Integration

;; Eglot integration (built-in to Emacs 29+)
(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs
               `(dotprompt-mode . (,dotprompt-promptly-path "lsp"))))

;; lsp-mode integration
(with-eval-after-load 'lsp-mode
  (add-to-list 'lsp-language-id-configuration '(dotprompt-mode . "dotprompt"))
  
  (lsp-register-client
   (make-lsp-client
    :new-connection (lsp-stdio-connection
                     (lambda () (list dotprompt-promptly-path "lsp")))
    :major-modes '(dotprompt-mode)
    :server-id 'promptly
    :priority -1)))

(provide 'dotprompt-mode)

;;; dotprompt-mode.el ends here
