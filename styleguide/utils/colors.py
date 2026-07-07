from __future__ import annotations

from itertools import cycle
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Iterator


ANSI_COLORS = [
	"blue",
	"green",
	"yellow",
	"red",
	"magenta",
	"cyan",
]


def _get_color() -> Iterator[str]:
	"""Yield a color from ANSI_COLORS in a round-robin fashion."""
	yield from cycle(ANSI_COLORS)


color_gen = _get_color()
