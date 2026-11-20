# Contributing to CFW Studio

Thank you for improving the effects, block, and recipe library. This guide is a draft of the process we want. **The merge-to-snapshot sync and CI described here are proposed, not built yet.** Until they exist, a merged pull request updates this repository only; it does not automatically publish anything into CFW.

## What to contribute

- An **effect** under `effects/e-<name>/` — a visual or audio treatment (transition, confetti, fireworks, caption style, overlay, sound effect, or music bed). An effect is a block of `kind: effect` that recipes reference by id. Include a preview of the look or sound.
- A **block** under `blocks/c-<name>/` — reusable instructions plus supporting scripts, with declared inputs and outputs.
- A **recipe** under `recipes/p-<name>/` — a guiding document that lists the blocks and effects it uses. If the recipe needs a block or effect that does not exist yet, include it in the same pull request.

A new variation of an existing block or effect is a sibling (a new `variation` id), not a silent rewrite of the old files if others still depend on them.

Start from `effects/_template/`, `blocks/_template/`, or `recipes/_template/`.

## Pull request checklist

1. The effect, block, or recipe id matches the folder name (`e-*`, `c-*`, or `p-*`).
2. `effect.yaml`, `block.yaml`, or `recipe.yaml` declares inputs and outputs. A recipe's inputs should be the union of its blocks' and effects' required inputs, and it should declare the final output.
3. `SKILL.md` is enough for an agent to run the work without private local paths or credentials.
4. Supporting scripts live in the `scripts/` folder and are self-contained.
5. Sample outputs are attached to the pull request (or added under a `samples/` folder) so an admin can judge quality. Effect pull requests also include a preview (see `effects/_template/PREVIEW.md`).
6. No secrets, API keys, private local paths, or private media URLs are included.

## Review and merge

An admin reviews the sample outputs, not only the file list. Merging to `main` is the approval. Once the sync is built, that merge will snapshot the changed effects, blocks, and recipes into CFW as immutable fingerprinted copies. Until then, merge only means the files are in this repository.

## Bots

Bots are welcome to open pull requests when they find a reusable piece, invent an effect or block, or compose a new recipe. A bot should follow this same checklist, include sample outputs, and never write snapshots directly into CFW.

## License

Contributions are under the repository's GPL-3.0 license unless a later decision says otherwise.

The effects library already in `effects/` (`fx/`, `presets/`, `examples/`, `tests/test_smoke.py`, `scripts/download_models.sh`, and the synthetic media and preview stills that shipped with it) is GPL-3.0-or-later. See [effects/README.md](effects/README.md#license). Changes to those paths stay on that grant. New and edited `e-*` catalog entries follow the repository GPL-3.0, same as blocks and recipes. The two grants are compatible and are distributed together as an aggregate.
