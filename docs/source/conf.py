# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Order Website'
copyright = '2025, Artem Tanchenko'
author = 'Artem Tanchenko'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',  # підтримка Google/NumPy стилю
    'sphinx.ext.viewcode',  # кнопка "подивитися код"
    'sphinx_autodoc_typehints',  # автоматично додає типи
]

templates_path = ['_templates']
exclude_patterns = []

language = 'ukr'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

import os
import sys
import django

sys.path.insert(0, os.path.abspath('../..'))  # шляхи до твого проекту
os.environ['DJANGO_SETTINGS_MODULE'] = 'bakery_order_system.settings'  # заміни на свій
django.setup()