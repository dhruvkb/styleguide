from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from styleguide.types.repo import Repo

MANIFEST_NAME = "sg.toml"


@dataclass
class Manifest:
	"""Represents the `sg.toml` manifest file in a repo."""

	repo: Repo
	languages: list[str] | None = None  # None → auto-detect
	exempt: list[str] = field(default_factory=list)
	display_name: str | None = None
	suppressions: list[str] = field(default_factory=list)

	@staticmethod
	def from_repo(repo: Repo) -> Manifest:
		manifest = repo.sg_dir / MANIFEST_NAME
		if not manifest.is_file():
			return Manifest(repo=repo)  # default manifest

		data = tomllib.loads(manifest.read_text())
		return Manifest(
			repo=repo,
			languages=data.get("languages"),
			exempt=list(data.get("exempt", [])),
			display_name=data.get("display_name"),
			suppressions=list(data.get("suppressions", [])),
		)
