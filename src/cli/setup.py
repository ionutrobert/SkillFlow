#!/usr/bin/env python3
"""
SkillFlow - Infinite Context. Zero Token Tax.
Smart skill organization for AI agents with hierarchical categories.

Usage:
    python setup.py                    # Run full setup (with confirmation)
    python setup.py --dry-run          # Preview changes without applying
    python setup.py --rebuild          # Rebuild pointers from existing vault
    python setup.py --optimize         # Recategorize skills with improved heuristics
    python setup.py --stats            # Show category statistics
    python setup.py --status           # Show health status
    python setup.py --revert           # Revert migration
    python setup.py --validate         # Validate configuration
    python setup.py --list             # List all skills and their categories
    python setup.py --sync             # Sync new skills from sources to vault
    python setup.py --yes              # Skip confirmation prompt
"""

import os
import shutil
import json
import argparse
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ==========================================
# Configuration - Aligned with SkillPointer
# ==========================================

# Primary active skills directory (where pointers go)
# Using legacy path that OpenCode scans on Windows
ACTIVE_SKILLS_DIR = Path.home() / ".opencode" / "skills"

# Hidden vault (where real skills are stored)
HIDDEN_VAULT_DIR = Path.home() / ".opencode-skill-libraries"

# State file
STATE_FILE = Path.home() / ".skillflow-state.json"

# Additional skill sources to migrate (will be moved to vault)
# These are scanned for real skills and cleared after migration
EXTRA_SKILL_SOURCES = [
    Path.home() / ".agents" / "skills",
    Path.home() / ".opencode" / "skills",  # Legacy location
]

# Colors for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_info(text):
        print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

# Fix Colors class to include WARNING (use YELLOW)
Colors.WARNING = Colors.YELLOW

# ==========================================
# State Management
# ==========================================

