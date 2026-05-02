# Start Command

This project is in development and is meant for research drafts and exploration, not for generating a thesis to hand in as final work.

Use this command in a folder that has already been bootstrapped with the local paper-writer files:

```text
start-paper here
```

Optional variants:

```text
start-paper here --output latex
start-paper here --output docx
start-paper here --title "My Paper Title"
start-paper here --just-write-it
```

## Expected Behavior

1. The agent checks for `.paper_writer/`
2. The agent reads local `AGENTS.md` and `.paper_writer/system_prompt.md`
3. The manager reads local workflows and role cards
4. The manager asks only the missing intake questions, or at most 10 in `--just-write-it` mode
5. The manager creates specialist agents when available, keeps status visible in `.paper_writer/agent_status.md`, and builds the brief, evidence package, outline, draft, and review pass
6. The manager exports the final manuscript to `paper.tex` or `paper.docx` in the folder root

## If The Folder Is Still Empty

Bootstrap it once first:

```powershell
python scripts/bootstrap_folder_workspace.py "C:\path\to\empty-folder" --output docx --title "Working Title"
```

If you want an AI assistant to help you install the repository itself, start with [AI_INSTALL_PROMPT.md](AI_INSTALL_PROMPT.md).
