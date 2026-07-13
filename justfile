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

	pnpm prek install --hook-type pre-commit --hook-type pre-push

alias i := install

# Lint
# ====

# Run one, or all, of `prek`'s hooks on specific, or all, files.
lint hook="" *files="":
	pnpm prek run {{ hook }} {{ if files == "" { "--all-files" } else { "--files" } }} {{ files }}

alias l := lint

# Development
# ===========

# Get an interactive shell with the project environment loaded.
shell:
	uv run ipython

# Run the program in development mode.
run *args:
	uv run sg {{ args }}

alias r := run

# Place the project on `$PATH` as a `uv` tool named `sg`.
self-install:
	uv tool install --editable .

alias s := self-install

# Release
# =======

# Bump the version and create a release commit and tag.
bump part="minor":
	uv version --bump {{ part }}
	git add -p pyproject.toml uv.lock
	git commit -m "Bump version to $(uv version --short)"
	git tag -s v$(uv version --short) -m "Release v$(uv version --short)"

alias B := bump
