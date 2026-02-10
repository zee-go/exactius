# Request Routing

This is currently a single-project setup. If the project expands to manage
multiple ad accounts or child projects, this file will define delegation rules
for spawning sub-agents.

## Current Structure

All work is handled directly in this repository. No sub-agent delegation needed yet.

## Future Multi-Project Pattern

If expanding to multiple ad accounts or separate automation workflows:

1. Create child directories (e.g., `client-a/`, `client-b/`)
2. Each child gets its own `CLAUDE.md` and `docs/active.md`
3. Add `.gitignore` entries for child directories
4. Define routing table here for keyword-based delegation

## Delegation Pattern (when needed)

Follow two-phase delegation:
1. **Phase 1 - Research**: Sub-agent reads child CLAUDE.md, proposes plan
2. **Phase 2 - Execute**: After approval, sub-agent implements (no commits)
3. **Phase 3 - Audit**: Parent reviews diff, user approves, parent commits

For now, handle all work directly in the main session.
