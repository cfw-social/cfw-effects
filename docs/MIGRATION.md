# Migration from today's system

**Proposed, not built.** This is the path from the current CFW recipe library to CFW Studio. It does not authorize any production change by itself.

## What today looks like

Published recipes are already stored in Postgres as immutable, content-hashed bundles (`recipe_library_*` tables). A building block today is one recipe step, hashed and joined onto a `RecipeVersion`. Shared `c-*` components live in the canonical harness source and are copied into a bundle by the packager.

Getting a new recipe into the product takes several steps that this design wants to collapse:

1. Author files in the canonical harness source.
2. Package a scratch bundle.
3. Publish an immutable library version with `publish.mjs` and the account master key.
4. Snapshot a vendored manifest and add the recipe to the `VENDORED` map in application code, then deploy, so start-asks work.
5. Insert a `skills` table row, because `list_recipes` and the automation picker do not read the library by themselves.
6. After review, add a `PublicRecipeApproval` entry in `approvals.server.ts` and deploy, because the Marketplace allowlist lives in code, not in the database.

Brand bots can only run, adapt, and save already published recipes. They cannot create or list a new one through the API.

## What the target replaces

| Today's piece | Target replacement |
| --- | --- |
| `publish.mjs` plus the account master key | A merge to `cfw-studio`, then one authenticated sync endpoint |
| `VENDORED` map and vendored manifest files | Start-asks read snapshot rows |
| Marketplace allowlist in `approvals.server.ts` | A listed/approved flag on the recipe snapshot, set at merge |
| Separate `skills` table as the owner-facing catalog | `list_recipes` and the Marketplace read snapshot rows |

Worth keeping: a light fingerprint on each block and recipe (today's content hash is a close ancestor), immutable bytes so old runs still resolve, and private brand plans for one-off orders and automations.

## Proposed steps

1. **Fill the public repo.** Contribution docs, templates, and later CI already start here. Copy existing `c-*` components and recipes from the canonical harness source into `blocks/` and `recipes/`. Copy effects into `effects/` as `kind: effect` once we confirm where that source lives (no `cfw-effects` repo was in the org when this was written).
2. **Snapshot what is already published.** Import today's library versions into the snapshot tables, keeping their existing content hashes as fingerprints and recording the source commit when known.
3. **Ship the sync endpoint and Action.** One merge-to-snapshot path, authenticated with GitHub OIDC or a signed webhook. Prove it with an existing recipe before opening the repo to outside pull requests.
4. **Point the app at snapshots.** Marketplace and `list_recipes` read the database flag. Start-asks read snapshots instead of the VENDORED map. Add Reviews tagging on new posts.
5. **Retire the old publish path.** Stop using `publish.mjs` as the public path (keep a short admin escape hatch if needed). Then remove the VENDORED map, `approvals.server.ts`, and the `skills` table once nothing reads them.

The archived public `cfw-skills` repository, if it is still needed as history, can stay archived once `cfw-studio` is the source of truth. Its fate is still an open question in [DESIGN.md](DESIGN.md).
