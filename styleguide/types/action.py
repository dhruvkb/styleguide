from __future__ import annotations

from enum import StrEnum


class ScaffoldFileAction(StrEnum):
	CREATED = "created"
	UPDATED = "updated"
	REJECTED = "rejected"
	UNCHANGED = "unchanged"

	@property
	def color(self) -> str:
		color_map = {
			ScaffoldFileAction.UNCHANGED: "dim",
			ScaffoldFileAction.CREATED: "blue",
			ScaffoldFileAction.UPDATED: "green",
			ScaffoldFileAction.REJECTED: "red",
		}
		return color_map[self]

	@property
	def glyph(self) -> str:
		glyph_map = {
			ScaffoldFileAction.UNCHANGED: "=",
			ScaffoldFileAction.CREATED: "*",
			ScaffoldFileAction.UPDATED: "✓",
			ScaffoldFileAction.REJECTED: "✗",
		}
		return glyph_map[self]

	@property
	def display_value(self) -> str:
		return f"[{self.color}]{self.value}[/{self.color}]"

	@property
	def display_glyph(self) -> str:
		return f"[{self.color}]{self.glyph}[/{self.color}]"
