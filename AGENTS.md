# AGENTS.md

Project harness for reliable agent-assisted development in a typescript codebase.

## Startup Workflow

Before writing code:

1. **Confirm working directory** with `pwd`
2. **Read this file** completely
3. **Read project docs if present** (`docs/ARCHITECTURE.md`, `docs/PRODUCT.md`, README, or equivalent)
4. **Run `.harness/init.sh`** to verify environment is healthy
5. **Read `.harness/feature_list.json`** to see current feature state
6. **Review recent commits** with `git log --oneline -5`

If baseline verification is failing, repair that first before adding new scope.

## Working Rules

- **One feature at a time**: Pick exactly one unfinished feature from `.harness/feature_list.json`
- **Verification required**: Don't claim done without running verification commands
- **Update artifacts**: Before ending session, update `.harness/progress.md` and `.harness/feature_list.json`
- **Stay in scope**: Don't modify files unrelated to the current feature
- **Leave clean state**: Next session must be able to run `./.harness/init.sh` immediately

## Required Artifacts

- `.harness/feature_list.json` — Feature state tracker (source of truth)
- `.harness/progress.md` — Session continuity log
- `.harness/init.sh` — Standard startup and verification path
- `.harness/session-handoff.md` — Optional, for larger sessions

## Definition of Done

A feature is done only when ALL of the following are true:

- [ ] Target behavior is implemented
- [ ] Required verification actually ran (tests / lint / type-check)
- [ ] Evidence recorded in `.harness/feature_list.json` or `.harness/progress.md`
- [ ] Repository remains restartable from standard startup path

## End of Session

Before ending a session:

1. Update `.harness/progress.md` with current state
2. Update `.harness/feature_list.json` with new feature status
3. Record any unresolved risks or blockers
4. Commit with descriptive message once work is in safe state
5. Leave repo clean enough for next session to run `.harness/init.sh` immediately

## Verification Commands

```bash
# Full verification (recommended)
./.harness/init.sh
```

Required checks:
- `npm install`
- `npm run type-check`
- `npm run lint`
- `npm run build`

## Escalation

If you encounter:
- **Architecture decisions**: Consult project architecture docs if present, otherwise ask user
- **Unclear requirements**: Check product/requirements docs if present, otherwise ask user
- **Repeated test failures**: Update progress, flag for human review
- **Scope ambiguity**: Re-read `.harness/feature_list.json` for definition of done
