.. _readthedocs.org: http://www.readthedocs.org

**************************
GLPI Sphinx Theme
**************************

.. contents::

GLPI Sphinx theme based on readthedocs.org_ one.


Installation
============

Via package
-----------

Download the package or add it to your ``requirements.txt`` file:

.. code:: bash

   pip install sphinx_glpi_theme

In your ``conf.py`` file:

.. code:: python

    import sphinx_glpi_theme

    html_theme = "glpi"

    html_theme_path = sphinx_glpi_theme.get_html_themes_path()

Via git or download
-------------------

Symlink or subtree the ``sphinx_glpi_theme/glpi`` repository into your documentation at
``docs/_themes/sphinx_glpi_theme`` then add the following two settings to your Sphinx
conf.py file:

.. code:: python

    html_theme = "sphinx_glpi_theme"
    html_theme_path = ["_themes", ]
