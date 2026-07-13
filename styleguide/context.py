"""Render data and template-global helpers for a repo.

`build_context` returns repo-specific *data*. `python_version` and
`resolve_license` are *helpers* registered as Jinja globals (see Task 6), so
they are invoked only when a template references them.
"""

from __future__ import annotations

import json
import re
import subprocess
from importlib.metadata import version
from pathlib import Path

import platformdirs
import requests


def styleguide_version() -> str:
	"""Get this package's own version, e.g. for pinning its own `prek` hooks."""
	return version("styleguide")


def _self_license() -> Path:
	"""Locate this project's own license.

	In a built wheel the root `LICENSE` is force-included as package data at
	`styleguide/assets/LICENSE` (see `pyproject.toml`). In the source tree, it
	lives at the repo root, one level above this package.
	"""
	packaged = Path(__file__).resolve().parent / "assets" / "LICENSE"
	if packaged.is_file():
		return packaged
	return Path(__file__).resolve().parents[1] / "LICENSE"


def remote_owner_repo(repo_path: Path) -> tuple[str | None, str | None]:
	"""`(owner, name)` from the `origin` remote, or `(None, None)`."""
	try:
		result = subprocess.run(
			["git", "-C", str(repo_path), "config", "--get", "remote.origin.url"],
			capture_output=True,
			text=True,
			check=True,
		)
	except subprocess.CalledProcessError, FileNotFoundError:
		return None, None
	url = result.stdout.strip()
	if not url:
		return None, None
	if url.startswith("git@") and ":" in url:
		path = url.split(":", 1)[1]
	elif "github.com/" in url:
		path = url.split("github.com/", 1)[1]
	else:
		return None, None
	path = path.removesuffix(".git")
	if "/" not in path:
		return None, None
	owner, name = path.rsplit("/", 1)
	return owner, name


def npm_version(package: str) -> dict[str, int]:
	"""
	Get the latest version of a package from npmjs.com.
	"""

	res = requests.get(f"https://registry.npmjs.org/{package}/latest")
	res.raise_for_status()
	data = res.json()
	version = data.get("version")
	if not version or not re.match(r"^\d+\.\d+\.\d+$", version):
		raise RuntimeError(f"unexpected {package} version format: {version!r}")
	major, minor, patch = map(int, version.split("."))
	return {"major": major, "minor": minor, "patch": patch}


def python_version() -> dict[str, int]:
	"""
	Get the version parts of the latest stable CPython from `uv python list`.
	"""
	try:
		result = subprocess.run(
			["uv", "python", "list", "--output-format", "json"],
			capture_output=True,
			check=True,
			text=True,
		)
		data = json.loads(result.stdout)
		preference = next(
			item
			for item in data
			if item["implementation"] == "cpython"
			and item["variant"] == "default"
			and re.match(r"^\d+\.\d+\.\d+$", item["version"])
		)
		parts = preference["version_parts"]
		return {k: int(parts[k]) for k in ("major", "minor", "patch")}
	except (FileNotFoundError, subprocess.CalledProcessError) as ex:
		raise RuntimeError("could not run `uv python list`; is uv installed?") from ex
	except StopIteration as ex:
		raise RuntimeError("no stable CPython version found via uv") from ex


def resolve_license(code: str) -> str:
	"""
	Get the license text.

	The first time this is invoked for any specific license code, it fetches the
	license text from GitHub, except for "gpl-3.0" for which it returns its own
	license.

	The license text is cached as per `platformdirs`, which respects the env var
	`$XDG_CACHE_HOME` on macOS.
	"""
	if code == "gpl-3.0":
		return _self_license().read_text().rstrip("\n")

	cache_dir = Path(platformdirs.user_cache_dir("styleguide")) / "licenses"
	cached = cache_dir / f"{code}.txt"
	if cached.is_file():
		return cached.read_text()

	response = requests.get(f"https://api.github.com/licenses/{code}", timeout=30)
	response.raise_for_status()
	data = response.json()
	if "body" not in data:
		raise RuntimeError(f"license API response for {code!r} had no body")
	body = data["body"]

	cache_dir.mkdir(parents=True, exist_ok=True)
	cached.write_text(body)

	return body


def indent_block(value: str, width: str = "\t") -> str:
	"""Indent every non-blank line of a template block, first line included.

	Unlike Jinja's built-in `indent`, a blank/empty block renders to `""`
	rather than a lone `width` — an overridden-but-empty block otherwise leaves
	a stray indent on the following line.
	"""
	if not value.strip():
		return ""
	return "\n".join(width + line if line else line for line in value.split("\n"))
