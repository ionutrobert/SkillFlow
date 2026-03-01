# SkillFlow GUI

Windows GUI wrapper for SkillFlow.

## Requirements

- .NET 10.0 SDK/Runtime
- Python 3.8+

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

Edit `Program.cs` line 20 to change the expected `setup.py` location.

