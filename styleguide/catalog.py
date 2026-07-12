"""The curated catalog of known scaffolding files (`scaffolding.txt`)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from styleguide.validators.readme_md import validations as readme_md_validations

if TYPE_CHECKING:
	from collections.abc import Sequence

	from styleguide.types.validators import Validator

MANAGED_SCAFFOLDING = [
	# Core files
	"LICENSE",
	# Git management
	".gitignore",
	"prek.toml",
	# Tools
	"justfile",
	# Editor
	".editorconfig",
	".vscode/settings.json",
	".vscode/extensions.json",
	# Toolchain pins
	".node-version",
	".python-version",
	# Linting / formatting
	".oxlintrc.json",
	".oxfmtrc.json",
	"eslint.config.mjs",
	".prettierrc.json",
	".prettier.ignore",
	".rustfmt.toml",
	".ruff.toml",
]

VALIDATED_SCAFFOLDING: dict[str, Sequence[Validator] | None] = {
	# Core files
	"README.md": readme_md_validations,
	# Manifest files
	"package.json": None,
	"pyproject.toml": None,
	"Cargo.toml": None,
	# Package manager config
	"pnpm-workspace.yaml": None,
	# TypeScript
	"tsconfig.json": None,
}
