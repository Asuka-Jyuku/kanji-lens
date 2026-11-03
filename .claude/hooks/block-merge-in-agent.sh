#!/usr/bin/env bash
# =====================================================================
# PreToolUse (Bash) hook for the project's agents (.claude/agents/):
# blocks what an agent never does on its own, because it needs an
# explicit "go ahead" from whoever asked, given for that PR:
#   - gh pr merge;
#   - git push with --force, -f or --force-with-lease.
# Everything else ("don't commit unless asked") depends on the request,
# which the hook does not read: it stays in the agent's text.
#
# Exits with 2 to block: the stderr text goes back to the agent
# (Claude Code docs: hooks, PreToolUse). It checks the whole input JSON,
# without jq: a "gh pr merge" inside an echo is also blocked, on purpose.
# =====================================================================
input="$(cat 2>/dev/null || true)"

if grep -Eq 'gh[[:space:]]+pr[[:space:]]+merge' <<<"$input"; then
    echo "Blocked by the agent hook: merging a PR needs a \"go ahead\" from whoever asked, for that PR. Open the PR, watch CI and return the link." >&2
    exit 2
fi
if grep -Eq 'git[[:space:]]+push[^|;&]*([[:space:]]-f([[:space:]"]|$)|--force)' <<<"$input"; then
    echo "Blocked by the agent hook: a forced git push rewrites someone else's history. Ask whoever called you." >&2
    exit 2
fi
exit 0
