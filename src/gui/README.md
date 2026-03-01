# SkillFlow GUI

Windows GUI wrapper for SkillFlow.

## Quick Start (Portable)

Download the portable release zip from [GitHub Releases](https://github.com/ionutrobert/SkillFlow/releases). Extract anywhere and double-click `SkillFlowGUI.exe`. No installation required — Python is bundled.

**Note:** The portable package includes `python/` (portable Python) and `cli/` (SkillFlow CLI) alongside the GUI executable. The GUI automatically detects and uses them.

## Requirements (for building from source)

- .NET 10.0 SDK/Runtime
- Python 3.8+ (only needed for development; not required when using portable package)

## Build

```bash
dotnet build -c Release
```

Output: `bin\Release\net10.0-windows\SkillFlowGUI.exe`

## Usage

1. Ensure `src/cli/setup.py` exists (default path: `C:\Work\SkillFlow\src\cli\setup.py`)
2. Run the executable
3. Click operations: Dry Run, Migrate, Stats, Health, Revert, Optimize

## Path Configuration

The GUI looks for `setup.py` in the following order:
1. `.\cli\setup.py` (relative to executable) — portable package layout
2. `.\src\cli\setup.py` (relative to executable) — repo layout
3. Hardcoded fallback: `C:\Work\SkillFlow\setup.py`

Edit `Program.cs` to change these paths if needed.

## How It Works

The GUI runs `python setup.py <args>` as a subprocess. It captures output, strips ANSI colors, and displays it in a RichTextBox. A banner is shown at start and completion.

When the portable package is used, the GUI detects `python/python.exe` next to the executable and uses that instead of the system Python.

