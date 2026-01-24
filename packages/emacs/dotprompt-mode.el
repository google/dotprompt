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
;; Version: 0.2.0
;; Keywords: languages, dotprompt
;; URL: https://github.com/google/dotprompt

;;; Commentary:

;; Major mode for editing Dotprompt files (.prompt).
;; Provides syntax highlighting for markers, helpers, and partials.
;; Includes LSP integration via eglot or lsp-mode for diagnostics,
;; formatting, and hover documentation when `promptly` is installed.
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

(defvar dotprompt-mode-hook nil
  "Hook run after entering `dotprompt-mode'.")

(defvar dotprompt-font-lock-keywords
  (list
   ;; License header comments (lines starting with #)
   '("^#.*$" . font-lock-comment-face)
   
   ;; Markers <<<dotprompt:role:system>>>
   '("<<<dotprompt:[^>]+>>>" . font-lock-preprocessor-face)
   
   ;; Partials {{> partialName}}
   '("{{>\\s-*[a-zA-Z0-9_.-]+\\s-*\\(.*?\\)}}" . font-lock-builtin-face)
   
   ;; Handlebars Control Flow {{#if}} {{/if}}
   '("{{[#/]\\(if\\|unless\\|each\\|with\\|log\\|lookup\\|else\\)" 1 font-lock-keyword-face)
   
   ;; Dotprompt Helpers (distinct color)
   '("\\<\\(json\\|role\\|history\\|section\\|media\\|ifEquals\\|unlessEquals\\)\\>" . font-lock-function-name-face)
   
   ;; General tags
   '("{{" . font-lock-delimiter-face)
   '("}}" . font-lock-delimiter-face)
   )
  "Minimal highlighting for Dotprompt.")

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
  (setq-local font-lock-defaults '(dotprompt-font-lock-keywords)))

;;;###autoload
(add-to-list 'auto-mode-alist '("\\.prompt\\'" . dotprompt-mode))

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

