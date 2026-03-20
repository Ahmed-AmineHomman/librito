"""Minimal Sphinx configuration for the Librito documentation."""

from pathlib import Path
import re
import tomllib


ROOT_DIR = Path(__file__).resolve().parent.parent
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"
LICENSE_PATH = ROOT_DIR / "LICENSE"

with PYPROJECT_PATH.open("rb") as pyproject_file:
    pyproject = tomllib.load(pyproject_file)

license_text = LICENSE_PATH.read_text(encoding="utf-8")
match = re.search(r"^Copyright \(c\) (?P<notice>.+)$", license_text, re.MULTILINE)
if match is None:
    raise ValueError("Could not extract the copyright notice from LICENSE.")

project_metadata = pyproject["project"]
project = project_metadata["name"]
author = project_metadata["authors"][0]["name"]
copyright = match.group("notice")

extensions = []
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

root_doc = "index"
html_theme = "sphinx_rtd_theme"
