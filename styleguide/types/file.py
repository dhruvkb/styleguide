from __future__ import annotations

import difflib
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.text import Text

from styleguide.types.action import ScaffoldFileAction
from styleguide.types.status import ScaffoldFileStatus
from styleguide.utils.colors import color_gen
from styleguide.utils.fmt import normalize

if TYPE_CHECKING:
	from rich.console import Console

	from styleguide.types.repo import Repo


def _render_diff(current: str, proposed: str) -> Text:
	"""
	Get the diff between the current and proposed content.

	:param current: the current content of the file
	:param proposed: the proposed content of the file
	:return: a rich Text object with colored lines containing the diff
	"""
	out = Text()
	for line in difflib.unified_diff(
		current.splitlines(keepends=True),
		proposed.splitlines(keepends=True),
	):
		if line.startswith(("+++", "---")):
			continue

		if line.startswith("+"):
			out.append(line, style="green")
		elif line.startswith("-"):
			out.append(line, style="red")
		elif line.startswith("@@"):
			out.append(line, style="dim")
		else:
			out.append(line, style="dim")
	return out


class ScaffoldFile:
	"""
	Represents a template file in the system.
	"""

	def __init__(self, repo: Repo, template_path: Path):
		self.repo = repo
		self.template_path = template_path

	@cached_property
	def template_file_name(self) -> str:
		"""
		Return just the file name of the template file.
		"""
		return self.template_path.name

	@cached_property
	def target_relative_path(self) -> Path:
		"""
		Return the path to the target file that the template creates relative to
		the repo root.
		"""
		return Path(*self.template_file_name.removesuffix(".j2").split("__"))

	@cached_property
	def target_path(self) -> Path:
		"""
		Return the path to the target file that the template creates.
		"""
		return self.repo.path / self.target_relative_path

	@cached_property
	def target_file_name(self) -> str:
		"""
		Get just the name part of the target file.
		"""
		return self.target_path.name

	@cached_property
	def current_content(self) -> str | None:
		"""
		Get the current content of the target file, or `None` if it does not
		already exist.
		"""

		if self.target_path.exists():
			return self.target_path.read_text()
		return None

	@cached_property
	def normalized_current_content(self) -> str | None:
		"""the current content, passed through the formatter"""
		if self.current_content is None:
			return None

		return normalize(
			self.repo.path,
			self.target_relative_path,
			self.current_content,
		)

	@cached_property
	def rendered_content(self) -> str:
		"""
		Render the template file and return the content.
		"""

		template = self.repo.jinja_env.get_template(self.template_file_name)
		return template.render(**self.repo.context)

	@cached_property
	def normalized_rendered_content(self) -> str:
		"""
		The rendered content passed through the target's formatter, i.e. what the
		repo's own hooks would produce. This is what `sync` writes so the file
		does not immediately drift on the next formatting pass.
		"""

		return normalize(
			self.repo.path,
			self.target_relative_path,
			self.rendered_content,
		)

	@cached_property
	def status(self) -> ScaffoldFileStatus:
		"""
		Return the status of the scaffold file.

		A file is up to date when it matches the render either verbatim or after
		both sides are run through the target's formatter. Normalising both sides
		absorbs formatter reflow (e.g. `oxfmt` collapsing an array) that would
		otherwise report an eternal, cosmetic drift.
		"""

		if not self.target_path.exists():
			return ScaffoldFileStatus.DOES_NOT_EXIST
		if self.rendered_content == self.current_content:
			return ScaffoldFileStatus.UP_TO_DATE
		if self.normalized_rendered_content == self.normalized_current_content:
			return ScaffoldFileStatus.UP_TO_DATE
		return ScaffoldFileStatus.OUT_OF_SYNC

	# Renderables
	# ===========

	@cached_property
	def display_diff(self) -> Panel | None:
		"""
		Return a unified diff between the current and rendered content, or
		`None` if the file is up to date.
		"""

		if self.status == ScaffoldFileStatus.UP_TO_DATE:
			return None

		accent = next(color_gen)
		return Panel(
			_render_diff(
				self.current_content or "",
				self.normalized_rendered_content,
			),
			title=f"[bold {accent}]{self.target_relative_path}[/bold {accent}]",
			title_align="left",
			border_style=accent,
		)

	# Actions
	# =======

	def sync(
		self,
		console: Console,
		show_diff: bool,
		assume_yes: bool,
	) -> ScaffoldFileAction:
		"""
		Perform an action to sync the scaffold file to its target, with options
		to show a diff and get the user's confirmation. Return what action was
		performed for summarisation.
		"""

		if (diff := self.display_diff) is None:
			return ScaffoldFileAction.UNCHANGED

		if show_diff or not assume_yes:
			# Even if the user asks not to see the diff, we have to show it if
			# we want to ask for confirmation.
			console.print(diff)

		if not assume_yes:
			confirm = console.input(f"Write {self.target_relative_path}? \\[y/N] ")
			if confirm.lower() != "y":
				return ScaffoldFileAction.REJECTED

		is_preexisting = self.target_path.is_file()
		if not is_preexisting:
			self.target_path.parent.mkdir(parents=True, exist_ok=True)
		self.target_path.write_text(self.normalized_rendered_content)
		if is_preexisting:
			return ScaffoldFileAction.UPDATED
		return ScaffoldFileAction.CREATED
