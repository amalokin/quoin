# {{PROJECT}}

<!-- fill: what the project is, in one or two sentences, for a reader who has never seen it; the rule is plain words, no internal labels -->

## Setup

Clone the repository from `{{REPO_URL}}`.

<!-- fill: the prerequisites, the one-time install and the first run, as commands; the rule is that a reader with a clean machine ends at a green fast suite -->

The fast suite is `{{TEST_COMMAND}}` and the lint is `{{LINT_COMMAND}}`. The repository's Python tools run as
`{{INTERPRETER}} -I <tool>`; [AGENTS.md](AGENTS.md) lists them with the rest of the commands.

## Quick start

<!-- fill: the commands that produce the project's main outputs, one per line with a sentence on what each prints or writes; the rule is a command a reader can run as written -->

## How the work is done

How {{PROJECT}} is built is [docs/process.md](docs/process.md), which opens with its Purpose and principles. A session
starts at [CLAUDE.md](CLAUDE.md), which loads first and points to the roadmap; the mechanics are in
[AGENTS.md](AGENTS.md). Each session starts from a kickoff prompt that {{OWNER}} copies from
[docs/skeletons/](docs/skeletons/) into a gitignored `local/`.

## License

<!-- fill: the project's license and the file that holds it, or that the repository is private; the rule is one line, and this section is deleted when there is nothing to say -->
