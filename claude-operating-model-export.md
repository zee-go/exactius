# Claude Code Operating Model — Anonymized Reference Export

> **What this is**: A complete export of the operating model used to run a multi-project software engineering workspace with Claude Code (Anthropic's CLI agent). This covers persistent memory, task tracking, multi-project orchestration, sub-agent delegation, credential management, and session protocols.
>
> **Anonymized**: All names, emails, IPs, API keys, GIDs, URLs, and project-specific details have been replaced with placeholders. The structure, patterns, and conventions are fully preserved.

---

## Table of Contents

1. [File Structure Overview](#1-file-structure-overview)
2. [Main Index — CLAUDE.md](#2-main-index--claudemd)
3. [Rules](#3-rules)
   - 3a. [Session Start Protocol](#3a-session-start-protocol)
   - 3b. [Request Routing & Delegation](#3b-request-routing--delegation)
   - 3c. [Cross-Project Context](#3c-cross-project-context)
4. [Persistent Memory (Auto-Memory)](#4-persistent-memory-auto-memory)
5. [Session Memory — Task Tracker](#5-session-memory--task-tracker)
6. [Session Memory — Decision Log](#6-session-memory--decision-log)
7. [Reference Documents (On-Demand)](#7-reference-documents-on-demand)
   - 7a. [Project Registry](#7a-project-registry)
   - 7b. [CLAUDE.md Standard for Child Projects](#7b-claudemd-standard-for-child-projects)
   - 7c. [MCP Server Inventory](#7c-mcp-server-inventory)
   - 7d. [External Service Reference](#7d-external-service-reference)
   - 7e. [Operating Model Meta-Doc](#7e-operating-model-meta-doc)
   - 7f. [Business Context (Memory Doc)](#7f-business-context-memory-doc)
8. [Permission Settings](#8-permission-settings)
9. [Domain-Specific Memory Files](#9-domain-specific-memory-files)
10. [Design Principles](#10-design-principles)

---

## 1. File Structure Overview

```
workspace/                              # Parent orchestrator repo
├── .claude/
│   ├── CLAUDE.md                       # Main index (auto-loaded every session)
│   ├── settings.json                   # Project-level permissions
│   ├── settings.local.json             # Local permission overrides
│   └── rules/
│       ├── session-start.md            # Session start protocol (auto-loaded)
│       ├── routing.md                  # Sub-agent delegation rules (auto-loaded)
│       └── cross-project.md            # Cross-project conventions (auto-loaded)
├── docs/
│   ├── active.md                       # Task tracker (read every session)
│   ├── decisions.md                    # Append-only decision log
│   ├── memory.md                       # Business context (synced from external doc)
│   ├── projects.md                     # Full project registry
│   ├── claude-md-standard.md           # Child project CLAUDE.md template
│   ├── mcp-servers.md                  # MCP server inventory
│   ├── service-reference.md            # External service API reference
│   └── operating-model.md             # Meta-doc about this system
├── scripts/
│   ├── setup-subprojects.sh            # Clone child repos
│   └── setup-mcp.sh                    # Install MCP servers + wrappers
├── child-project-alpha/                # Child project (own git, .gitignored)
│   ├── CLAUDE.md                       # Project-specific context
│   └── docs/
│       ├── active.md
│       └── decisions.md
├── child-project-beta/                 # Another child project
│   ├── CLAUDE.md
│   └── docs/
│       ├── active.md
│       └── decisions.md
└── ...

~/.claude/
├── settings.json                       # Global user permissions
├── settings.local.json                 # Local global overrides
└── projects/
    └── <project-hash>/
        └── memory/
            ├── MEMORY.md               # Auto-loaded persistent memory
            ├── topic-a-conventions.md  # Domain-specific memory
            └── topic-b-patterns.md     # Domain-specific memory
```

### Three-Tier Context Loading

| Tier | When Loaded | Files | Purpose |
|------|-------------|-------|---------|
| **1. Auto-loaded** | Every session, automatically | `.claude/CLAUDE.md`, `.claude/rules/*`, `memory/MEMORY.md` | Core operating context (~350 lines total) |
| **2. Session start** | First substantive interaction | `docs/active.md` | Surface due/overdue tasks |
| **3. On-demand** | When relevant to current task | `docs/memory.md`, `docs/decisions.md`, `docs/projects.md`, etc. | Deep context loaded selectively |

---

## 2. Main Index — CLAUDE.md

> Location: `.claude/CLAUDE.md` (auto-loaded every session)
>
> Principle: **Lean index, not a knowledge base.** Max 3 lines per topic. Heavy docs go in `docs/`. This file is loaded into every session's context, so bloat directly increases token cost and dilutes attention.

```markdown
# Project Name — Subtitle Description

Brief description of what this workspace does. Personal assistant + orchestrator
for engineering projects across multiple repositories.

## Project Registry

| Project | Directory | GitHub | Cloud Project |
|---|---|---|---|
| Orchestrator | (this repo) | owner/orchestrator | project-id-001 |
| Alpha Service | child-alpha/ | org/alpha-service | project-id-002 |
| Beta API | child-beta/ | org/beta-api | project-id-003 |
| Gamma Dashboard | child-gamma/ | org/gamma-dash | project-id-004 |

Full details: `docs/projects.md`

## Delegation

When a request targets a specific project, spawn a Task sub-agent and explicitly
instruct it to read the child's CLAUDE.md first (sub-agents do NOT auto-load
child CLAUDE.md). See `.claude/rules/routing.md` for the prompt template and
routing table.

- **Single-project work**: Delegate to sub-agent, prefix paths with child directory
- **Cross-project work**: Coordinate from here, spawn multiple sub-agents
- **General / this codebase**: Handle directly
- **High-risk ops** (deploys, data migrations): Handle in main session for visibility

## Git Isolation

Git commands from this directory affect the PARENT repo only. Sub-agents in child
directories use the child's git. Each child is .gitignored from the parent. Never
run `git add .` from this directory.

- **This repo**: Push to origin after each commit (personal config repo, no CI risk)
- **Child repos**: Always confirm before pushing (team contributors, CI pipelines)

## Architecture

- **Runtime**: Python 3.12 + FastAPI on Cloud Run
- **LLM**: Claude API (Sonnet primary, Opus for complex tasks)
- **Persistence**: Firestore
- **Accounts**: work@company.com (delegation) + personal@domain.com (OAuth)

```
src/
  main.py              # FastAPI app entry point
  config.py            # Pydantic settings
  system_prompt.py     # Agent system prompt
  types.py             # Core type definitions
  agent/               # Reasoning engine, tool registry, approval gate
  gateway/             # Webhook handler, JWT auth
  tools/               # External service integrations
  persistence/         # Database client
```

## Key Patterns

- **Agentic loop**: Runs Claude in a tool-use loop (max 25 turns)
- **Action tiers**: read_only (auto) > low_risk_write (auto+log) > high_risk_write (approval card)
- **Tool registry**: Tools self-register with JSON Schema; registry exports to API format
- **Dual-account**: All tools support `account="work"` or `account="personal"`

## Shorthand Commands

- **dcp** = Document, commit, and push this repo. Update session docs (active.md,
  decisions.md), commit changes, push to origin.
- **dcp <project>** = DCP scoped to a single child repo. Uses child's git.
- **dcp everything** = DCP parent + all child repos with uncommitted changes.

## Session Memory

Uses `docs/active.md` (task tracker) + `docs/decisions.md` (decision log).
Same format as all child projects. See `.claude/rules/session-start.md`.

## Reference Documents (on-demand)

- `docs/active.md` — task tracker (read every session)
- `docs/decisions.md` — append-only decision log
- `docs/projects.md` — project registry with full details
- `docs/memory.md` — persistent context (synced from external doc)
- `docs/mcp-servers.md` — MCP server configuration reference
- `docs/service-reference.md` — cross-project service GIDs and API patterns
- `docs/claude-md-standard.md` — child project CLAUDE.md template

## MCP Server Setup

MCP servers configured globally via `claude mcp add`, stored in `~/.claude.json`.
Credentials pulled from Secret Manager at runtime. Full setup: `docs/mcp-servers.md`

## External Service API Access

- **Token**: `service-bot-token` in Secret Manager project `project-id-001`
- **Retrieve**: `gcloud secrets versions access latest --secret=service-bot-token --project=project-id-001`
- Do NOT use personal tokens for automated operations
- See auto memory for API details

## Infrastructure Gateway Access

Authenticated API proxy to home/lab infrastructure via Tailscale bridge.

- **URL**: `http://<gateway-ip>:<port>`
- **Auth header**: `X-Gateway-Key: <key>`
- **Endpoints**: Various service proxies + SSH command execution

## Guardrails

- IMPORTANT: Verify before irreversible actions (sending emails, publishing, deleting)
- IMPORTANT: Never send communications to external parties without explicit approval
- Ask for clarification when business context is ambiguous
- Never delete or overwrite important data without confirmation
- Never make assumptions about business decisions — ask when uncertain
- **Approval expiry**: High-risk approvals lapse after 60 minutes. Re-confirm if delayed.
- **Quality gates**: Autonomous pipelines must define measurable pass/fail criteria.
```

---

## 3. Rules

### 3a. Session Start Protocol

> Location: `.claude/rules/session-start.md` (auto-loaded)

```markdown
# Session Start Protocol

IMPORTANT: At the start of every conversation, read `docs/active.md` before
responding to the user's first message. Surface any items due or overdue based
on today's date. If nothing is due, proceed normally — no need to announce
"nothing overdue."

This applies to the first substantive interaction, not quick factual questions.
If the user opens with something like "what time is it?" or "convert 500 USD
to EUR", answer that directly. But if the first message involves project work,
planning, or is open-ended, read active.md first.

## Deep Context (on-demand)

These files are NOT read automatically — load them when relevant:

- `docs/memory.md` — full personal + business context. Read when you need
  background on the user, company, team, strategy, or preferences beyond
  what's in auto-memory.
- `docs/decisions.md` — append-only decision log. Read when you need to
  understand why a past decision was made, or before making a decision that
  might contradict an earlier one.
- `docs/projects.md` — detailed project registry. Read when you need full
  project details beyond the summary table in CLAUDE.md.
```

### 3b. Request Routing & Delegation

> Location: `.claude/rules/routing.md` (auto-loaded)

```markdown
# Request Routing

When the user's request targets a specific project, delegate to a sub-agent via
the Task tool. Sub-agents do NOT automatically pick up child CLAUDE.md files —
you must explicitly inject context.

## Delegation Mode: Two-Phase

All sub-agent delegation uses a two-phase pattern: research first, execute only
after parent approval.

### Phase 1 — Research & Propose (no edits)

```
You are working on the {PROJECT_NAME} project in the `{DIRECTORY}/` directory.

FIRST: Read `{DIRECTORY}/CLAUDE.md` and follow its instructions as your project
context. Also read `{DIRECTORY}/docs/active.md` for current task context (if it
exists). All file paths should be relative to `{DIRECTORY}/`. Use
`git -C {DIRECTORY}` for all git commands.

TASK: {actual task here}

IMPORTANT: This is a research-only phase. Do NOT edit, create, or delete any
files. Do NOT run any commands that modify state. Only read files, search code,
and investigate.

Report back:
- What you found
- What files would need to change (and why)
- A proposed plan of changes
```

### Phase 2 — Execute (after parent approval)

Only spawn this after the user has reviewed and approved the Phase 1 proposal.

```
You are working on the {PROJECT_NAME} project in the `{DIRECTORY}/` directory.

FIRST: Read `{DIRECTORY}/CLAUDE.md` and follow its instructions. Also read
`{DIRECTORY}/docs/active.md`. All file paths relative to `{DIRECTORY}/`.
Use `git -C {DIRECTORY}` for all git commands.

TASK: Execute the following approved changes:
{approved plan}

Do NOT commit changes — leave them as uncommitted modifications for review.
Report what files you changed and what commands you ran.
```

### Phase 3 — Audit (parent runs after execution)

After Phase 2 completes, the parent session runs `git -C {DIRECTORY} diff --stat`
and `git -C {DIRECTORY} status` to produce a change summary for the user. No
commits or pushes without explicit user approval.

**Parent active.md sync**: If the completed work corresponds to an item tracked
in the parent's `docs/active.md`, move it to Completed.

## Routing Table

| Keywords / Topics | Target Directory |
|---|---|
| Alpha, sprint management, team tasks | child-alpha/ |
| Beta, billing, clients, invoices | child-beta/ |
| Gamma, dashboard, UI, analytics | child-gamma/ |
| Orchestrator, this codebase | Handle directly (this repo) |

## Phase 2 Alternative: Autonomous Agent Loop

For approved plans with 3+ discrete implementation steps, an autonomous agent
loop can replace the standard Phase 2 sub-agent. The loop spawns fresh Claude
instances in sequence, each implementing one user story from a structured JSON
spec, committing, and passing learnings forward.

**When to use:**
- Approved plan has 3+ sequential, well-defined implementation steps
- Work is scoped to a single repo/branch
- Each step fits in one context window
- You want unattended execution

**When NOT to use:**
- Investigative or diagnostic work
- Cross-project coordination
- Changes requiring human judgment mid-stream
- Small changes (1-2 steps) — standard Phase 2 is simpler

## Rules

- **Two-phase by default**: All delegated work goes through research → approve →
  execute → audit. No exceptions unless the user explicitly says otherwise.
- **Read-only tasks are single-phase**: Pure information gathering can skip Phase 2.
- **Ambiguous requests**: Ask the user which project they mean.
- **Cross-project requests**: Coordinate from here, spawn multiple sub-agents.
- **No commits without approval**: Sub-agents never commit. Parent shows diff, user
  approves, then parent commits.
- **High-risk operations** (deploys, data migrations): Handle in main session.
```

### 3c. Cross-Project Context

> Location: `.claude/rules/cross-project.md` (auto-loaded)

```markdown
# Cross-Project Context

Shared context that applies across multiple child projects.

## Credentials Reference

Each project has its own cloud project and Secret Manager. Don't duplicate
credential values — just reference where they live.

| Secret | Cloud Project | Used By |
|---|---|---|
| api-key | project-id-002 | Alpha Service |
| service-token | project-id-001 | Orchestrator, CLI |
| admin-sa-key | project-id-002 | Alpha Admin SDK |
| billing-api-id | project-id-001 | Billing API |
| billing-api-secret | project-id-001 | Billing API |

## Conventions

- **Commit style**: Structured messages with context. Co-author tag when Claude
  commits.
- **Session memory**: All projects use `docs/active.md` + `docs/decisions.md`
  pattern. Read active.md at session start, update both at session end.
- **CLAUDE.md philosophy**: Lean index, not a knowledge base. Max 3 lines per
  topic. Heavy docs go in `docs/`.
- **Deployment rule**: Always ask before deploying.
- **Action tiers**: read_only (auto) > low_risk_write (auto+log) >
  high_risk_write (approval required)
- **Cloud project isolation**: Each child project owns its own cloud project.
  No sharing infrastructure across projects.

## Cloud CLI Safety

Multiple child projects use different cloud projects. The CLI has a single
global active config that all processes share. Concurrent sub-agents can
cross-contaminate if they mutate this state.

**Rules:**

1. **Always pass `--project=<id>` on every CLI command.** No exceptions. Never
   rely on the active config.
2. **Always pass `--account=<email>` on every CLI command** targeting the correct
   org. The default account may differ.
3. **Never run `config set project` or `config set account` in sub-agents.** This
   mutates global state and affects all other processes.
4. **Each child CLAUDE.md must declare its cloud project ID.**

## Git Operations

- Git commands from the parent directory affect the PARENT repo only
- Sub-agents working in child directories use the CHILD repo's git automatically
- Never run `git add .` from the parent directory
- Each child pushes to its own remote independently
```

---

## 4. Persistent Memory (Auto-Memory)

> Location: `~/.claude/projects/<project-hash>/memory/MEMORY.md` (auto-loaded every session)
>
> This file is injected into the system prompt at the start of every session. It persists across conversations and is editable by Claude itself. Keep it concise — lines after 200 are truncated.

```markdown
# Auto Memory

## User — Essentials
- **Name**: [User Name]
- **Based**: [City, Country]
- **Businesses**: [Company A] (role), [Company B] (role)
- **Company A**: Brief description, ~revenue, ~staff count. Focus area.
- **CEO**: [Name] — runs day-to-day operations
- **Exec team**: [Name] (Finance), [Name] (People), [Name] (Growth)
- **Personality**: [MBTI], [DISC]. Neurodivergent traits. Key interests.

## Communication Preferences
- Concise, bullet-based responses. No emojis or filler.
- Direct, blunt communication — no soft asks or conversational transitions
- Single-step solutions preferred over multi-step workflows
- Accuracy critical for tax/finance numbers
- When presenting options, include a recommendation
- Default to practical over perfect
- **Currency**: Always quote prices in preferred currency. Convert if needed.

## Infrastructure
- **Cloud region preference**: [region] — closest to user
- **Home server IP**: [Tailscale IP] (secret ref: `server-ip` in project `X`)
- **Gateway**: Deployed at `http://<ip>:<port>` (project, zone). Proxies
  services + SSH. Auth: header-based.

## Orchestration Lessons
- Sub-agents spawned via Task tool inherit parent's permission mode
- Two-phase delegation is an instruction-level guardrail, not a technical gate
- Sub-agents do NOT auto-load child CLAUDE.md — must explicitly inject via
  prompt template
- Read-only delegations work well as single-phase

## DCP (Document-Commit-Push) Conventions
- After a DCP, suggest `/clear` if: context is long/compacted, multiple
  sub-agents were spawned, or it's a natural topic breakpoint.
- Deployment check: If the DCP'd project has a deployable service, check for
  uncommitted code that differs from last deploy. Ask user if they want to deploy.

## Background Agent Lessons
- `run_in_background` agents: completion notifications don't always surface.
  Workaround: use `Task resume` with agent ID to pull results.
- Check agent status proactively with `TaskOutput` rather than waiting.

## Domain-Specific Lessons
- [Category]: [Key lesson learned]. [Workaround or fix].
- [Category]: [Another lesson]. [Pattern to follow].
- See `memory/topic-a.md` for full patterns.
- See `memory/topic-b.md` for troubleshooting guide.

## External Service Conventions
- **Work logs go in comments** (stories API), not task descriptions.
  See `memory/service-conventions.md` for full API patterns.
- **Never use built-in MCP tools for writes** — they authenticate as personal
  account. Use curl + service token for all create/update operations.
  MCP tools OK for read-only lookups.
```

### How Auto-Memory Works

- `MEMORY.md` is always loaded into the system prompt (truncated at 200 lines)
- Create separate topic files (e.g., `debugging.md`, `patterns.md`) for detailed notes
- Link to topic files from MEMORY.md
- Record insights about problem constraints, strategies that worked/failed, and lessons learned
- Update or remove memories that turn out to be wrong or outdated
- Organize semantically by topic, not chronologically
- Claude itself reads and writes these files using the Edit/Write tools

---

## 5. Session Memory — Task Tracker

> Location: `docs/active.md` (read at start of every session per session-start protocol)
>
> This is the source of truth for what's in-flight, what needs checking, and what's coming up.

```markdown
# Active Tasks & Reminders

> This file is the source of truth for what's in-flight, what needs checking,
> and what's coming up. Claude reads this at the start of every session and
> surfaces anything due or overdue. Update at the end of every session.

---

## In Progress

- **[TBD] Feature X implementation** — Description of current state. What's been
  done, what's remaining. Next: specific next step.
- **[TBD] Service Y deployment** — Code complete (version, commit ref). Needs:
  credentials, config, deploy command. See `child-project/docs/active.md`.
- **[TBD] Infrastructure improvement Z** — N improvements identified and
  documented in `child-project/docs/improvement-plan.md`. Top 3 priorities
  listed. Next: create PRD and run via autonomous loop.

## Pending Review

- **[2026-03-15] Config change — verify fix** — Description of what was deployed
  and what to verify. Root cause explanation. If still broken: fallback plan.
- **[2026-03-20] Cloud cleanup — verify completion** — What was initiated and
  what the recovery window is. Linked task reference.

## Scheduled Checks

- **[2026-06-01] External doc sync** — Re-sync `docs/memory.md` from source
  documents. Last synced date.
- **[2026-04-01] MCP server health check** — Verify all global MCP servers are
  functional. Check for stale references.

## Completed (Recent)

- ~~[2026-03-10] Feature A delivered~~ — Summary of what was done, key decisions,
  files changed, commits. Enough context to understand the work without re-reading
  the code.
- ~~[2026-03-09] Bug fix B~~ — What was broken, root cause, fix applied.

---

## How This File Works

**Sections:**
- **In Progress** — actively being worked on across sessions
- **Pending Review** — done but needs verification after a time delay
  (date = when to check)
- **Scheduled Checks** — recurring or future reviews (date = when due)
- **Completed (Recent)** — finished items, kept for ~30 days then removed

**Rules:**
- Dates in brackets are due dates, not start dates
- Move items down as they progress: In Progress -> Pending Review -> Completed
- Remove completed items older than 30 days (they're in git history)
- If an item spawns new work, add the new item and complete the original
```

---

## 6. Session Memory — Decision Log

> Location: `docs/decisions.md` (on-demand, append-only, reverse-chronological)
>
> Captures the "why" so future sessions don't re-litigate settled questions.

```markdown
# Decision Log

> Reverse-chronological record of significant decisions. Captures the "why" so
> future sessions don't re-litigate settled questions.
> Append new entries at the top.

## 2026-03-10 — Feature X: chose approach A over approach B

- **Decided**: Used library A with pattern X instead of library B with pattern Y.
- **Why**: Library A has better TypeScript support, smaller bundle size, and the
  team already uses it in two other projects. Library B would require a new
  dependency and has a less active maintainer.
- **See**: `docs/feature-x-architecture.md`

## 2026-03-09 — Infrastructure: plain HTTP over TLS for internal gateway

- **Decided**: Use plain HTTP + firewall rules instead of TLS for the internal
  API gateway.
- **Why**: This is personal infrastructure behind an API key on a private network.
  TLS adds certificate management overhead for zero security benefit (traffic
  never leaves the private network). Firewall rules restrict access to known IPs.

## 2026-03-08 — Cloud project naming: always use auto-generated IDs

- **Decided**: When creating cloud projects, let the provider auto-generate the
  project ID with random numbers. Never append descriptive suffixes.
- **Why**: User prefers the auto-generated pattern (e.g., `project-484513`).
  Short slugs are often globally taken anyway. Auto-generated IDs are unique
  and consistent with existing convention.
```

### When to Log

- Choosing between alternatives
- Changing an existing approach
- Establishing a new convention

### When NOT to Log

- Routine bug fixes
- Config tweaks
- Self-evident changes

---

## 7. Reference Documents (On-Demand)

These files are NOT auto-loaded. They're read only when the current task requires their context.

### 7a. Project Registry

> Location: `docs/projects.md`

```markdown
# Project Registry

> Master reference for all projects managed from this orchestrator workspace.

## Active Projects

| Project | Directory | GitHub Repo | Cloud Project | Purpose | Status |
|---|---|---|---|---|---|
| Orchestrator | (this repo) | owner/orchestrator | project-001 | Assistant + orchestrator | Active |
| Alpha | child-alpha/ | org/alpha | project-002 | Service management | Active |
| Beta | child-beta/ | org/beta | project-003 | Billing MCP server | Active |
| Gamma | child-gamma/ | owner/gamma | project-004 | Dashboard + analytics | Active |

## Cloud Project Map

| Cloud Project ID | Purpose | Region(s) | Key Services |
|---|---|---|---|
| `project-001` | Orchestrator | europe-west | Cloud Run, Firestore, Secret Manager |
| `project-002` | Alpha | us-east | Cloud Run, Cloud SQL, Secret Manager |
| `project-003` | Beta | us-central | Cloud Run (Node.js), Secret Manager |
| `project-004` | Gamma | asia-southeast | Cloud Run, Cloud SQL, Artifact Registry |

## Onboarding Checklist

To add a new project:
1. Clone repo into this directory: `git clone <url>`
2. Add directory name to `.gitignore`
3. Add entry to the table above
4. Ensure child has `CLAUDE.md` at the project root
5. Add routing rule to `.claude/rules/routing.md`
6. Verify git isolation: `git status` from parent should not show child files
```

### 7b. CLAUDE.md Standard for Child Projects

> Location: `docs/claude-md-standard.md`

```markdown
# Child Project CLAUDE.md Standard

Convention guide for all child project CLAUDE.md files.

## Principles

- **Project-specific only** — orchestration, session protocols, and generic
  guardrails live in the parent. Child files contain only what's unique.
- **Lean index** — max 3 lines per topic. Heavy docs go in `docs/`.
- **Canonical name** — the `# Title` line is the project's canonical name.
- **Location** — `CLAUDE.md` at the project root (not `.claude/CLAUDE.md`).

## Standard Section Order

1. `# Project Name` — canonical name (not "CLAUDE.md - Project")
2. `## Purpose` — 1-3 lines
3. `## Tech Stack` — runtime, framework, language, deployment target
4. `## Commands` — build, test, dev, deploy
5. `## Project Structure` — directory layout
6. `## Architecture` (optional) — system diagrams, data flow
7. `## Key Patterns` (optional) — important non-obvious conventions
8. `## Environment Variables` — required and optional env vars
9. Project-specific sections — integrations, APIs, team, deployment
   9a. `## Hardcoded Constants` (recommended) — values that break if external
       config changes
10. `## Gotchas` — edge cases, common pitfalls, project-specific safety rules
11. `## Reference Docs` (always last) — points to session memory files

## What does NOT belong in child CLAUDE.md

These live in the parent orchestrator:
- Deployment approval rules
- Session protocols (read active.md at start)
- Communication preferences
- Shorthand commands (dcp)
- Generic guardrails
- Documentation update rules

## Mass Update Procedure

1. Update this standard doc if the convention is changing
2. Use parent orchestrator to spawn sub-agents for each child
3. Each sub-agent reads child CLAUDE.md and applies changes
4. Parent audits diffs before committing
5. Commit each child repo independently
6. Push after user approval
```

### 7c. MCP Server Inventory

> Location: `docs/mcp-servers.md`

```markdown
# MCP Servers

All MCP servers configured globally via `claude mcp add`.
Stored in `~/.claude.json`. Single source of truth.

## Server Inventory

### Zero-install (npx / remote)

| Server | Package / URL | What it does | Auth |
|--------|---------------|-------------|------|
| **doc-editor** | `npx @some/doc-mcp` | Docs, Sheets, Drive | OAuth |
| **video** | `npx yt-mcp` | Video search, transcripts | None |
| **cms** | `npx @some/cms-mcp` | CMS management | OAuth |
| **billing** | `mcp-remote` → `https://...` | Billing, clients | OAuth |
| **project-mgmt** | HTTP → `https://...` | Tasks, projects | Service token |

### Require per-machine setup

| Server | Package | Install | Credentials |
|--------|---------|---------|-------------|
| **analytics** | `analytics-mcp` | `pipx install ...` | ADC |
| **workspace** | `workspace-mcp` | `uv tool install ...` | Secret Manager |
| **seo** | HTTP remote | Helper script | Secret Manager |

## New Machine Setup

```bash
# 1. Prerequisites
brew install node python pipx uv
brew install --cask google-cloud-sdk
gcloud auth login user@company.com
gcloud auth application-default login --scopes="..."

# 2. Clone and run setup
git clone https://github.com/owner/orchestrator.git
cd orchestrator
./scripts/setup-subprojects.sh   # clone child repos
./scripts/setup-mcp.sh           # install packages, create wrappers, register
```

## Architecture Notes

- **Credential pattern**: No secrets in config files. Wrapper scripts pull from
  Secret Manager at runtime.
- **Portability**: Run `scripts/setup-mcp.sh` on any new machine. All wrappers
  use `$HOME` (no hardcoded paths).
- **Source of truth**: The setup script generates wrapper scripts — don't edit
  `~/.local/bin/` scripts directly, update setup-mcp.sh and re-run.
```

### 7d. External Service Reference

> Location: `docs/service-reference.md` (e.g., Asana, JIRA, or whatever PM tool)

```markdown
# External Service Cross-Project Reference

> Centralized config for external services used across projects.

## Workspace / Organization

- **Org ID**: `<workspace-gid>`

## Projects by Child Repo

| Service Project | ID | Used By | Purpose |
|---|---|---|---|
| Sprint Board | `<project-gid>` | Alpha, Orchestrator | Sprint management |
| Engineering | `<project-gid>` | Alpha | Engineering board |
| Content | `<project-gid>` | Beta | Content tracking |

## Authentication by Project

| Project | Token Type | Storage | Notes |
|---|---|---|---|
| Orchestrator | Service token (bot) | Secret Manager | Use for automated ops |
| Alpha | Personal access token | Secret Manager | Legacy |
| Beta | Personal access token | `.env` | Extract with grep |
| Gamma | OAuth (company-wide) | Database | Auto-refresh, per-user |

## API Gotchas

- **Pagination**: Max 100 items/request. Use cursor/offset.
- **Rate limiting**: 300ms delay between writes.
- **Date format**: JSON object `{"date": "YYYY-MM-DD"}`, not bare string.
- **Subtask projects**: Subtasks don't inherit parent's project — add explicitly.
```

### 7e. Operating Model Meta-Doc

> Location: `docs/operating-model.md`

```markdown
# Claude Agent Operating Model

## Overview

A lightweight persistent memory system that gives Claude continuity across
sessions without relying on conversation history. Three files act as a shared
brain between sessions, enabling any Claude instance to pick up where the last
one left off.

## Architecture

| File | Purpose | Update Frequency |
|---|---|---|
| `docs/active.md` | Task tracker — in-flight, needs checking, done | Every session |
| `docs/decisions.md` | Decision log — what and why (append-only) | When decisions are made |
| `docs/memory.md` | User profile and business context | Monthly |

## Task Tracker (`active.md`)

Four sections that items flow through:

1. **In Progress** — actively being worked on across sessions
2. **Pending Review** — done but needs verification after a delay (date = check)
3. **Scheduled Checks** — recurring or future reviews (date = when due)
4. **Completed (Recent)** — finished items, kept ~30 days then pruned

## Decision Log (`decisions.md`)

Append-only, reverse-chronological. Each entry has:
- **Decided** — what was chosen
- **Why** — rationale, tradeoffs, context
- **See** — link to related doc (optional)

## Memory (`memory.md`)

One-way sync from an external document. Contains persistent context: identity,
business operations, strategy, preferences. The external doc is the source of
truth — the local copy is for Claude's context window.

## Session Protocol

1. **Start**: Read `active.md` — surface anything due or overdue today
2. **During**: Update `active.md` as tasks progress; log decisions as they're made
3. **End**: Ensure both files reflect what happened
4. **External work**: If user mentions work done outside Claude, log it

## Why This Exists

This workspace handles diverse tasks across sessions spanning weeks. Without
persistent memory, each session starts cold and risks re-litigating settled
decisions or losing track of open work.

- `active.md` = **what** (current state)
- `decisions.md` = **why** (rationale archive)

This pattern is standardised across multiple projects so any Claude session
in any workspace follows the same conventions.
```

### 7f. Business Context (Memory Doc)

> Location: `docs/memory.md` (on-demand, synced from external document)

This is a one-way sync from an external document (e.g., Google Doc). It contains comprehensive business and personal context: company operations, team details, strategy, audience data, technology stack, content guidelines, tax planning, etc. Typically 500-700 lines.

The auto-memory (`MEMORY.md`) contains essential highlights. The full memory doc is loaded only when deep context is needed.

---

## 8. Permission Settings

> Location: `.claude/settings.json` (project-level)

```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  },
  "respectGitignore": true
}
```

The permission system has three levels:
- **Global**: `~/.claude/settings.json` — user-wide defaults
- **Project**: `.claude/settings.json` — project-level overrides
- **Local**: `.claude/settings.local.json` — machine-specific (gitignored)

Permission modes:
- `"ask"` — ask before every tool use
- `"acceptEdits"` — auto-accept file edits, ask for bash commands
- `"bypassPermissions"` — auto-accept everything (requires explicit opt-in)

---

## 9. Domain-Specific Memory Files

> Location: `~/.claude/projects/<project-hash>/memory/`

These are separate files linked from `MEMORY.md` for detailed domain knowledge that doesn't fit in the 200-line auto-memory limit.

### Example: External Service Conventions (`memory/service-conventions.md`)

```markdown
# Service Conventions

## Work Logs vs Descriptions

- **Descriptions** are the static task spec. Don't write work logs here.
- **Work logs go in comments** via POST /tasks/{id}/stories.
- Format: date header + bullet list + commit refs.

## Time Entries

- **Create**: POST /tasks/{id}/time_tracking_entries with duration + date
- **Query**: GET /tasks/{id}/time_tracking_entries
- Always check existing entries before adding to avoid duplicates.

## Authentication

- **Token**: `service-bot-token` in Secret Manager `project-001`
- Retrieve fresh each session
- Do NOT use personal token for automated operations
- Built-in MCP tools OK for read-only, curl + bot token for writes

## API Patterns

- **Pagination**: Max 100/request. Use `offset` from `next_page`.
- **Rate limiting**: 300ms delay between writes.
- **Search**: GET /workspaces/{id}/tasks/search with query params.

## Multi-Source Synthesis Pattern

When a task needs comprehensive review, pull from multiple sources in parallel:

1. **Task tree**: Get task + subtasks + sub-subtasks via REST API
2. **Linked docs**: Subtask notes often contain doc links. Fetch content.
3. **Meeting transcripts**: Search MCP for related discussions. If recent,
   fall back to Drive search for notes.
4. **Synthesise and post**: Compile into structured comment via bot token.
```

### Example: Infrastructure Troubleshooting (`memory/infra-patterns.md`)

```markdown
# Infrastructure Troubleshooting Patterns

## How to Detect Broken Items

Query all items and flag anomalous ratios:

```python
# API: GET /library/sections/{id}/all with auth header
# Flag: unexpected ratios or counts that indicate mismatched data
```

Common symptom: non-standard naming causes incorrect categorization.

## Known Naming Issues

### Pattern: Non-standard format (parsed incorrectly)
- **Example**: `S1.Ep.02.Title.mp4`
- **System reads as**: Season 2, Episode 2 (wrong)
- **Fix**: Rename to standard `S01E02` format

### Pattern: Wrong external ID match
- **Example**: Files from "Show A (2014)" matched to "Show A (1980)"
- **Fix**: Delete wrong entry (preserve files), add correct match, rescan

## Fix Procedure

1. **Identify**: Query for items with suspicious data
2. **Diagnose**: Check file paths and metadata
3. **Rename**: Move files to standard naming format
4. **Re-map**: If external ID is wrong, fix the mapping
5. **Scan**: Trigger library refresh
6. **Verify**: Re-query to confirm
```

---

## 10. Design Principles

### CLAUDE.md as Lean Index
- Max 3 lines per topic in CLAUDE.md
- Detailed docs go in `docs/` and are referenced by path
- CLAUDE.md is loaded every session — bloat = higher cost + diluted attention
- Rule of thumb: if content is only relevant to a specific workflow, it belongs in its own file

### Session Memory Pattern
- **active.md** = current state (what)
- **decisions.md** = rationale archive (why)
- **memory.md** = persistent context (who/what/where)
- Standardised across all projects — any Claude session follows the same conventions

### Two-Phase Delegation
- Phase 1: Research only (no edits) — propose a plan
- Phase 2: Execute approved plan (no commits) — leave changes for review
- Phase 3: Parent audits diff, user approves, parent commits
- Read-only tasks skip Phase 2

### Git Isolation
- Parent repo and child repos are fully independent
- Each child is `.gitignored` from the parent
- Never `git add .` from the parent directory
- Sub-agents in child directories use the child's git automatically

### Credential Management
- No secrets in config files or CLAUDE.md
- Credentials live in Secret Manager, referenced by name
- Wrapper scripts pull secrets at runtime
- Each project has its own cloud project (isolation)
- Always pass `--project=<id>` on every CLI command (never rely on active config)

### Action Tiers
- **read_only**: Auto-approve, no logging needed
- **low_risk_write**: Auto-approve + log the action
- **high_risk_write**: Require explicit user approval before executing
- Approval expires after 60 minutes — re-confirm if delayed

### Autonomous Agent Loop (for Multi-Step Builds)
- Used when approved plan has 3+ well-defined sequential steps
- Each step = one fresh Claude instance with context from prior steps
- Commits per step, on a feature branch
- Parent audits the branch (`git log`, `git diff main...feature`) before merge
- Not suitable for: investigation, cross-project work, mid-stream judgment calls

---

## Appendix: How the Pieces Fit Together

```
Session Start
    │
    ├─ Auto-loaded: CLAUDE.md + rules/* + MEMORY.md (~350 lines)
    │
    ├─ Session protocol: Read active.md, surface due/overdue items
    │
    ▼
User Request
    │
    ├─ General question → Answer directly
    │
    ├─ This codebase → Handle directly
    │
    ├─ Specific child project → Route via routing table
    │   │
    │   ├─ Read-only task → Single-phase sub-agent (research only)
    │   │
    │   └─ Write task → Two-phase delegation
    │       ├─ Phase 1: Research sub-agent (no edits)
    │       ├─ User reviews proposal
    │       ├─ Phase 2: Execute sub-agent (no commits)
    │       │   └─ OR: Autonomous loop (3+ steps)
    │       ├─ Parent audits diff
    │       └─ User approves → Parent commits
    │
    ├─ Cross-project → Coordinate multiple sub-agents
    │
    └─ High-risk → Handle in main session for visibility

Session End
    │
    ├─ Update active.md (move items, add new ones)
    ├─ Log decisions to decisions.md (if any were made)
    ├─ Commit + push (if requested)
    └─ Suggest /clear if context is bloated
```