class MigrationState:
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self.load()
    
    def load(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                return self.get_default_state()
        return self.get_default_state()
    
    def get_default_state(self) -> dict:
        return {
            'migrated': False,
            'vault_exists': False,
            'migrated_at': None,
            'pointers_created': [],
            'original_sources': [],  # List of source dirs that were migrated
            'skill_count': 0,
            'failed_at': None
        }
    
    def save(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def is_migrated(self) -> bool:
        return self.state.get('migrated', False) and self.state.get('vault_exists', False)
    
    def has_incomplete_migration(self) -> bool:
        return self.state.get('failed_at') is not None

    def mark_failed(self, stage: str):
        self.state['failed_at'] = stage
        self.save()

    def mark_success(self):
        self.state['migrated'] = True
        self.state['vault_exists'] = True
        self.state['migrated_at'] = datetime.utcnow().isoformat()
        self.state['failed_at'] = None
        self.save()

    def reset(self):
        self.state = self.get_default_state()
        self.save()

# ==========================================
# Configuration Loading
# ==========================================

def load_config():
    """Load configuration from categories.json."""
    config_path = Path(__file__).parent / "config" / "categories.json"
    if not config_path.exists():
        print_error(f"Config not found: {config_path}")
        return None
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        return None

def get_category_for_skill(skill_name: str, config: dict) -> str:
    """Categorize a skill using keyword matching with word boundaries."""
    name_lower = skill_name.lower().replace("_", "-")
    
    # Check hierarchical categories first (exact match for meta-skills)
    hierarchical = config.get("categories", {}).get("hierarchical", [])
    for cat in hierarchical:
        if cat in name_lower:
            return cat
    
    # Check keywords with word boundaries
    keywords = config.get("keywords", {})
    for category, keyword_list in keywords.items():
        for keyword in keyword_list:
            keyword_lower = keyword.lower()
            # Use word boundary regex: \bkeyword\b
            pattern = rf'\b{re.escape(keyword_lower)}\b'
            if re.search(pattern, name_lower):
                return category
    
    return "_uncategorized"

# ==========================================
# Directory Operations
# ==========================================

def setup_directories(dry_run: bool = False) -> bool:
    """Create necessary directories."""
    try:
        # Create active skills dir if not exists
        if not ACTIVE_SKILLS_DIR.exists():
            if not dry_run:
                ACTIVE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
                print_success(f"Created active skills dir: {ACTIVE_SKILLS_DIR}")
            else:
                print(f"[DRY RUN] Would create: {ACTIVE_SKILLS_DIR}")
        
        # Create hidden vault
        if not HIDDEN_VAULT_DIR.exists():
            if not dry_run:
                HIDDEN_VAULT_DIR.mkdir(parents=True, exist_ok=True)
                print_success(f"Created vault: {HIDDEN_VAULT_DIR}")
            else:
                print(f"[DRY RUN] Would create: {HIDDEN_VAULT_DIR}")
        
        return True
    except Exception as e:
        print_error(f"Failed to setup directories: {e}")
        return False

def get_skill_source_name(source_path: Path) -> str:
    """Get a readable name for a skill source."""
    if source_path == ACTIVE_SKILLS_DIR:
        return "active skills directory"
    for src in EXTRA_SKILL_SOURCES:
        if src == source_path:
            return f"extra source: {src}"
    return str(source_path)

def find_all_skill_sources() -> list[Path]:
    """Find all directories that contain skills to migrate."""
    sources = []
    
    # Check active skills dir (may already have pointers)
    if ACTIVE_SKILLS_DIR.exists():
        sources.append(ACTIVE_SKILLS_DIR)
    
    # Check extra sources
    for src in EXTRA_SKILL_SOURCES:
        if src.exists():
            sources.append(src)
    
    return sources

def is_pointer_folder(folder_name: str) -> bool:
    """Check if a folder is a category pointer."""
    return folder_name.endswith("-category-pointer")

def is_skill_folder(folder_path: Path) -> bool:
    """Check if a folder is a real skill (has SKILL.md and not a pointer)."""
    if not folder_path.is_dir():
        return False
    if is_pointer_folder(folder_path.name):
        return False
    if folder_path.name.startswith('.'):
        return False
    # Check if it has a SKILL.md file
    if not (folder_path / "SKILL.md").exists():
        return False
    return True

def get_all_real_skills(sources: list[Path]) -> list[tuple[Path, Path]]:
    """
    Get all real skills from all sources.
    Returns list of (skill_path, source_dir) tuples.
    """
    skills = []
    for source in sources:
        for item in source.iterdir():
            if is_skill_folder(item):
                skills.append((item, source))
    return skills

# ==========================================
# Migration
# ==========================================

def migrate_skills(dry_run: bool, config: dict) -> tuple[int, dict]:
    """Migrate skills from all sources to vault."""
    print_header("Migrating Skills")
    
    sources = find_all_skill_sources()
    if not sources:
        print_warning("No skill sources found.")
        return 0, {}
    
    print_info(f"Scanning {len(sources)} source(s):")
    for src in sources:
        print(f"  - {get_skill_source_name(src)}")
    print()
    
    skill_folders = get_all_real_skills(sources)
    
    if not skill_folders:
        print_warning("No skills found to migrate.")
        return 0, {}
    
    print(f"Found {len(skill_folders)} skill(s) to migrate.\n")
    
    category_counts = defaultdict(int)
    moved_count = 0
    
    for skill_path, source_dir in skill_folders:
        category = get_category_for_skill(skill_path.name, config)
        cat_dir = HIDDEN_VAULT_DIR / category
        dest = cat_dir / skill_path.name
        
        print(f"  {skill_path.name} -> {category}/")
        
        if not dry_run:
            try:
                cat_dir.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(skill_path), str(cat_dir))
                moved_count += 1
                category_counts[category] += 1
            except Exception as e:
                print_error(f"Failed to migrate {skill_path.name}: {e}")
        else:
            moved_count += 1
            category_counts[category] += 1
    
    if not dry_run:
        print_success(f"Moved {moved_count} skill(s) to vault")
    else:
        print(f"[DRY RUN] Would move {moved_count} skill(s) to vault")
    
    return moved_count, dict(category_counts)

def generate_pointers(dry_run: bool = False, config: dict = None, state: MigrationState = None):
    """Generate category pointers in active skills directory."""
    print_header("Generating Pointers")
    
    if not HIDDEN_VAULT_DIR.exists():
        print_warning("Vault not found. Cannot generate pointers.")
        return False
    
    # Scan vault to count skills per category and build index
    categories_with_skills = []
    total_skills = 0
    skill_index = {}  # {skill_name: relative_path_from_vault}
    
    for cat_dir in HIDDEN_VAULT_DIR.iterdir():
        if not cat_dir.is_dir():
            continue
        # Count SKILL.md files recursively within this category
        skill_files = list(cat_dir.rglob("SKILL.md"))
        count = len(skill_files)
        if count > 0:
            categories_with_skills.append((cat_dir.name, count))
            total_skills += count
            # For each skill, get its folder relative to vault
            for skill_skill in skill_files:
                skill_folder = skill_skill.parent
                rel_path = skill_folder.relative_to(HIDDEN_VAULT_DIR).as_posix().replace('\\', '/')
                skill_index[skill_folder.name] = rel_path
    
    if not categories_with_skills:
        print_warning("No skills found in vault.")
        return False
    
    print(f"Found {total_skills} skills across {len(categories_with_skills)} categories.\n")
    
    # First, generate the SKILL_INDEX.json (master index)
    if not dry_run:
        import json
        index_path = ACTIVE_SKILLS_DIR / "SKILL_INDEX.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(skill_index, f, indent=2, sort_keys=True)
        print_success(f"Created SKILL_INDEX.json ({len(skill_index)} entries)")
        print_info(f"Index path: {index_path}")
    else:
        print(f"[DRY RUN] Would create SKILL_INDEX.json ({len(skill_index)} entries)")
    
    created_count = 0
    
    for category, count in categories_with_skills:
        pointer_name = f"{category}-category-pointer"
        pointer_dir = ACTIVE_SKILLS_DIR / pointer_name
        
        # Check if pointer already exists
        if pointer_dir.exists():
            # In dry run or rebuild, we'll overwrite
            if not dry_run and state and state.is_migrated():
                # Already exists, skip unless rebuild
                continue
        
        if not dry_run:
            pointer_dir.mkdir(exist_ok=True)
            
            # Create pointer SKILL.md with reference to index
            content = f"""---
name: {pointer_name}
description:Provides access to {count} specialized skills in {category.replace('-', ' ').title()} category.
---

  ___ _   _ _ _ ___ _            
 / __| |_(_) | | __| |_____ __ __
 \__ \ / / | | | _|| / _ \\\\ V  V / 
 |___/\\_\\_\\|_|_|_| |_\\___/ \\_/\\_/ 
                                  

# {category.replace('-', ' ').title()} Capability Library

**Skills Available:** {count} | **Token Cost:** ~8 tokens

You do NOT have all {category} skills loaded immediately. Instead, you have access to an organized library of {count} specialized skills in your local vault.

## Fast Lookup

To quickly find any skill:

1. **Read `SKILL_INDEX.json`** in the active skills directory (`{ACTIVE_SKILLS_DIR}`)
2. **Find the skill name** in the index to get its vault path (e.g., "nextjs-best-practices" → "frontend/nextjs/nextjs-best-practices")
3. **Read the skill** directly using that path: `{HIDDEN_VAULT_DIR}/[path-from-index]/SKILL.md`

This avoids directory browsing and gives instant access.

## How to Use

- If you need a specific skill, consult `SKILL_INDEX.json` first
- Then use `view_file` to read the skill's SKILL.md directly from the vault path indicated in the index
- Follow the instructions in that skill file

## Ecosystem Discovery (For Missing Skills)

If you can't find a relevant skill in the vault:

1. Search the skills ecosystem: `npx skills find [your-task]`
2. Example: `npx skills find {category}`
3. If found, install with: `npx skills add <owner/repo>@<skill> -g -y`

Learn more at: https://skills.sh/

## Remember

- **DO NOT guess** best practices - always check the vault first
- **DO use** `npx skills find` when you need something not in the vault
- **DO suggest** installing new skills if you find useful ones at skills.sh
"""
            
            with open(pointer_dir / "SKILL.md", "w", encoding='utf-8') as f:
                f.write(content)
            
            # Also create a simple README.md in pointer dir
            with open(pointer_dir / "README.md", "w", encoding='utf-8') as f:
                f.write(f"# {category}-category-pointer\n\nThis is a SkillPointer to the `{category}` category in the hidden vault.\n")
            
            created_count += 1
            print(f"  ⊕ Created {pointer_name} -> {count} skills")
        else:
            print(f"  ⊕ Would create {pointer_name} -> {count} skills")
    
    if not dry_run:
        print_success(f"Created {created_count} category pointers")
        print_success(f"Total tokens: pointers={created_count * 8}, index={len(skill_index) * 8} = ~{created_count * 8 + len(skill_index) * 8}")
    else:
        print(f"[DRY RUN] Would create {created_count} category pointers")
    
    return True

def cleanup_skill_sources(dry_run: bool = False):
    """Remove any remaining raw skill folders from all sources (should be only pointers)."""
    print_header("Cleaning Up Source Directories")
    
    sources = find_all_skill_sources()
    cleaned_count = 0
    
    for source in sources:
        for item in source.iterdir():
            if is_skill_folder(item):
                print(f"  Removing leftover skill: {item.name}")
                if not dry_run:
                    try:
                        shutil.rmtree(item)
                        cleaned_count += 1
                    except Exception as e:
                        print_error(f"Failed to remove {item.name}: {e}")
                else:
                    cleaned_count += 1
    
    if not dry_run:
        if cleaned_count > 0:
            print_success(f"Cleaned {cleaned_count} leftover skill(s)")
        else:
            print_info("No leftover skills found (sources already clean)")
    else:
        print(f"[DRY RUN] Would clean {cleaned_count} leftover skill(s)")

def full_migration(dry_run: bool = False, config: dict = None, state: MigrationState = None) -> bool:
    """Execute full migration."""
    print_header("Full Migration")
    
    if not setup_directories(dry_run):
        if state:
            state.mark_failed("setup")
        return False
    
    try:
        # Phase 1: Move skills to vault
        moved_count, category_counts = migrate_skills(dry_run, config)
        
        if moved_count == 0:
            print_warning("No skills migrated. Migration complete (nothing to do).")
            if state and not dry_run:
                state.state['skill_count'] = 0
                state.mark_success()
            return True
        
        # Phase 2: Generate pointers
        if not generate_pointers(dry_run, config, state):
            if state:
                state.mark_failed("generate_pointers")
            return False
        
        # Phase 3: Clean up sources
        cleanup_skill_sources(dry_run)
        
        if not dry_run:
            # Save state
            if state:
                state.state['skill_count'] = moved_count
                state.state['original_sources'] = [str(s) for s in find_all_skill_sources()]
                state.mark_success()
            
            print_success(f"Migration complete! {moved_count} skills vaulted with ~{moved_count * 8} Level 1 tokens")
        else:
            print(f"\n[DRY RUN] Migration would move {moved_count} skills")
        
        return True
        
    except Exception as e:
        print_error(f"Migration failed: {e}")
        if state:
            state.mark_failed("exception")
        return False

def revert_migration(dry_run: bool = False, state: MigrationState = None):
    """Revert migration - restore all skills from vault to original sources."""
    print_header("Reverting Migration")
    
    if not HIDDEN_VAULT_DIR.exists():
        print_warning("Vault not found. Nothing to revert.")
        return
    
    # Get all skills from vault
    vault_skills = []
    for cat_dir in HIDDEN_VAULT_DIR.iterdir():
        if not cat_dir.is_dir():
            continue
        for skill_dir in cat_dir.iterdir():
            if skill_dir.is_dir() and is_skill_folder(skill_dir):
                vault_skills.append((skill_dir, cat_dir.name))
    
    if not vault_skills:
        print_warning("No skills found in vault.")
        return
    
    print(f"Found {len(vault_skills)} skills in vault to revert.\n")
    
    if not dry_run:
        # Remove all pointers from active skills dir
        removed_pointers = 0
        for item in ACTIVE_SKILLS_DIR.iterdir():
            if item.is_dir() and is_pointer_folder(item.name):
                shutil.rmtree(item)
                removed_pointers += 1
        print_success(f"Removed {removed_pointers} category pointers")
        
        # Restore each skill to its original source
        restored_count = 0
        for skill_path, category in vault_skills:
            # Try to restore to original location if we tracked it
            # For now, restore to ACTIVE_SKILLS_DIR (simpler)
            dest = ACTIVE_SKILLS_DIR / skill_path.name
            
            if dest.exists():
                shutil.rmtree(dest)
            
            try:
                shutil.move(str(skill_path), str(dest))
                restored_count += 1
                print(f"  Restored: {skill_path.name}")
            except Exception as e:
                print_error(f"Failed to restore {skill_path.name}: {e}")
        
        # Remove vault if empty
        try:
            if not any(HIDDEN_VAULT_DIR.iterdir()):
                shutil.rmtree(HIDDEN_VAULT_DIR)
                print_success("Removed empty vault")
        except:
            pass
        
        # Reset state
        if state:
            state.reset()
        
        print_success(f"Reverted {restored_count} skills to active skills directory")
    else:
        print(f"[DRY RUN] Would restore {len(vault_skills)} skills to active skills directory")
        print(f"[DRY RUN] Would remove {len(list(ACTIVE_SKILLS_DIR.glob('*-category-pointer')))} pointers")

def rebuild_pointers(dry_run: bool = False, config: dict = None, state: MigrationState = None):
    """Rebuild pointers from existing vault (useful after manual changes)."""
    print_header("Rebuilding Pointers")
    
    if not HIDDEN_VAULT_DIR.exists():
        print_warning("Vault not found. Run full migration first.")
        return False
    
    # Remove existing pointers
    if not dry_run:
        for item in ACTIVE_SKILLS_DIR.iterdir():
            if item.is_dir() and is_pointer_folder(item.name):
                shutil.rmtree(item)
        print_info("Removed existing pointers")
    
    return generate_pointers(dry_run, config, state)

def sync_new_skills(dry_run: bool = False, config: dict = None, state: MigrationState = None):
    """Sync new skills from source directories to vault."""
    print_header("Syncing New Skills")
    
    if not state.is_migrated():
        print_warning("Migration not complete. Run full migration first.")
        return False
    
    # Find skills in sources that are NOT yet in vault
    sources = find_all_skill_sources()
    new_skills = []
    
    for skill_path, source_dir in get_all_real_skills(sources):
        # Check if already in vault
        in_vault = False
        for cat_dir in HIDDEN_VAULT_DIR.iterdir():
            if cat_dir.is_dir() and (cat_dir / skill_path.name).exists():
                in_vault = True
                break
        if not in_vault:
            new_skills.append((skill_path, source_dir))
    
    if not new_skills:
        print_info("No new skills to sync.")
        return True
    
    print(f"Found {len(new_skills)} new skill(s) to sync.\n")
    
    moved_count = 0
    for skill_path, source_dir in new_skills:
        category = get_category_for_skill(skill_path.name, config)
        cat_dir = HIDDEN_VAULT_DIR / category
        dest = cat_dir / skill_path.name
        
        print(f"  {skill_path.name} -> {category}/")
        
        if not dry_run:
            try:
                cat_dir.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(skill_path), str(cat_dir))
                moved_count += 1
            except Exception as e:
                print_error(f"Failed to sync {skill_path.name}: {e}")
        else:
            moved_count += 1
    
    if not dry_run and moved_count > 0:
        # Rebuild ALL pointers to update counts (force refresh)
        success = rebuild_pointers(dry_run, config, state)
        if success:
            state.state['skill_count'] = state.state.get('skill_count', 0) + moved_count
            state.save()
            print_success(f"Synced {moved_count} new skill(s) and refreshed pointers")
        else:
            print_error("Failed to refresh pointers")
            return False
    
    return True

