# SkillFlow

Organize AI agent skills to reduce startup token usage.

## What It Does

Moves skills to a hidden vault and creates category pointers. Agent loads only pointers (~1.5k tokens) instead of all skill descriptions (~80k).

## Quick Start

```bash
cd src/cli
python setup.py --yes
```

Then restart your agent.

## Structure

- `src/cli/` - Main Python script and config
- `src/gui/` - Optional Windows GUI (C#)
- `src/cli/config/` - Category keywords (editable)
- `src/cli/banner.txt` - ASCII art for batch file

## Commands

- `python setup.py` - Migrate (moves skills to vault)
- `python setup.py --dry-run` - Preview changes
- `python setup.py --sync` - Add new skills after initial migration
- `python setup.py --rebuild` - Rebuild pointers from existing vault (refreshes index)
- `python setup.py --status` - Health check + statistics
- `python setup.py --list` - List all skills (add `--output skills.csv` to export)
- `python setup.py --revert` - Restore all skills to original active directory

## Revert: Is It Reversible?

**Yes, mostly.** `--revert` will:
- Move all skills from the vault back to the active skills directory
- Remove all category pointers
- Delete the vault (if empty)
- Reset migration state

After revert, your agent will load all skills normally again (high token usage).

**Caveats:**
- Any NEW skills you installed **after** migration and already synced will also be moved back (which is expected)
- If you manually edited files in the vault, those changes will be restored (preserved)
- If vault is corrupted or missing, revert will fail (but this is unlikely)
- Revert does NOT restore the original order/categorization; skills are just placed back in the active directory

**Recommendation:** Run `--dry-run` with `--revert` first to see what will happen.

## How It Works

1. **Vault**: Skills stored in `~/.opencode-skill-libraries/` (hidden from agent)
2. **Pointers**: Lightweight folders in `~/.opencode/skills/` that the agent **does** scan
3. **Index**: `SKILL_INDEX.json` maps skill name → vault path for fast lookup
4. **Agent startup**: Loads only pointers (~1.5k tokens) instead of 80k+
5. **On-demand**: When a skill is needed, agent reads index → goes to vault → reads SKILL.md

## Testing

After migration, run the included test script to verify everything is working:

```bash
python test_skillflow.py
```

It checks:
- `SKILL_INDEX.json` exists and contains your skills
- Category pointers are in place
- Sample skill lookups work
- Vault structure is intact
- Migration state file present

All tests should pass. If not, review the output and consider running `--revert` then retrying.

## Notes

- Vault: `~/.opencode-skill-libraries/`
- Pointers: `~/.opencode/skills/`
- Index: `SKILL_INDEX.json` (auto-generated)
- Restart agent after migration

See `src/cli/README.md` for more.

## GUI (Optional)

Windows GUI built with .NET 10.0 WinForms.

**Requirements:**
- Windows 10/11
- .NET 10.0 SDK/Runtime
- Python 3.8+ (in PATH)

**Build:**
```bash
cd src/gui
dotnet build -c Release
```

**Run:**
```
bin\Release\net10.0-windows\SkillFlowGUI.exe
```

The GUI auto-detects `setup.py` relative to its location. It shows the banner, strips ANSI codes, and provides one-click access to all commands.

See `src/gui/README.md` for details.
