# ‹Item› — ‹what the plan builds›: implementation plan

> **For agentic workers:** *The sub-skill that runs the plan, superpowers:subagent-driven-development, and the sessions that run it (process.md §II, stage 5).*

> *The banner: the record line the plans index gives, written by the PR that executes the plan and absent before it (process.md §Doc taxonomy, the Plan row; §Canonical and pointer sites, the record freeze).*

**Goal:** *One sentence: what is built and proven, and for whom.*

**Architecture:** *The shape of the build in a few sentences: its parts and how they fit.*

**Tech Stack:** *The languages, libraries and tools the plan builds with, and the checks it runs.*

**Spec:** *The design doc the plan implements, by path, and its gate record by link: the rows of the design's decision log that record the design gate over this plan, which the plan check reads (process.md §II, stage 3; the plan check).*

## Plan rulings

*The plan's decision record, with the pinned facts: the rulings `R-‹item›-‹n›`, each with its rationale and its cost if wrong, mirrored into the design's decision log; when a ruling of the loop amends the parameter one sets, it is rewritten in place and marked as whose ruling it is (process.md §II, stage 3; §Canonical and pointer sites, the record freeze; §Model policy, Records).*

## Pinned facts

*The plan's decision record, with the rulings: each fact a task builds on, with the observation that pins it, and any formula with no observation behind it marked unpinned with the observation that would pin it; amended in place and marked as whose ruling it is, as a plan ruling is, when a ruling of the loop changes the parameter it sets (process.md §II, stage 3; §Model policy, Records).*

## Global constraints

*The constraints that hold for every task, each citing where its rule lives instead of restating it (process.md §Canonical and pointer sites).*

## Review focus

*The places the item is most likely to be wrong, numbered, each with the test or check that guards it.*

## File structure

*The files the plan creates and the files it modifies, by path; each task names its own again.*

## Tasks

*The tasks in the order they run, each under a heading of the shape below.*

### Task ‹N›: ‹what it builds›

*The task shape superpowers:writing-plans gives: Files to create, modify and test, by path; Interfaces, what the task consumes and produces, by name and signature; then the steps as checkboxes, the failing test first and a commit last (process.md §II, stage 3).*
