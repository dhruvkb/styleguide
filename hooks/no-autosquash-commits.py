#!/usr/bin/env python3
"""Reject pushes containing autosquash (fixup!/squash!/amend!) commits."""

import os
import subprocess
import sys

PREFIXES = ("fixup!", "squash!", "amend!")


def is_null(sha: str) -> bool:
	# The all-zeros null OID marks a created/deleted ref. Its length varies by
	# hash algorithm (40 for SHA-1, 64 for SHA-256), so match on content.
	return bool(sha) and set(sha) == {"0"}


def main() -> int:
	# prek/pre-commit consume git's pre-push stdin themselves and expose the
	# range via env vars, invoking the hook once per pushed ref.
	from_ref = os.environ.get("PRE_COMMIT_FROM_REF", "")
	to_ref = os.environ.get("PRE_COMMIT_TO_REF", "")

	if not to_ref or is_null(to_ref):  # nothing to push, or a branch deletion
		return 0
	if not from_ref or is_null(from_ref):  # new branch: commits not on any remote
		rev_range = [to_ref, "--not", "--remotes"]
	else:  # existing branch: only the commits being added
		rev_range = [f"{from_ref}..{to_ref}"]

	result = subprocess.run(
		["git", "rev-list", *rev_range, "--format=%s", "--no-commit-header"],
		capture_output=True,
		text=True,
		check=True,
	)
	offenders = [s for s in result.stdout.splitlines() if s.startswith(PREFIXES)]
	if not offenders:
		return 0

	sys.stderr.write("Push rejected: autosquash commits found:\n")
	for subject in offenders:
		sys.stderr.write(f"  ✕ {subject}\n")
	sys.stderr.write("Run 'git rebase -i --autosquash' first.\n")
	return 1


if __name__ == "__main__":
	raise SystemExit(main())
