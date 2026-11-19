# Agent instructions

This repository holds the **proposed** design for CFW Studio, plus empty scaffolds. Almost none of the runtime described in the docs is built yet.

## Start here

1. Read [docs/DESIGN.md](docs/DESIGN.md) for the target model (blocks, recipes, GitHub as source of truth, merge-to-snapshot sync, Reviews tagging).
2. Read [docs/DECISIONS.md](docs/DECISIONS.md) for the decisions and the reasons they were chosen on 2026-11-19.
3. Read [docs/MIGRATION.md](docs/MIGRATION.md) before touching today's Social publish path (`publish.mjs`, the VENDORED map, Marketplace approvals in code, or the `skills` table).
4. Follow [CONTRIBUTING.md](CONTRIBUTING.md) when adding a block or recipe. Use `blocks/_template/` and `recipes/_template/`.

## Hard rules

- Treat everything in `docs/` as **proposed, not built**, unless a later decision or merged implementation says otherwise.
- Do not invent a parallel catalog, a new versioning scheme, or a bot-to-Postgres upload path. New work should match the design: contribute via pull request, approve by merge, sync a snapshot after merge, and have bots render from the snapshot.
- Do not commit secrets, credentials, API keys, or private local paths.
- Do not copy AGPL third-party application code into this repo. Rebuild ideas as CFW blocks and recipes.
- Do not push directly to `main` once this repo has content. Open a pull request.
- Do not implement the CFW sync endpoint, Marketplace changes, or Reviews tagging in this repo unless the task explicitly says to; those changes belong in the Social application, guided by `docs/MIGRATION.md`.
