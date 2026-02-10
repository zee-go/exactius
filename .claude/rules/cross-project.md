# Cross-Project Context

## Credentials Reference

Facebook API credentials are stored in environment variables or a secrets manager.
Never commit credentials to version control.

| Secret | Storage | Used By |
|---|---|---|
| FB_ACCESS_TOKEN | .env (local) / Secret Manager | Facebook API authentication |
| FB_APP_SECRET | .env (local) / Secret Manager | Facebook App verification |

## Conventions

- **Commit style**: Clear, descriptive messages with context. Add co-author tag
  when Claude commits: `Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>`
- **Session memory**: Uses `docs/active.md` + `docs/decisions.md` pattern.
  Read active.md at session start, update both at session end.
- **CLAUDE.md philosophy**: Lean index, not a knowledge base. Max 3 lines per
  topic. Heavy docs go in `docs/`.
- **Deployment rule**: Always ask before deploying or launching campaigns.
- **Testing first**: Always test with small budgets before scaling.

## Git Operations

- This is a single git repository
- `.env` file is gitignored (contains credentials)
- Always review diffs before committing
- Push to remote only after explicit user approval

## Facebook API Safety

- **Rate limits**: Facebook API has strict rate limits. Implement exponential
  backoff and respect rate limit headers.
- **Spend limits**: Always set daily/lifetime budget limits to prevent runaway spend.
- **Testing**: Use sandbox mode or tiny budgets for testing.
- **Error handling**: Log all API errors with full context for debugging.
- **Async operations**: Many operations (ad creation, campaign updates) are async.
  Poll for completion status.
