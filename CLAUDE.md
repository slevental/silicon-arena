# Autonomous Agent Guidelines

## 1. Core Philosophy & Stack
- **Role**: You are an autonomous Senior Python Engineer.
- **Package Manager**: STRICTLY use `uv`. Never use `pip` directly.
  - To add packages: `uv add <package>`
  - To run scripts: `uv run <script>`
- **Type Checking**: Strict typing is required. Use `make ty` to verify.
- **Testing**: TDD is preferred. Use `make test` (pytest).

## 2. The Loop (How you work)
Do not stop until `bd ready` returns no results.

1.  **Discovery**: Run `bd ready` to find the highest priority unblocked bead (task).
2.  **Claim**: Update the bead status: `bd update <id> --status in_progress`.
3.  **Context**: Read the bead description (`bd read <id>`) and relevant files.
4.  **Implementation**:
    - Write code.
    - If you need new libs, run `uv add <lib>`.
    - **CRITICAL**: Before finishing, run `make all` (runs tests and types).
    - If `make ty` fails, FIX THE TYPE ERRORS.
5.  **Commit**:
    - Git commit with the bead ID in the message: `git commit -am "feat: <description> (closes #<id>)"`
6.  **Close**: Mark the bead as done: `bd close <id>`.
7.  **Repeat**: Check `bd ready` again.

## 3. GitHub Integration (`gh`)
- If you are starting a massive Epic, you may create a branch: `git checkout -b feature/<bead-slug>`.
- When a major bead or set of beads is done, push and create a PR:
  - `git push -u origin HEAD`
  - `gh pr create --fill`

## 4. Troubleshooting
- If tests fail, debug. Do not comment out tests to make them pass.
- If you get stuck, add a comment to the bead: `bd comments add <id> "Stuck on logic X..."`.
- If you realize a task is too big, split it: `bd create "Subtask 1" --parent <id>`.
