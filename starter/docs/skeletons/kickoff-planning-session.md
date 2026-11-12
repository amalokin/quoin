# Planning session — ‹the item›

## Launch

This is a planning-class session, launched with `claude --model ‹the planning class's model, process.md §Model policy, the binding table› --effort max`, the owner confirming `/effort` reads max; if the work asked of you belongs to the implementation class, say so before you start (process.md §Model policy).

## The item

Plan ‹the roadmap item, by number and title›; its roadmap entry is the spec, and this prompt yields to the entry on scope, order and purpose (process.md §II, stage 1).

## Reads

Start clean, a fresh session in a git worktree off `origin/main`: read `CLAUDE.md`, the roadmap, the item's design doc (its Read-first sections and its Active obligations) and the report sections they cite, and confirm the item's dependencies are merged, stopping to surface it if not (process.md §II, stage 1).

## Branch

Cut `docs/‹slug›-plan` from `origin/main` (process.md §II, stage 2).

## Design and plan

If the design doc is missing or still directional, check the survey triggers first (process.md §III, Triggers), stopping to surface one that fires, since a survey session then runs first; then run the ideation pass, laying the doc out as `docs/skeletons/design.md`. Then write the plan in `docs/plans/` with `superpowers:writing-plans`, laid out as `docs/skeletons/plan.md`, every number carrying its source and every plan ruling numbered and mirrored into the design's decision log (process.md §I; §II, stage 3).

## Design review

Run the adversarial gate on the design doc and the plan, its focus text laid out as `docs/skeletons/gate-focus.md`; judge every finding against the ground truth, record each ruling in the design's decision log, amend the plan, and leave none pending (process.md §II, stage 4; §Adversarial review protocol).

## The hard stop

End by opening the planning PR; dispatch no implementers and write no code or tests for the item, and treat the owner's merge as the go-ahead to implement (process.md §II, the hard stop).

## The planning PR

Carry in it the plan with its row in `docs/plans/README.md`, the design doc with its rulings and gate rows, the roadmap's status paragraph set to planned with the plan's path, and the updated "Now and next" and CLAUDE.md Status naming the next session; once the PR is open, write its number at the status sites and in the plan's index row by one more commit (process.md §II, the hard stop and stage 7).

## The planning PR's description

Lay the description out as `docs/skeletons/pr-description.md`, listing the rulings made in the owner's place and the questions only the owner can answer (process.md §II, the hard stop).

## Asking the owner

Ask the owner only what only the owner can answer, batched as structured questions; trivia gets a default and a recorded ruling (process.md §II).
