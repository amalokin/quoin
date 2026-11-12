#!/bin/bash
# The codex adversarial-review gate's standing invocation (docs/process.md, Adversarial
# review protocol; the recipe and the gotchas: docs/runbooks/codex-gate.md).
#
#   tools/codex_gate.sh FOCUS_FILE [--scope branch | --base REF] [--cwd DIR]
#   (from a worktree pass --base origin/main, a re-gate --base <sha>: the branch scope reads the local main)
#
# This is a bash script: run it directly, as the usage line shows, never under the
# interpreter of the repository's Python tools.
#
# Runs the codex plugin's companion from the repository root in background mode with the
# focus text read from FOCUS_FILE (a relative path is the caller's, resolved before the
# move to the root); launch it with the harness's background mode and wait for its
# notification. The options and the focus text reach the companion as separate
# arguments, the focus text after --, so a path with a space stays one argument. The
# plugin's versioned path is resolved at run time: $CODEX_PLUGIN when set, else the
# newest ~/.claude/plugins/cache/openai-codex/codex/<version>/. A dash-led token in the
# focus text is refused (handed its arguments as one string, as the plugin's slash
# command hands them, the companion would read it as a flag): its tokenizer splits on
# any whitespace and drops quotes and backslashes, so a dash followed by a letter
# (quotes, backslashes and more dashes between) counts after a line start, any
# whitespace, a quote or a backslash.
set -u
USAGE="usage: tools/codex_gate.sh FOCUS_FILE [--scope branch | --base REF] [--cwd DIR]"
case "${1:-}" in
    "" | -*)
        echo "$USAGE" >&2
        exit 2
        ;;
    /*) FOCUS_FILE="$1" ;;
    *) FOCUS_FILE="$PWD/$1" ;;
esac
shift
if [ ! -f "$FOCUS_FILE" ]; then
    echo "codex_gate: no focus file at $FOCUS_FILE" >&2
    exit 2
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
# JavaScript's whitespace beyond ASCII (U+00A0, U+1680, U+2000-U+200A, U+2028, U+2029,
# U+202F, U+205F, U+3000, U+FEFF) as UTF-8, so that grep under LC_ALL=C matches it too
WIDE=$'\xc2\xa0|\xe1\x9a\x80|\xe2\x80\x80|\xe2\x80\x81|\xe2\x80\x82|\xe2\x80\x83'
WIDE+=$'|\xe2\x80\x84|\xe2\x80\x85|\xe2\x80\x86|\xe2\x80\x87|\xe2\x80\x88|\xe2\x80\x89'
WIDE+=$'|\xe2\x80\x8a|\xe2\x80\xa8|\xe2\x80\xa9|\xe2\x80\xaf|\xe2\x81\x9f|\xe3\x80\x80'
WIDE+=$'|\xef\xbb\xbf'
DASH_LED="(^|[[:space:]\"']|\\\\|$WIDE)-([-\"']|\\\\)*[A-Za-z]"
LC_ALL=C grep -n -o -E "$DASH_LED" "$FOCUS_FILE"
case $? in
    0)
        echo "codex_gate: dash-led tokens in the focus text (above); spell them out" >&2
        exit 2
        ;;
    1) ;;
    *)
        echo "codex_gate: cannot read the focus file $FOCUS_FILE" >&2
        exit 2
        ;;
esac
PLUGIN="${CODEX_PLUGIN:-}"
if [ -z "$PLUGIN" ]; then
    PLUGIN="$(ls -d "$HOME"/.claude/plugins/cache/openai-codex/codex/*/ 2>/dev/null | sort -V | tail -n 1)"
fi
if [ -z "$PLUGIN" ] || [ ! -f "$PLUGIN/scripts/codex-companion.mjs" ]; then
    echo "codex_gate: no codex plugin found; set CODEX_PLUGIN to its directory" >&2
    exit 2
fi
FOCUS="$(cat "$FOCUS_FILE")"
echo "codex_gate: $PLUGIN from $ROOT with: $*" >&2
exec node "$PLUGIN/scripts/codex-companion.mjs" adversarial-review --background "$@" -- "$FOCUS"
