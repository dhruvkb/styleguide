import subprocess
from typing import TYPE_CHECKING

from identify import identify
from rich.console import Console

if TYPE_CHECKING:
	from pathlib import Path

err_console = Console(stderr=True)


# Taken from the Oxc compatibility list: https://oxc.rs/compatibility.html
OXFMT_TYPES = [
	"javascript",
	"ts",
	"vue",
	"css",
	"html",
	"json",
	"yaml",
	"markdown",
	"mdx",
	"toml",
]


def normalize(repo: Path, path: Path, content: str) -> str:
	"""
	Get the Oxfmt-formatted version of the content.

	This function returns the content unchanged if Oxfmt does not handle it.

	:param repo: the path to the repo root
	:param path: the path to the target file
	:param content: the current content of the file
	:return: the formatted content of the file
	"""

	try:
		path_types = identify.tags_from_path(str(path))
	except ValueError:
		return content

	if not path_types & set(OXFMT_TYPES):
		return content

	try:
		result = subprocess.run(
			["pnpm", "--silent", "oxfmt", f"--stdin-filepath={path}"],
			input=content,
			capture_output=True,
			text=True,
			cwd=repo,
			check=True,
		)
		return result.stdout
	except OSError:
		# The formatter is not available.
		return content
	except subprocess.CalledProcessError as e:
		if stderr := (e.stderr or "").strip():
			# The formatter raised an error.
			err_console.print(
				f"[red]oxfmt could not format[/red] [bold]{path}[/bold]"
				f"[red]; using unformatted content.[/red]"
			)
			err_console.print(f"[dim]{stderr}[/dim]")

		# The formatter is not available.
		return content
