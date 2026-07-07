from __future__ import annotations

from enum import StrEnum


class ScaffoldFileStatus(StrEnum):
	DOES_NOT_EXIST = "does not exist"  # remedial action: create
	OUT_OF_SYNC = "out of sync"  # remedial action: update
	UP_TO_DATE = "up to date"  # remedial action: none

	@property
	def color(self) -> str:
		color_map = {
			ScaffoldFileStatus.DOES_NOT_EXIST: "red",
			ScaffoldFileStatus.OUT_OF_SYNC: "yellow",
			ScaffoldFileStatus.UP_TO_DATE: "green",
		}
		return color_map[self]

	@property
	def glyph(self) -> str:
		glyph_map = {
			ScaffoldFileStatus.DOES_NOT_EXIST: "✗",
			ScaffoldFileStatus.OUT_OF_SYNC: "≠",
			ScaffoldFileStatus.UP_TO_DATE: "✓",
		}
		return glyph_map[self]

	@property
	def display_value(self) -> str:
		return f"[{self.color}]{self.value}[/{self.color}]"

	@property
	def display_glyph(self) -> str:
		return f"[{self.color}]{self.glyph}[/{self.color}]"
