#!/usr/bin/env python3
"""
SkillFlow Test Script

Validates that the SkillFlow migration is working correctly.
Run from the project root: python test_skillflow.py
"""

import json
import os
import sys
from pathlib import Path

def print_pass(msg):
    print(f"[PASS] {msg}")

def print_fail(msg):
    print(f"[FAIL] {msg}")
    return False

def print_warn(msg):
    print(f"[WARN] {msg}")

def find_active_dir():
    """Find the active skills directory"""
    home = Path.home()
    possible = [
        home / '.opencode' / 'skills',
        home / '.config' / 'opencode' / 'skills',
    ]
    for p in possible:
        if p.exists():
            return p
    return None

def find_vault_dir():
    """Find the vault directory"""
    home = Path.home()
    possible = [
        home / '.opencode-skill-libraries',
        home / '.opencode' / 'skill-libraries',
    ]
    for p in possible:
        if p.exists():
            return p
    return None

def test_pointer_count(active_dir):
    """Test that category pointers exist"""
    # Count folders that are not the index file and not hidden
    pointers = [d for d in active_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    expected_min = 10  # At least a few categories
    if len(pointers) >= expected_min:
        print_pass(f"Found {len(pointers)} category pointer folders")
        return True
    else:
        return print_fail(f"Expected at least {expected_min} pointers, found {len(pointers)}")

def test_index_exists(active_dir):
    """Test that SKILL_INDEX.json exists and is valid"""
    index_path = active_dir / 'SKILL_INDEX.json'
    if not index_path.exists():
        return print_fail("SKILL_INDEX.json not found")
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print_pass(f"SKILL_INDEX.json exists and is valid JSON ({len(data)} skills)")
        return data
    except json.JSONDecodeError as e:
        return print_fail(f"SKILL_INDEX.json is not valid JSON: {e}")

def test_vault_structure(vault_dir, expected_categories):
    """Test that vault has expected category structure"""
    if not vault_dir.exists():
        return print_fail(f"Vault directory not found: {vault_dir}")

    vault_subdirs = [d.name for d in vault_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    missing = set(expected_categories) - set(vault_subdirs)
    if missing:
        print_warn(f"Missing categories in vault: {missing}")
    else:
        print_pass(f"Vault contains all {len(expected_categories)} expected top-level categories")

    # Count total skills in vault (top-level only)
    skill_count = sum(1 for d in vault_dir.rglob('SKILL.md') if d.is_file())
    if skill_count >= 100:
        print_pass(f"Vault contains {skill_count} skills")
    else:
        print_warn(f"Vault only contains {skill_count} skills (expected >100)")
    return True

def test_state_file():
    """Test that state file exists if migration was run"""
    state_path = Path.home() / '.skillflow-state.json'
    if state_path.exists():
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            print_pass(f"State file exists (last operation: {state.get('last_operation', 'unknown')})")
            return True
        except json.JSONDecodeError:
            print_warn("State file exists but is not valid JSON (maybe migration never completed)")
            return True
    else:
        print_warn("No state file found - run migration first or ignore if you haven't migrated yet")
        return True

def main():
    print("=== SkillFlow Validation Test ===\n")

    active_dir = find_active_dir()
    if not active_dir:
        return print_fail("Could not find active skills directory. Check your OpenCode installation.")
    print(f"Active skills dir: {active_dir}")

    vault_dir = find_vault_dir()
    if not vault_dir:
        print_warn("Vault directory not found. Skills may not have been migrated yet.")
    else:
        print(f"Vault dir: {vault_dir}")

    results = []

    # Test 1: Index
    index_data = test_index_exists(active_dir)
    results.append(index_data is not None)

    # Test 2: Pointer count
    results.append(test_pointer_count(active_dir))

    # Test 3: Vault structure
    if vault_dir:
        expected_cats = ['frontend', 'backend', 'database', 'ai', 'testing', 'devops', 'security']
        results.append(test_vault_structure(vault_dir, expected_cats))

    # Test 4: State file
    results.append(test_state_file())

    print("\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    status = "ALL TESTS PASSED" if passed == total else "SOME TESTS FAILED"
    print(f"{passed}/{total} test groups passed - {status}")

    if passed == total:
        print("\nAll tests passed! SkillFlow is working correctly.")
        return 0
    else:
        print("\nSome tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
