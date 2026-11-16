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

package dotprompt

// In-band markers used to turn a rendered template string into messages.
//
// The role, history, section and media helpers emit markers into the rendered
// string, which is then split back apart by ToMessages. Because the rendered
// string also contains user-supplied variable values verbatim, every marker
// carries a random per-render nonce and the splitter only honors markers with
// that nonce. Anything else that merely looks like a marker (e.g. typed by an
// end user) stays plain text.
//
// Marker format: <<<dotprompt:{nonce}:{body}>>>, where body is one of
// "role:{name}", "history", "section {name}", "media:url {url} [{contentType}]".

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"regexp"
	"strings"
)

// markerNonceDataKey is the key under which the per-render nonce is stored in
// the private data frame. It is written after DataArgument.Context is copied
// into the frame so user context can't override it.
const markerNonceDataKey = "__dotpromptMarkerNonce"

// markerNoncePattern matches a valid nonce: 128 bits as lowercase hex.
var markerNoncePattern = regexp.MustCompile(`^[0-9a-f]{32}$`)

// errInvalidMarkerNonce is returned when a nonce doesn't match
// markerNoncePattern.
var errInvalidMarkerNonce = errors.New("dotprompt: invalid marker nonce")

// generateMarkerNonce returns a fresh 128-bit nonce as 32 lowercase hex chars.
// Call once per render.
func generateMarkerNonce() string {
	var b [16]byte
	// crypto/rand.Read never returns an error; it crashes the program if the
	// system CSPRNG fails (Go 1.24+).
	_, _ = rand.Read(b[:])
	return hex.EncodeToString(b[:])
}

// validateMarkerNonce checks that nonce is safe to interpolate into a regexp.
func validateMarkerNonce(nonce string) error {
	if !markerNoncePattern.MatchString(nonce) {
		return errInvalidMarkerNonce
	}
	return nil
}

// formatMarker formats a marker with the given nonce and body.
func formatMarker(nonce, body string) (string, error) {
	if err := validateMarkerNonce(nonce); err != nil {
		return "", err
	}
	return "<<<dotprompt:" + nonce + ":" + body + ">>>", nil
}

// roleAndHistoryMarkerRegex matches role and history markers for the given
// nonce. The single capture group is the marker body ("role:user",
// "history").
//
// Only lowercase letters are allowed in role names.
func roleAndHistoryMarkerRegex(nonce string) (*regexp.Regexp, error) {
	if err := validateMarkerNonce(nonce); err != nil {
		return nil, err
	}
	return regexp.MustCompile(`<<<dotprompt:` + nonce + `:(role:[a-z]+|history)>>>`), nil
}

// mediaAndSectionMarkerRegex matches media and section markers for the given
// nonce. The single capture group is the marker body
// ("media:url https://... image/png", "section code").
//
// The body comes from user-controlled values (media url, section name) and
// may contain newlines, so (?s) lets it span lines. Otherwise such a marker
// would fail to match and leak into the output as text, nonce included.
func mediaAndSectionMarkerRegex(nonce string) (*regexp.Regexp, error) {
	if err := validateMarkerNonce(nonce); err != nil {
		return nil, err
	}
	return regexp.MustCompile(`(?s)<<<dotprompt:` + nonce + `:((?:media:url|section) .*?)>>>`), nil
}

// markerPiece is a piece of a rendered string: either literal text or the body
// of a trusted marker.
type markerPiece struct {
	// isMarker is true if value is a marker body, false if it is literal text.
	isMarker bool
	value    string
}

// splitByMarkers splits source on markers matched by re, which must have
// exactly one capture group (the marker body).
//
// Pieces are classified by position rather than content: text lies between
// matches and markers are the matches themselves. This matters because a text
// piece could itself start with something that looks like a marker.
// Whitespace-only text pieces are dropped.
func splitByMarkers(source string, re *regexp.Regexp) []markerPiece {
	var pieces []markerPiece
	appendText := func(s string) {
		if strings.TrimSpace(s) != "" {
			pieces = append(pieces, markerPiece{value: s})
		}
	}

	lastEnd := 0
	for _, m := range re.FindAllStringSubmatchIndex(source, -1) {
		// m[0:2] is the full match, m[2:4] the capture group.
		appendText(source[lastEnd:m[0]])
		pieces = append(pieces, markerPiece{isMarker: true, value: source[m[2]:m[3]]})
		lastEnd = m[1]
	}
	appendText(source[lastEnd:])

	return pieces
}
