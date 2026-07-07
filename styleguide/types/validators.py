from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable
	from pathlib import Path

	from styleguide.types.repo import Repo

	Validator = Callable[[Repo, Path], None]
