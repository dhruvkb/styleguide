from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pathlib import Path

	from styleguide.types.repo import Repo


def assert_logo_is_present_in_readme_assets(repo: Repo, hit: Path) -> None:
	logo_path = repo.path / "readme_assets" / "logo.png"
	if not logo_path.exists():
		raise AssertionError("Logo should be present at `readme_assets/logo.png`.")


def assert_logo_is_referenced_in_readme(repo: Repo, hit: Path) -> None:
	first_line = hit.read_text().splitlines()[0]
	if "readme_assets/logo.png" not in first_line:
		raise AssertionError("Logo should be referenced in `README.md`.")


def assert_logo_does_not_use_raw_githubusercontent(repo: Repo, hit: Path) -> None:
	first_line = hit.read_text().splitlines()[0]
	if "raw.githubusercontent.com" in first_line:
		raise AssertionError("Logo should be a `github.com` URL.")


def assert_readme_has_display_name(repo: Repo, hit: Path) -> None:
	first_line = hit.read_text().splitlines()[0]
	display_name = repo.display_name
	if display_name not in first_line:
		raise AssertionError("`README.md` should contain the repo's display name.")


validations = [
	assert_logo_is_present_in_readme_assets,
	assert_logo_is_referenced_in_readme,
	assert_logo_does_not_use_raw_githubusercontent,
	assert_readme_has_display_name,
]
