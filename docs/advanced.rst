.. _advanced:

Advanced Usage and Publication Tools
====================================

esgadd_facetvalues
******************

This is a command-line utility that allows for the addition of supplemental faceted metadata beyond the values in the dataset_id and global attributes.  The command runs with similar options as esgpublish and is intended to run as a repeat of the --thredds catalog generation step.

Requirements
------------

A "dataset metadata" mapfile must be produced to call the utility.  The mapfile takes the form:

::

	<dataset_id> | <key>=<value> | ...

Where the <dataset_id>s are the same as those found in the mapfile produced by esgprep and used with esgpublish.  The subsequent columns store the key=value pairs for the supplementary facets.

Usage
-----

::

	$ esgadd_facetvalues --project <project> --mapfile <dataset_mapfile> --noscan --thredds --service fileservice

