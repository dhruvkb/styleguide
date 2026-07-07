set dotenv-load := false

# @ toggles quieting at the recipe-level. Without quiet, each commands is
#   printed to STDERR before execution.
# _ marks a recipe as private and stops it from appearing in `just --list` or
#   `just --summary`.

# Show all available recipes.
@_default:
	just --list --unsorted

# Print the given text with an equal number of `=` characters below it.
@_section text:
	printf "\n{{ text }}\n"
	printf "%0.s=" $(seq 1 $(printf "%s" "{{ text }}" | wc -c))
	printf "\n"

# Setup
# =====

# Install dependencies.
install:
	uv sync
	pnpm i

	just prek install --hook-type pre-commit --hook-type pre-push

alias i := install

# Lint
# ====

# This abstracts the underlying provisioning of `prek` through the appropriate
# package manager (which may be pnpm, or even uv or Cargo).
#
# Run `prek` commands through package manager.
prek *args:
	pnpm prek {{ args }}

# Run one, or all, of `prek`'s hooks on specific, or all, files.
lint hook="" *files="":
	just prek run {{ hook }} {{ if files == "" { "--all-files" } else { "--files" } }} {{ files }}

alias l := lint

# Development
# ===========

# Get an interactive shell with the project environment loaded.
shell:
	uv run ipython

# Run the project in development mode.
run *args:
	uv run sg {{ args }}

alias r := run

# Place the project on `$PATH` as a `uv` tool named `sg`.
self-install:
	uv tool install --editable .

alias s := self-install

# Release
# =======

# Tag a commit with a version number ('v' will be prefixed automatically)
release version commit="":
	git tag -a v{{ version }} -m "Release v{{ version }}" {{ commit }}

alias R := release