# ==========================================
# Utilities
# ==========================================

def validate_config():
    """Validate the configuration file."""
    print_header("Validating Configuration")
    try:
        config = load_config()
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        return False
    
    required_keys = ["categories", "keywords", "settings"]
    for k in required_keys:
        if k not in config:
            print_error(f"Missing required top-level key: {k}")
            return False
    
    # Check that all hierarchical categories have keyword definitions
    hierarchical = config["categories"].get("hierarchical", [])
    keywords = config.get("keywords", {})
    missing = [cat for cat in hierarchical if cat not in keywords]
    if missing:
        print_error(f"Missing keyword definitions for categories: {missing}")
        return False
    
    # Check for duplicate category names
    all_cats = hierarchical + config["categories"].get("flat", [])
    duplicates = set([c for c in all_cats if all_cats.count(c) > 1])
    if duplicates:
        print_error(f"Duplicate category names: {duplicates}")
        return False
    
    print_success("Configuration is valid.")
    return True

def list_skills(output_csv=None):
    """List all skills and their categories."""
    config = load_config()
    if not config:
        return
    
    state = MigrationState(STATE_FILE)
    
    # Use vault if migrated, otherwise scan sources
    if state.is_migrated() and HIDDEN_VAULT_DIR.exists():
        skills = []
        for cat_dir in HIDDEN_VAULT_DIR.iterdir():
            if cat_dir.is_dir() and not cat_dir.name.startswith('_'):
                for skill_dir in cat_dir.iterdir():
                    if skill_dir.is_dir() and is_skill_folder(skill_dir):
                        skills.append((skill_dir.name, cat_dir.name))
        skill_list = sorted(skills, key=lambda x: x[0])
    else:
        # Scan current sources
        sources = find_all_skill_sources()
        skill_folders = get_all_real_skills(sources)
        skill_list = [(path.name, get_category_for_skill(path.name, config)) for path, _ in skill_folders]
    
    if not skill_list:
        print_warning("No skills found.")
        return
    
    if output_csv:
        import csv
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Skill', 'Category'])
            for skill, cat in sorted(skill_list):
                writer.writerow([skill, cat])
        print_success(f"List written to {output_csv}")
    else:
        print(f"\n{'Skill':<40} | {'Category':<30}")
        print("-" * 72)
        for skill, cat in sorted(skill_list):
            skill_display = (skill[:37] + '...') if len(skill) > 40 else skill
            cat_display = (cat[:27] + '...') if len(cat) > 30 else cat
            print(f"{skill_display:<40} | {cat_display:<30}")
        print(f"\nTotal: {len(skill_list)} skills")

