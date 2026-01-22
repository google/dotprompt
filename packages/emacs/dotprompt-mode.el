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
;; Version: 0.1.0
;; Keywords: languages, dotprompt
;; URL: https://github.com/google/dotprompt

;;; Commentary:

;; Major mode for editing Dotprompt files (.prompt).
;; Provides minimal syntax highlighting for markers, helpers, and partials.
;; For best results with frontmatter, consider using polymode or mmm-mode.

;;; Code:

(defgroup dotprompt nil
  "Major mode for editing Dotprompt files."
  :prefix "dotprompt-"
  :group 'languages)

(defvar dotprompt-mode-hook nil
  "Hook run after entering `dotprompt-mode'.")

(defvar dotprompt-font-lock-keywords
  (list
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
  
  ;; Font lock
  (setq-local font-lock-defaults '(dotprompt-font-lock-keywords)))

;;;###autoload
(add-to-list 'auto-mode-alist '("\\.prompt\\'" . dotprompt-mode))

(provide 'dotprompt-mode)

;;; dotprompt-mode.el ends here
