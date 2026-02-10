# Decision Log

> Reverse-chronological record of significant decisions. Captures the "why" so
> future sessions don't re-litigate settled questions.
> Append new entries at the top.

## 2026-02-10 — Initial Architecture: Python + Facebook Business SDK

- **Decided**: Use Python with the official facebook-business SDK for campaign
  automation, rather than direct REST API calls or other language options.
- **Why**: Python has the most mature and well-maintained Facebook SDK, excellent
  data processing libraries for analytics, and is ideal for automation scripts.
  The official SDK handles API versioning, authentication, and error handling better
  than manual REST calls.
- **See**: `.claude/CLAUDE.md` for tech stack details

## 2026-02-10 — Project Structure: Full Orchestrator Model

- **Decided**: Implement the full operating model structure with .claude/, docs/,
  rules/, and persistent memory patterns from the start.
- **Why**: Starting with the complete structure enables better session continuity,
  task tracking, and decision logging from day one. Easier to set up now than
  retrofit later. Supports scaling to multiple ad accounts or child projects.
