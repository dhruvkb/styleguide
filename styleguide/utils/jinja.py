from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from styleguide.context import (
	indent_block,
	npm_version,
	python_version,
	resolve_license,
	styleguide_version,
)
from styleguide.utils.fmt import OXFMT_TYPES

BASE_TEMPLATES_PATH = Path(__file__).resolve().parents[1] / "templates"


def jinja_env(templates_path: Path) -> Environment:
	"""
	Create a fully-configured Jinja2 environment for rendering templates.

	This overrides many defaults to make it suitable for use with scaffolding-
	related templates, such as the use of `<<` and `>>` for variables and the
	customised line-statements that match the language's comments.

	:param templates_path: the path to the templates directory within the repo
	:return: a fully-configured Jinja2 `Environment` instance
	"""

	env = Environment(
		loader=FileSystemLoader(
			[
				templates_path,
				BASE_TEMPLATES_PATH,
			]
		),
		autoescape=False,
		keep_trailing_newline=True,
		trim_blocks=True,
		lstrip_blocks=True,
		# We use "<<" and ">>" because "{{" and "}}" are used by `justfile`.
		variable_start_string="<<",
		variable_end_string=">>",
	)
	env.globals["oxfmt_types"] = OXFMT_TYPES  # ty: ignore[invalid-assignment]
	env.globals["python_version"] = python_version  # ty: ignore[invalid-assignment]
	env.globals["npm_version"] = npm_version  # ty: ignore[invalid-assignment]
	env.globals["license"] = resolve_license  # ty: ignore[invalid-assignment]
	env.globals["styleguide_version"] = styleguide_version  # ty: ignore[invalid-assignment]
	env.filters["indent_block"] = indent_block
	return env
