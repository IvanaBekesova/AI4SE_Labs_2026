# Project Guidelines

## Scope

This workspace is the documentation and evidence repository for **Week 08 - Dissecting coding assistants**. It contains Markdown assignment briefs and student-generated reports and configuration evidence; it is not an application with source-code build or test targets.

## Repository layout

- `Assignments/readme.md` gives the assignment overview.
- `Assignments/Task_<number>/Task_<number>.md` contains the task brief.
- Task folders may also contain the required deliverable, such as `report1.md`, screenshots, configuration files, or generated reports.
- `.github/prompts/` contains repository-level VS Code prompt files.

## Build, test, and lint

No package manifest, build script, test runner, or linter configuration is present. Do not invent build/test commands. Verify Markdown changes by:

- Checking links and relative paths.
- Confirming that deliverables remain in the matching `Assignments/Task_<number>/` folder.
- Viewing screenshots or images when an assignment requires visual evidence.

## Documentation conventions

- Preserve each assignment's original `Task_<number>` folder structure and naming.
- Keep assignment briefs and submitted reports separate; do not overwrite a brief with a report.
- Markdown and screenshot/report deliverables are tracked per task. For example, Task 1 uses `Assignments/Task_1/report1.md`, while Task 2 uses `Assignments/Task_2/task2.png`.
- Assignment text is primarily in English, with some supporting reports and Copilot prompt text in Slovak. Preserve the language of the existing deliverable when editing it.
- Keep configuration and report files suitable for submission: redact credentials, tokens, API keys, and private paths.
- Screenshots should remain as image artifacts and should not be replaced by placeholder text.

## Copilot configuration

- Repository prompts belong in `.github/prompts/` and use `.prompt.md` files with YAML frontmatter containing `name`, `description`, and `agent` when applicable.
- The existing prompt file demonstrates a prompt-specific workflow: `task2.prompt.md` is a focused explain-code prompt and uses `${selection}` for the selected code.
- Changes to these files should preserve prompt frontmatter and prompt intent rather than converting them into generic documentation.