def show_stats():
    """Display category statistics."""
    print_header("Category Statistics")
    
    state = MigrationState(STATE_FILE)
    
    if state.is_migrated():
        print(f"{Colors.GREEN}Status: Migrated{Colors.ENDC}")
        print(f"  Last migrated: {state.state.get('migrated_at', 'Unknown')}")
    else:
        print(f"{Colors.YELLOW}Status: Not migrated{Colors.ENDC}")
    
    # Count skills by category from vault
    if HIDDEN_VAULT_DIR.exists():
        total = 0
        categories = []
        
        for cat_dir in sorted(HIDDEN_VAULT_DIR.iterdir()):
            if cat_dir.is_dir():
                count = len([d for d in cat_dir.iterdir() if is_skill_folder(d)])
                if count > 0:
                    total += count
                    categories.append((cat_dir.name, count))
        
        print(f"\n{'Category':<30} | {'Count':<8}")
        print("-" * 42)
        for cat, count in sorted(categories, key=lambda x: x[1], reverse=True):
            display = cat if len(cat) < 28 else cat[:25] + "..."
            print(f"{display:<30} | {count:<8}")
        print("-" * 42)
        print(f"{'Total':<30} | {total:<8}")
        
        # Token estimate
        pointer_count = len(list(ACTIVE_SKILLS_DIR.glob("*-category-pointer")))
        pointer_tokens = pointer_count * 8
        print(f"\nEstimated Level 1 tokens: ~{pointer_tokens}")
        print(f"Reduction vs 80,000: ~{100 - (pointer_tokens / 80000 * 100):.1f}%")
    else:
        print(f"\n{Colors.YELLOW}Vault not found. Run migration first.{Colors.ENDC}")

