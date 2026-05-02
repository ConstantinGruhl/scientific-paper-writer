# AI Install Prompt

Copy the prompt below into Codex, Claude, ChatGPT, or another assistant if you want help installing this repository and getting it running.

```text
Help me install and run this GitHub project:
https://github.com/ConstantinGruhl/scientific-paper-writer

Important context:
- I may not know how Git repositories work.
- I may not know how to use the terminal.
- Please keep the instructions beginner-friendly.
- If you can run terminal commands for me, do that when possible and explain what you are doing.
- If you cannot run commands for me, guide me one step at a time and wait after major steps.

What I want you to do:
1. Detect my operating system first.
2. Check whether Git is installed.
3. Check whether Python 3 is installed.
4. If Git is missing, either:
   - help me install Git, or
   - show me how to download the repository as a ZIP instead.
5. If Python is missing, help me install Python 3.
6. Clone or download the repository.
7. Explain the difference between these two workflows and recommend one:
   - folder-native workflow
   - repo workspace workflow
8. If I choose folder-native workflow, help me run:
   python scripts/bootstrap_folder_workspace.py "<path to my paper folder>" --title "<working title>" --output docx
9. Then explain how to open the resulting folder in a file-aware AI assistant and use:
   start-paper here
10. If I choose repo workspace workflow, help me run:
   python scripts/init_paper_project.py my-paper-slug --title "<working title>"
11. Mention this disclaimer clearly before we start writing:
   This project is in development. It is intended for research drafts, exploration, and early manuscript development. It should not be used to generate a thesis and hand it in as final academic work.
12. If a command fails, show me the exact error and help me fix that specific issue instead of guessing.

Please adapt the commands to my operating system and explain unfamiliar terms in plain language.
```
