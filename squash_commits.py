#!/usr/bin/env python
"""
Script to automatically squash commits between release tags.

This script will:
1. Analyze commit history between release tags on the main branch
2. Create a new squashed branch with one commit per release tag
3. Use changelog entries as commit descriptions
4. Preserve original tag dates in squashed commits
5. Preserve unreleased commits after the last tag

WARNING: This will create new commits and does not rewrite history in place.
It is safer than interactive rebase for large changes.
"""

import subprocess
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict, Optional


def run_git(
    args: List[str], cwd: Path = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a git command and return the result."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=check,
            cwd=cwd
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {' '.join(args)}")
        print(f"Error: {e.stderr}")
        return None


def get_release_tags(cwd: Path) -> List[str]:
    """Get all release tags sorted by version."""
    result = run_git(["git", "tag", "-l"], cwd=cwd, check=False)
    if not result or not result.stdout:
        return []

    tags = [line.strip() for line in result.stdout.split("\n") if line.strip()]

    # Parse and sort versions
    def parse_version(tag: str) -> Tuple[int, int, int, str]:
        match = re.search(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", tag)
        if match:
            major = int(match.group(1)) or 0
            minor = int(match.group(2)) if match.group(2) else 0
            patch = int(match.group(3)) if match.group(3) else 0
            return (major, minor, patch, tag)
        return (0, 0, 0, tag)

    return sorted(tags, key=parse_version)


def parse_changelog(changelog_path: Path) -> Dict[str, str]:
    """
    Parse CHANGELOG.md and extract version entries.
    
    Returns a dict mapping version (e.g., 'v1.0.0') to changelog content.
    """
    changelog_entries = {}
    
    if not changelog_path.exists():
        return changelog_entries
    
    with open(changelog_path, 'r') as f:
        content = f.read()
    
    # Split by version headers (## vX.Y.Z pattern)
    version_pattern = r'^## (v?\d+\.\d+\.\d+(?:-\w+\d*)?)'
    matches = list(re.finditer(version_pattern, content, re.MULTILINE))
    
    for i, match in enumerate(matches):
        version = match.group(1)
        # Normalize version key (ensure v prefix)
        if not version.startswith('v'):
            version_key = f"v{version}"
        else:
            version_key = version
        
        # Get content from this version to the next
        start = match.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(content)
        
        entry_content = content[start:end].strip()
        # Clean up: remove the section marker line if present
        lines = entry_content.split('\n')
        cleaned_lines = [l for l in lines if l.strip() and not l.startswith('##')]
        changelog_entries[version_key] = '\n'.join(cleaned_lines).strip()
    
    return changelog_entries


def get_commits_between_tags(from_tag: str, to_tag: str, cwd: Path) -> List[str]:
    """Get commit hashes between two tags."""
    result = run_git(
        ["git", "rev-list", "--count", f"{from_tag}..{to_tag}"], cwd=cwd, check=False
    )
    if not result or not result.stdout:
        return []

    count = int(result.stdout.strip())
    if count == 0:
        return []

    result = run_git(
        ["git", "rev-list", "--oneline", "--no-merges", f"{from_tag}..{to_tag}"],
        cwd=cwd,
        check=False,
    )
    if not result or not result.stdout:
        return []

    commits = [line for line in result.stdout.split("\n") if line]
    return commits


def create_squashed_history(cwd: Path) -> bool:
    """
    Create a squashed history with one commit per release tag.

    This script:
    1. Gets all release tags
    2. For each tag, creates a commit representing all changes up to that tag
    3. Uses changelog entries as commit messages
    4. Preserves original tag dates in the squashed commits
    5. Preserves unreleased commits after the last tag

    Returns True on success, False on failure.
    """
    print("=" * 80)
    print("SQUASHING COMMITS BETWEEN RELEASE TAGS")
    print("=" * 80)

    # Get tags
    tags = get_release_tags(cwd)

    if not tags:
        print("No release tags found.")
        return False

    print(f"\nFound {len(tags)} release tags:")
    for tag in tags:
        print(f"  - {tag}")

    # Parse changelog
    changelog_path = cwd / "CHANGELOG.md"
    changelog_entries = parse_changelog(changelog_path)
    print(f"\nParsed changelog with {len(changelog_entries)} entries")

    # Create backup branch first
    backup_branch = "rebase-backup"
    result = run_git(["git", "branch", "-D", backup_branch], cwd=cwd, check=False)
    if result and result.returncode == 0:
        print(f"\nDeleted existing backup branch '{backup_branch}'")

    result = run_git(["git", "branch", backup_branch], cwd=cwd, check=False)
    if not result or result.returncode != 0:
        print(f"Error creating backup branch: {backup_branch}")
        return False

    # Preserve original state on backup
    result = run_git(["git", "checkout", backup_branch], cwd=cwd, check=False)
    if not result or result.returncode != 0:
        print("Error switching to backup branch")
        return False

    print(f"\nSwitched to backup branch '{backup_branch}' - preserving all history")

    # Create squashed history on a new branch
    squashed_branch = "squashed-history"

    # Checkout orphan branch (completely new history)
    result = run_git(["git", "checkout", "--orphan", squashed_branch], cwd=cwd, check=False)
    if not result or result.returncode != 0:
        print(f"Error creating orphan branch '{squashed_branch}'")
        return False

    # Remove all files from staging
    result = run_git(["git", "rm", "-rf", "."], cwd=cwd, check=False)

    print(f"\nCreated new squashed history branch: '{squashed_branch}'")

    # Process each tag
    for i, tag in enumerate(tags):
        print(f"\n{'-' * 80}")
        print(f"Processing: {tag}")

        # Get the tree object at this tag (all files at that point)
        result = run_git(["git", "checkout", tag, "--", "."], cwd=cwd, check=False)
        if not result or result.returncode != 0:
            print(f"  Error checking out files from {tag}")
            return False

        # Get the date of the tag
        result = run_git(["git", "log", "-1", "--format=%aI", tag], cwd=cwd, check=False)
        tag_date = result.stdout.strip() if result else ""

        # Get changelog entry for this version
        changelog_msg = changelog_entries.get(tag, "")
        if not changelog_msg:
            print(f"  Warning: No changelog entry found for {tag}")
            changelog_msg = "(No changelog entry)"

        # Create commit message: tag as title, changelog as body
        message = tag
        if changelog_msg:
            message += f"\n\n{changelog_msg}"

        # Add and commit with original date
        result = run_git(["git", "add", "-A"], cwd=cwd, check=False)
        
        commit_args = ["git", "commit", "-m", message, "--author=p-vdp <peter@corbelspatial.com>"]
        if tag_date:
            commit_args.extend(["--date", tag_date])
        
        result = run_git(commit_args, cwd=cwd, check=False)
        if not result or result.returncode != 0:
            # If no changes, skip
            if "nothing to commit" not in result.stderr.lower():
                print(f"  Warning: commit failed - {result.stderr if result else 'unknown error'}")

        print(f"  Committed {tag} (date: {tag_date[:10] if tag_date else 'unknown'})")

    # Handle unreleased commits (from last tag to HEAD on backup)
    print(f"\n{'-' * 80}")
    print("Processing unreleased commits")
    
    result = run_git(["git", "checkout", backup_branch], cwd=cwd, check=False)
    if not result or result.returncode != 0:
        print("Error checking out backup branch to get unreleased changes")
        return False
    
    # Get the unreleased commits
    result = run_git(["git", "rev-list", "--oneline", f"{tags[-1]}..HEAD"], cwd=cwd, check=False)
    unreleased_commits_str = result.stdout.strip() if result else ""
    
    if unreleased_commits_str:
        unreleased_commits = [line.split()[0] for line in unreleased_commits_str.split('\n') if line.strip()]
        print(f"Found {len(unreleased_commits)} unreleased commit(s):")
        for commit in unreleased_commits:
            result = run_git(["git", "log", "-1", "--format=%s", commit], cwd=cwd, check=False)
            commit_msg = result.stdout.strip() if result else ""
            print(f"  - {commit} {commit_msg}")
        
        # Switch back to squashed-history and get unreleased files
        result = run_git(["git", "checkout", squashed_branch], cwd=cwd, check=False)
        if result and result.returncode == 0:
            # Checkout files from HEAD of backup branch
            result = run_git(["git", "checkout", backup_branch, "--", "."], cwd=cwd, check=False)
            if result and result.returncode == 0:
                result = run_git(["git", "add", "-A"], cwd=cwd, check=False)
                
                # Build commit message from unreleased commits
                commit_msg = ""
                for commit in unreleased_commits:
                    result = run_git(["git", "log", "-1", "--format=%B", commit], cwd=cwd, check=False)
                    if result and result.stdout.strip():
                        commit_msg += f"{result.stdout.strip()}\n\n"
                
                if not commit_msg:
                    commit_msg = f"Unreleased changes ({len(unreleased_commits)} commits)"
                
                result = run_git(
                    ["git", "commit", "-m", commit_msg, "--author=p-vdp <peter@corbelspatial.com>"],
                    cwd=cwd,
                    check=False,
                )
                if result and result.returncode == 0:
                    print(f"  Committed unreleased changes")
                else:
                    print(f"  Warning: Failed to commit unreleased changes")
    else:
        print("No unreleased commits found")

    print(f"\n{'-' * 80}")
    print("Squashed history created successfully!")
    print(f"\nCompare branches:")
    print(f"  Backup (full history):   {backup_branch}")
    print(f"  Squashed (new history):  {squashed_branch}")
    print(f"\nUse this command to view the squashed history with dates:")
    print(f"  git log --format='%h %ad %s' --date=short {squashed_branch}")
    print(f"  git log --oneline --date=short --graph {squashed_branch}")

    print(f"\nUse this command to compare with original:")
    print(f"  git diff {squashed_branch}...{backup_branch} --stat")

    print(f"\n{'-' * 80}")
    print("IMPORTANT NOTES:")
    print(f"  1. The squashed branch has {len(tags)} release commits (one per tag)")
    print(f"  2. Unreleased commits have been combined into one final commit")
    print(f"  3. Original tag dates are preserved in commit timestamps")
    print(f"  4. Commit messages use changelog entries from CHANGELOG.md")
    print(f"  5. Commits authored by p-vdp <peter@corbelspatial.com>")
    print(f"  6. DO NOT push to any remote without ensuring team agreement")
    print(f"  7. Use 'git push --force-with-lease' only if you understand the consequences")
    print(f"  8. The backup branch preserves full history if needed")

    return True


def main():
    """Main entry point."""
    cwd = Path.cwd()

    print("=" * 80)
    print("GIT COMMIT SQUASHING SCRIPT")
    print("=" * 80)
    print()
    print("This script will create a NEW branch with squashed history.")
    print("It will NOT rewrite history in place.")
    print()
    print("Current directory:", cwd)
    print()

    # Check if we're on main branch
    result = run_git(["git", "branch", "--show-current"], cwd=cwd, check=False)
    if not result or not result.stdout:
        print("Warning: Could not determine current branch")
    else:
        current_branch = result.stdout.strip()
        print(f"Current branch: {current_branch}")

        if current_branch != "main":
            print(f"\nWarning: You are on '{current_branch}', not 'main'")
            print(
                "Please switch to 'main' before squashing, or create squashed branch from here"
            )

    print("\nOptions:")
    print("  1. Automatic squashing (create_squashed_history)")
    print("  2. Exit")

    print("\nEnter your choice (1 or 2): ", end="")

    while True:
        choice = input().strip()

        if choice == "1":
            print("\nRunning automatic squashing...")
            success = create_squashed_history(cwd)
            if success:
                print("\nSquashing complete!")
            else:
                print("\nSquashing failed. Check for conflicts and resolve them.")
            return 0 if success else 1

        elif choice == "2":
            print("Exiting.")
            return 0

        else:
            print("Invalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    sys.exit(main())
