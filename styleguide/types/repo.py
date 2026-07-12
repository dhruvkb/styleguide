from __future__ import annotations

import re
import subprocess
from functools import cached_property
from typing import TYPE_CHECKING, Any

from rich.box import ROUNDED
from rich.table import Table

from styleguide.catalog import MANAGED_SCAFFOLDING, VALIDATED_SCAFFOLDING
from styleguide.types.action import ScaffoldFileAction
from styleguide.types.file import ScaffoldFile, ScaffoldFileStatus
from styleguide.types.manifest import Manifest
from styleguide.utils.jinja import jinja_env

if TYPE_CHECKING:
	from collections.abc import Sequence
	from pathlib import Path

	from jinja2 import Environment
	from rich.console import Console, RenderableType
	from rich.panel import Panel

	from styleguide.types.validators import Validator

LANGUAGE_EXTENSIONS: dict[str, set[str]] = {
	"python": {"py"},
	"javascript": {"js", "mjs", "vue", "astro"},
	"typescript": {"ts", "mts", "vue", "astro"},
	"rust": {"rs"},
	"markdown": {"md", "mdx"},
	"toml": {"toml"},
	"json": {"json"},
	"css": {"css"},
	"html": {"html", "htm"},
}

REMOTE = re.compile(r"github.com[:/](?P<owner>[^/]*)/(?P<repo>[^.]*)(\.git)?")


