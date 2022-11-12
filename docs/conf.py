import sys
from pathlib import Path

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

sys.path.append(str(Path('..', 'polyfile').resolve()))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Polyfile'
copyright = '2022, Yuriy Makarov'
author = 'Yuriy Makarov'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx_toolbox.confval',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'bizstyle'
html_static_path = ['_static']
html_sidebars = {
    "index": ['localtoc.html', 'relations.html', 'project.html', 'searchbox.html'],
    '**': ['localtoc.html', 'relations.html', 'searchbox.html'],
}
html_context = {
    'project_links': [
        ('Source Code', 'https://github.com/FeroxTL/polyfile'),
        ('Issue Tracker', 'https://github.com/FeroxTL/polyfile/issues/'),
    ]
}
