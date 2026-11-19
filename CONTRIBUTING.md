# Contributing to CFW Studio

Thank you for improving the block and recipe library. This guide is a draft of the process we want. **The merge-to-snapshot sync and CI described here are proposed, not built yet.** Until they exist, a merged pull request updates this repository only; it does not automatically publish anything into CFW.

## What to contribute

- A **block** under `blocks/c-<name>/` — reusable instructions plus supporting scripts, with declared inputs and outputs. Effects are blocks with `kind: effect`. A new variation of an existing block is a sibling (a new `variation` id), not a silent rewrite of the old files if others still depend on them.
- A **recipe** under `recipes/p-<name>/` — a guiding document that lists the blocks it uses. If the recipe needs a block that does not exist yet, include that block in the same pull request.

Start from `blocks/_template/` or `recipes/_template/`.

## Pull request checklist

1. The block or recipe id matches the folder name (`c-*` or `p-*`).
2. `block.yaml` or `recipe.yaml` declares inputs and outputs. A recipe's inputs should be the union of its blocks' required inputs, and it should declare the final output.
3. `SKILL.md` is enough for an agent to run the work without private local paths or credentials.
4. Supporting scripts live in the block's `scripts/` folder and are self-contained.
5. Sample outputs are attached to the pull request (or added under a `samples/` folder) so an admin can judge quality.
6. No secrets, API keys, or private local paths are included.

## Review and merge

An admin reviews the sample outputs, not only the file list. Merging to `main` is the approval. Once the sync is built, that merge will snapshot the changed blocks and recipes into CFW as immutable fingerprinted copies. Until then, merge only means the files are in this repository.

## Bots

Bots are welcome to open pull requests when they find a reusable piece, invent a block, or compose a new recipe. A bot should follow this same checklist, include sample outputs, and never write snapshots directly into CFW.

## License

Contributions are under the repository's GPL-3.0 license unless a later decision says otherwise.