def check_health():
    """Check migration health."""
    print_header("Health Check")
    
    issues = []
    
    # Check directories
    if not ACTIVE_SKILLS_DIR.exists():
        issues.append("Active skills directory does not exist")
    
    if HIDDEN_VAULT_DIR.exists():
        # Count raw skills in sources (should be 0)
        sources = find_all_skill_sources()
        raw_skills = []
        for source in sources:
            for item in source.iterdir():
                if is_skill_folder(item):
                    raw_skills.append(item.name)
        
        if raw_skills:
            issues.append(f"Found {len(raw_skills)} raw skill(s) in source directories (should be only pointers)")
    else:
        issues.append("Vault does not exist")
    
    # Check state
    state = MigrationState(STATE_FILE)
    if not state.is_migrated():
        issues.append("Migration state shows not migrated")
    
    if issues:
        print(f"{Colors.FAIL}Issues found:{Colors.ENDC}")
        for issue in issues:
            print(f"  ✗ {issue}")
    else:
        print(f"{Colors.GREEN}No issues found. Migration is healthy.{Colors.ENDC}")

def print_banner():
    """Print SkillFlow banner."""
    banner_path = Path(__file__).parent / "banner.txt"
    try:
        with open(banner_path, 'r', encoding='utf-8') as f:
            banner = f.read()
        print(f"\n{Colors.BOLD}{Colors.CYAN}{banner}{Colors.ENDC}")
        print(f"{Colors.BLUE}  Infinite Context. Zero Token Tax.{Colors.ENDC}\n")
    except Exception:
        # Fallback if banner.txt missing
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("  ___ _   _ _ _ ___ _            ")
        print(" / __| |_(_) | | __| |_____ __ __")
        print(" \__ \ / / | | | _|| / _ \\ V  V / ")
        print(" |___/_\\_\\|_|_|_|_| |_\\___/ \\_/\\_/")
        print(f"{Colors.ENDC}")
        print(f"{Colors.BLUE}  Infinite Context. Zero Token Tax.{Colors.ENDC}\n")

