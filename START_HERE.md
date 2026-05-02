# Start Command

This project is for research-grounded drafting and export, not for handing in unreviewed AI text as final academic work.

## Folder-Native Start

Use this in a folder that has already been bootstrapped:

```text
start-paper here
```

Optional variant:

```text
start-paper here --just-write-it
```

## Expected Behavior

1. The agent checks for `.paper_writer/state/`
2. The agent reads local `AGENTS.md`, `.paper_writer/system_prompt.md`, and `.paper_writer/workflow.md`
3. The manager treats `.paper_writer/state/*.json` as canonical
4. The manager asks only the missing intake questions, or at most 10 in `--just-write-it` mode
5. The manager keeps claims, sources, and substantial-prose coverage current in `.paper_writer/state/evidence.json`, using `spw scaffold-coverage` when suggested coverage records would help
6. The manager runs deterministic checks with `spw wordcount` and `spw validate`
7. The manager exports deliverables only after validation passes

## Bootstrap A New Folder

```powershell
python scripts/bootstrap_folder_workspace.py "C:\path\to\empty-folder" --title "Working Title"
```

## Core CLI Commands

```powershell
spw render-views .
spw wordcount .
spw validate .
spw scaffold-coverage .
spw export .
```

If you want an AI assistant to help you install the repository itself, start with [AI_INSTALL_PROMPT.md](AI_INSTALL_PROMPT.md).
