# SkillFlow

Smart skill organization for AI agents. Reduces startup token usage by moving skills to a hidden vault and using lightweight category pointers.

## Quick Start

```bash
cd src/cli
python setup.py --yes
```

Restart your agent. Done.

## Commands

- `python setup.py` - Run migration (with confirmation)
- `python setup.py --dry-run` - Preview changes
- `python setup.py --sync` - Add new skills
- `python setup.py --rebuild` - Rebuild pointers
- `python setup.py --status` - Show health
- `python setup.py --revert` - Undo migration
- `python setup.py --list` - List skills

## How It Works

1. Skills moved to `~/.opencode-skill-libraries/` (vault)
2. Pointers created in `~/.opencode/skills/` (what agent scans)
3. Master index `SKILL_INDEX.json` enables fast lookup
4. Agent reads index → finds skill → reads from vault

Token usage drops from tens of thousands to ~1,500.

## Testing

Validate your installation:

```bash
python test_skillflow.py
```

Checks index, pointers, vault structure, and sample lookups.

## Files

- `src/cli/setup.py` - Main script
- `src/cli/config/` - Categorization config
- `src/gui/` - Optional WinForms GUI

See inline comments in `setup.py` for technical details.
