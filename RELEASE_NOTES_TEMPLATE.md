# Release Notes Template

## [VERSION] - YYYY-MM-DD

### Added
- 

### Changed
- 

### Fixed
- 

### Known Issues
- 

---

## Installation

### CLI (Cross-platform)
1. Clone or download this repo
2. Install Python 3.8+
3. Run migration: `cd src/cli && python setup.py --yes`
4. Restart your agent

### GUI (Windows)
1. Download `SkillFlowGUI.zip` from the assets below
2. Extract to a folder (e.g., `C:\Program Files\SkillFlow\`)
3. Run `SkillFlowGUI.exe`
4. Click "Migrate Skills" to start

**Requirements:** Windows 10/11, .NET 10.0 Runtime (included in self-contained package)

---

## Migration Status

After running, check status:
```bash
python setup.py --status
```

Expected: `Overall Status: healthy`

---

## Token Reduction Estimate

- Before: ~80,000 tokens
- After: ~1,500 tokens
- Reduction: ~98%

---

## Reverting

If you need to undo the migration:
```bash
python setup.py --revert
```

See [README.md](README.md) for details.

---

## What's New

Describe the highlights of this release.

## Full Changelog

Link to commit history or list all changes.
