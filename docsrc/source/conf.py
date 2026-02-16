# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os, sys, datetime, re
from functools import reduce
from sphinx.util import logging
_mainDir = reduce(lambda x,y: os.path.dirname( x ),
                  range(2), os.path.abspath('.'))
sys.path.insert( 0, _mainDir )

logger = logging.getLogger( __name__ )
logger.debug( "mainDir = %s" % _mainDir)


# -- Project information -----------------------------------------------------

project = 'howdy_grabbag'
copyright = '2022, Tanim Islam'
author = 'Tanim Islam'

tls_verify = True

# The full version, including alpha/beta/rc tags
release = '0.5'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.mathjax',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinxcontrib.youtube',
    'sphinx_issues',
    'sphinxarg.ext',
]

#
## following instructions here (https://github.com/svenevs/exhale/tree/master/docs/_intersphinx) to fix beautifulsoup doc.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'requests': ( 'https://requests.readthedocs.io/en/latest', None),
    'beautifulsoup' : ( 'https://www.crummy.com/software/BeautifulSoup/bs4/doc', "_intersphinx/bs4_objects.inv"),
    'geoip2' : ( 'https://geoip2.readthedocs.io/en/latest', None),
    'gmusicapi' : ( 'https://unofficial-google-music-api.readthedocs.io/en/latest', None ),
    'cinemagoer' : ( 'https://cinemagoer.readthedocs.io/en/latest', None),
    'pyqt5' : ( 'https://www.riverbankcomputing.com/static/Docs/PyQt5', "_intersphinx/pyqt5_objects.inv" ),
    'requests_oauthlib' : ( 'https://requests-oauthlib.readthedocs.io/en/latest', None ),
    'oauth2client' : ( 'https://oauth2client.readthedocs.io/en/latest', None ),
    'google-auth' : ( 'https://google-auth.readthedocs.io/en/latest', None ),
    'deluge' : ( 'https://deluge.readthedocs.io/en/latest', None ),
    'transmission_rpc' : ( 'https://transmission-rpc.readthedocs.io/en/stable', None ),
    'plexapi' : ( 'https://python-plexapi.readthedocs.io/en/latest', None ),
    'sqlalchemy' : ( 'https://docs.sqlalchemy.org', None ),
    'subliminal' : ( 'https://subliminal.readthedocs.io/en/latest/', None ),
    'musicbrainzngs' : ( 'https://python-musicbrainzngs.readthedocs.io/en/latest', None ),
    'pillow' : ( 'https://pillow.readthedocs.io/en/stable', None ),
    'pandas' : ( 'http://pandas.pydata.org/pandas-docs/stable', None ),
}


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

#
## numfig stuff
numfig = True


#
## GitHub repo
issues_github_path = "tanimislam/howdy"

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_sidebars = {
   '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
   'using/windows': ['windowssidebar.html', 'searchbox.html'],
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'custom.css',
]
