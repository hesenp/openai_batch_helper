from __future__ import annotations

import os
import sys
from datetime import datetime

project = "openai-batch-helper"
author = "hesenp"
copyright = f"{datetime.now():%Y}, {author}"

# Ensure package is importable when building docs
sys.path.insert(0, os.path.abspath(".."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autodoc_typehints = "description"
autodoc_class_signature = "separated"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns: list[str] = []

try:
    html_theme = "furo"
except Exception:  # pragma: no cover - fallback for environments without furo
    html_theme = "alabaster"
html_static_path = ["_static"]