class Repo:
	"""
	Represents a repository being scaffolded.
	"""

	def __init__(self, path: Path):
		self.raw_path = path
		self.path = path.expanduser().resolve()

		if not self.sg_dir.is_dir():
			raise ValueError(f"No `.sg` directory in {self.path}")

	@cached_property
	def sg_dir(self) -> Path:
		"""the path to the `.sg` directory in the repository"""

		return self.path / ".sg"

	@cached_property
	def jinja_env(self) -> Environment:
		"""Jinja2 environment for this repo's templates"""

		return jinja_env(self.sg_dir)

	@cached_property
	def scaffold_files(self) -> list[ScaffoldFile]:
		"""the `.sg` templates in this repo"""

		return sorted(
			(
				ScaffoldFile(self, item)
				for item in sorted(self.sg_dir.glob("*.j2"))
				if item.is_file()
			),
			key=lambda f: f.target_path,
		)

	@cached_property
	def manifest(self) -> Manifest:
		"""the parsed `sg/sg.toml` manifest for this repo"""

		return Manifest.from_repo(self)

	@cached_property
	def git_files(self) -> list[str]:
		"""list of all files in the repo according to `git`"""

		result = subprocess.run(
			["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
			capture_output=True,
			text=True,
			check=True,
			cwd=self.path,
		)
		return [name for name in result.stdout.split("\0") if name]

	@cached_property
	def exts(self) -> set[str]:
		"""set of all file extensions (no dot) in the repo"""

		exts: set[str] = set()
		for name in self.git_files:
			base = name.rsplit("/", 1)[-1]
			stem, dot, ext = base.rpartition(".")
			key = ext if (dot and stem) else base
			exts.add(key)
		return exts

	@cached_property
	def detected_languages(self) -> list[str]:
		"""inferred list of languages from the list of extensions"""

		exts_present = set(self.exts)
		return sorted(
			lang for lang, exts in LANGUAGE_EXTENSIONS.items() if exts & exts_present
		)

	@cached_property
	def origin_url(self) -> str | None:
		"""the URL of the `origin` remote"""

		try:
			result = subprocess.run(
				["git", "config", "--get", "remote.origin.url"],
				capture_output=True,
				text=True,
				check=True,
				cwd=self.path,
			)
		except subprocess.CalledProcessError:
			return None
		url = result.stdout.strip()
		return url or None

	@cached_property
	def gh_owner_and_name(self) -> tuple[str, str] | None:
		"""repo owner and repo name on GitHub, derived from the `origin` remote"""

		if not self.origin_url:
			return None
		if match := REMOTE.search(self.origin_url):
			return match.group("owner"), match.group("repo")
		return None

	@cached_property
	def display_name(self) -> str:
		"""the display name of the repo"""

		if self.manifest.display_name:
			return self.manifest.display_name
		if self.gh_owner_and_name:
			return self.gh_owner_and_name[1]
		return self.path.name

	@cached_property
	def root_package_managers(self) -> list[str]:
		"""the package managers detected in the repo"""

		lock_files = {
			"pnpm-lock.yaml": "pnpm",
			"uv.lock": "uv",
			"Cargo.lock": "cargo",
		}
		return [
			manager
			for lock_file, manager in lock_files.items()
			if (self.path / lock_file).exists()
		]

	@cached_property
	def is_pnpm_workspace(self) -> bool:
		"""whether this repo is a pnpm workspace"""

		workspace_file = self.path / "pnpm-workspace.yaml"
		if not workspace_file.exists():
			return False

		content = workspace_file.read_text()
		return "packages:" in content

	@cached_property
	def frameworks(self) -> list[str]:
		"""the frameworks detected in the repo"""

		frameworks: list[str] = []
		if "astro" in self.exts:
			frameworks.append("astro")
		if "vue" in self.exts:
			frameworks.append("vue")
		if "mdx" in self.exts:
			frameworks.append("mdx")
		return frameworks

	@cached_property
	def context(self) -> dict[str, Any]:
		"""the Jinja render context for this repo's templates"""

		languages = (
			self.manifest.languages
			if self.manifest.languages is not None
			else self.detected_languages
		)

		return {
			"exts": self.exts,
			"languages": languages,
			"frameworks": self.frameworks,
			"display_name": self.display_name,
			"gh_owner_and_name": self.gh_owner_and_name,
			"package_managers": self.root_package_managers,
			"is_pnpm_workspace": self.is_pnpm_workspace,
		}

	@cached_property
	def present_scaffold_files(
		self,
	) -> tuple[dict[str, Path], dict[str, tuple[Path, Sequence[Validator] | None]]]:
		"""the list of existing scaffolding file that could be managed by `sg`"""

		entries = MANAGED_SCAFFOLDING
		managed = {
			entry: hit for entry in entries if (hit := self.path / entry).exists()
		}
		entries = VALIDATED_SCAFFOLDING
		validated = {
			entry: (hit, validators)
			for entry, validators in entries.items()
			if (hit := self.path / entry).exists()
		}
		return managed, validated

	@cached_property
	def unmanaged_files(self) -> dict[str, Path]:
		"""the list of scaffolding files not generated by a `.sg` template"""

		managed = {file.target_path for file in self.scaffold_files}  # absolute paths
		exempt = self.manifest.exempt  # relative paths
		present, _ = self.present_scaffold_files  # relative paths: absolute paths
		return {
			key: value
			for key, value in present.items()
			if key not in exempt and value not in managed
		}

	@cached_property
	def has_drift(self) -> bool:
		"""whether any of the `.sg` templates are out of sync with their targets"""

		return any(
			file.status is not ScaffoldFileStatus.UP_TO_DATE
			for file in self.scaffold_files
		)

	# Renderables
	# ===========

	@cached_property
	def display_unmanaged_files(self) -> list[str]:
		"""the displayable list of unmanaged files"""

		output: list[str] = []
		if self.unmanaged_files:
			output.append("[bold magenta]Unmanaged files:[/bold magenta]")
			output.extend(f"[magenta]![/magenta] {key}" for key in self.unmanaged_files)
		return output

	# Actions
	# =======

	def display_status(
		self,
		*,
		show_diff: bool,
		show_only_drifts: bool,
	) -> list[RenderableType]:
		"""
		Display the status of the repo's managed files and list the unmanaged
		files.

		This has stong parallels to the `perform_sync` method.

		This is the code that powers the `status` subcommand for the CLI.
		"""

		diffs: list[Panel] = []
		output: list[RenderableType] = []

		table = Table(
			header_style="bold",
			title_justify="left",
			box=ROUNDED,
		)
		table.add_column("File", no_wrap=True)
		table.add_column("Status")
		for file in self.scaffold_files:
			if (file.status is ScaffoldFileStatus.UP_TO_DATE) and show_only_drifts:
				# The user does not want to see up-to-date files.
				continue

			if show_diff and (diff := file.display_diff):
				diffs.append(diff)

			table.add_row(
				str(file.target_relative_path),
				f"{file.status.display_glyph} {file.status.display_value}",
			)

		if show_diff and diffs:
			output.extend(diffs)
			output.append("")  # blank line after diffs, before managed files

		output.append("[bold cyan]Managed files:[/bold cyan]")
		output.append(table)

		if unmanaged_output := self.display_unmanaged_files:
			output.append("")  # blank line after managed files, before unmanaged files
			output.extend(unmanaged_output)

		return output

	def perform_sync(
		self,
		*,
		assume_yes: bool,
		show_diff: bool,
		console: Console,
	) -> list[RenderableType]:
		"""
		Sync the repo's managed files to their targets and list a disclaimer for
		the unmanaged files.

		This has strong parallels to the `display_status` method.

		This is the code that powers the `sync` subcommand for the CLI.
		"""
		any_diff = False
		output: list[RenderableType] = []

		table = Table(
			header_style="bold",
			title_justify="left",
			box=ROUNDED,
		)
		table.add_column("File", no_wrap=True)
		table.add_column("Action")
		for file in self.scaffold_files:
			action = file.sync(
				assume_yes=assume_yes,
				show_diff=show_diff,
				console=console,
			)
			if action is not ScaffoldFileAction.UNCHANGED:
				any_diff = True
			table.add_row(
				str(file.target_relative_path),
				f"{action.display_glyph} {action.display_value}",
			)

		if any_diff and (show_diff or not assume_yes):
			output.append("")  # blank line after diffs, before managed files

		output.append("[bold cyan]Managed files:[/bold cyan]")
		output.append(table)

		if unmanaged_output := self.display_unmanaged_files:
			output.append("")  # blank line after managed files, before unmanaged files
			output.extend(unmanaged_output)
			output.append("Unmanaged files cannot be synced, by definition.")

		return output

	def perform_validation(
		self, *, show_only_fails: bool
	) -> tuple[list[RenderableType], int]:
		"""
		Validate the repo's validation-only scaffolding.
		"""

		output: list[RenderableType] = []

		any_failures = False

		_, present = self.present_scaffold_files
		for rel_path, (abs_path, validators) in present.items():
			table = Table(
				header_style="bold",
				title_justify="left",
				box=ROUNDED,
			)
			table.add_column("Test", no_wrap=True)
			table.add_column("Outcome")
			table.add_column("Message", no_wrap=True)
			for validator in validators or []:
				name = getattr(validator, "__name__", "operation")
				is_suppressed = name in self.manifest.suppressions
				try:
					validator(self, abs_path)
					if not show_only_fails:
						table.add_row(name, "[green]✓[/green]", "")
				except AssertionError as e:
					if not is_suppressed:
						any_failures = True
					if not is_suppressed or not show_only_fails:
						table.add_row(
							name,
							"[yellow]![/yellow]" if is_suppressed else "[red]✗[/red]",
							str(e),
						)
			if table.row_count > 0:
				output.append(f"[bold cyan]{rel_path}[/bold cyan]")
				output.append(table)
				output.append("")  # blank line after each file's output

		return output, 1 if any_failures else 0
