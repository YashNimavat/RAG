# Install Visual Learning Writer in Claude Code (Windows)

The skill is the complete **visual-learning-writer** folder, including `SKILL.md`, `references/` and `examples/`. Do not copy `SKILL.md` alone if you want the original supporting guidance and approved example.

## Recommended: personal installation (all local projects)

Extract `visual-learning-writer.zip` into:

```text
C:\Users\<YourWindowsUsername>\.claude\skills\
```

Resulting file:

```text
C:\Users\<YourWindowsUsername>\.claude\skills\visual-learning-writer\SKILL.md
```

Or run in PowerShell, after downloading the ZIP to Downloads:

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills" | Out-Null
Expand-Archive -LiteralPath "$HOME\Downloads\visual-learning-writer.zip" -DestinationPath "$HOME\.claude\skills" -Force
Test-Path "$HOME\.claude\skills\visual-learning-writer\SKILL.md"
```

The last command should print `True`. If the ZIP is stored elsewhere, change the ZIP path.

## Alternative: project-specific installation

Extract the same ZIP into the *root of your project's* `.claude\skills` folder:

```text
D:\your-project\.claude\skills\visual-learning-writer\SKILL.md
```

In PowerShell, while standing in your project's root folder:

```powershell
New-Item -ItemType Directory -Force -Path ".claude\skills" | Out-Null
Expand-Archive -LiteralPath "$HOME\Downloads\visual-learning-writer.zip" -DestinationPath ".claude\skills" -Force
Test-Path ".claude\skills\visual-learning-writer\SKILL.md"
```

## Check in Claude Code

1. Start/restart a Claude Code session **inside the project folder**, in the VS Code terminal or regular terminal.
2. Type `/visual-learning-writer BM25` (or `/visual-learning-writer Explain Hybrid Retrieval`).
3. Claude should inspect your project files first, report meaningful prerequisite gaps, and ask whether to include additional missing explanations before expanding the lesson.
4. Once approved, Claude generates an interactive HTML lesson in the project's existing lesson folder or `lessons/`.

Personal skills are loaded by local Claude Code sessions across projects. Project skills are scoped to that repository. They do **not** automatically sync to Claude Web/Cowork or a different Windows computer. Confirmed via https://code.claude.com/docs/en/skills

**Avoid installing two versions with the same name:** Claude Code gives the personal skill priority over a same-name project skill. To customize per project, either install only there, or use a distinct name.
