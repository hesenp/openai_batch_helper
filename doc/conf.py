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

html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#e02424",
        "color-brand-content": "#c81e1e",
        "color-background-primary": "#f7f7f8",
        "color-background-secondary": "#ededf0",
        "color-foreground-primary": "#1f2024",
        "color-foreground-secondary": "#2c2f36",
        "color-sidebar-background": "#f1f2f4",
        "color-sidebar-search-background": "#e7e8ec",
        "color-inline-code-background": "#f0edee",
    },
    "dark_css_variables": {
        "color-brand-primary": "#ff4d4f",
        "color-brand-content": "#ff6b6b",
        "color-background-primary": "#111217",
        "color-background-secondary": "#16181f",
        "color-foreground-primary": "#f4f5f7",
        "color-foreground-secondary": "#d3d4d9",
        "color-sidebar-background": "#12141a",
        "color-sidebar-search-background": "#1a1d24",
        "color-inline-code-background": "#1e2028",
    },
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]