# ==========================================
# Main Entry Point
# ==========================================

def main():
    """Main entry point."""
    print_banner()
    
    parser = argparse.ArgumentParser(
        description="SkillFlow - Smart Skill Organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                # Run full migration with confirmation
  python setup.py --dry-run      # Preview changes
  python setup.py --yes          # Skip confirmation prompt
  python setup.py --optimize     # Improve categorization
  python setup.py --status       # Show health status
  python setup.py --sync          # Add new skills without full rebuild
        """
    )
    
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild pointers from existing vault")
    parser.add_argument("--optimize", action="store_true", help="Recategorize skills with improved heuristics")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--status", action="store_true", help="Show health status")
    parser.add_argument("--revert", action="store_true", help="Revert migration")
    parser.add_argument("--validate", action="store_true", help="Validate configuration")
    parser.add_argument("--list", action="store_true", help="List all skills and their categories")
    parser.add_argument("--output", type=str, help="Output CSV file for --list")
    parser.add_argument("--sync", action="store_true", help="Sync new skills from sources to vault")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--vault-path", type=str, help="Custom vault path (overrides default)")
    parser.add_argument("--skills-path", type=str, help="Custom active skills path (overrides default)")
    
    args = parser.parse_args()
    
    # Allow custom paths
    global ACTIVE_SKILLS_DIR, HIDDEN_VAULT_DIR
    if args.vault_path:
        HIDDEN_VAULT_DIR = Path(args.vault_path).expanduser()
    if args.skills_path:
        ACTIVE_SKILLS_DIR = Path(args.skills_path).expanduser()
    
    # Load config
    try:
        config = load_config()
        if config is None:
            sys.exit(1)
    except SystemExit:
        return
    
    state = MigrationState(STATE_FILE)
    
    # Check for incomplete migration
    if state.has_incomplete_migration() and not (args.revert or args.rebuild):
        print(f"{Colors.YELLOW}Warning: Previous migration failed at '{state.state.get('failed_at')}'{Colors.ENDC}")
        print(f"  Use --rebuild to continue or --revert to undo\n")
    
    # Handle commands
    if args.stats:
        show_stats()
        return
    
    if args.status:
        check_health()
        print()
        show_stats()
        return
    
    if args.revert:
        revert_migration(args.dry_run, state)
        return
    
    if args.validate:
        validate_config()
        return
    
    if args.list:
        list_skills(args.output)
        return
    
    if args.sync:
        if not setup_directories(args.dry_run):
            return
        sync_new_skills(args.dry_run, config, state)
        return
    
    if args.optimize:
        # In future: re-categorize all skills in vault with new keywords
        print_warning("Optimize not yet implemented")
        return
    
    if args.rebuild:
        if not setup_directories(args.dry_run):
            return
        # First, ensure vault exists and has skills
        if not HIDDEN_VAULT_DIR.exists() or not any(HIDDEN_VAULT_DIR.iterdir()):
            print_warning("Vault is empty. Run full migration first.")
            return
        rebuild_pointers(args.dry_run, config, state)
        return
    
    # Default: full migration
    if not args.dry_run and not args.yes:
        # Show confirmation prompt
        sources = find_all_skill_sources()
        total_skills = sum(1 for _ in get_all_real_skills(sources))
        
        print(f"\n{Colors.BOLD}Migration Summary:{Colors.ENDC}")
        print(f"  Skill sources: {len(sources)}")
        for src in sources:
            count = sum(1 for p in src.iterdir() if is_skill_folder(p))
            print(f"    - {get_skill_source_name(src)}: {count} skills")
        print(f"  Total skills to migrate: {total_skills}")
        print(f"  Vault location: {HIDDEN_VAULT_DIR}")
        print(f"  Active pointers: {ACTIVE_SKILLS_DIR}")
        print()
        
        response = input(f"{Colors.YELLOW}Proceed with migration? (yes/no): {Colors.ENDC}").strip().lower()
        if response != 'yes':
            print("Migration cancelled.")
            return
    
    full_migration(args.dry_run, config, state)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Setup cancelled by user.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}An unexpected error occurred: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
