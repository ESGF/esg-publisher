Troubleshooting & Tips
======================

If you encounter issues running any of the esgcet commands, try looking for common issues:
 - If you encounter issues processing arguments (variables are undefined but you included them either in the command line or ini file), try checking your ini file for
   syntax issues. The error messages should be clear for the most part, but for variable issues the config file is a good place to start.
 - If the program fails to create the dataset, check to see if autocurator exited without error.
 - If you are using a custom project and encounter errors, try using the individual commands one at a time instead of ``esgpublish``. If your project requires customization,
   feel free to open a github issue and request that support for your project is added.
 - For example commands and test scripts, see our `test suite repository <https://github.com/lisi-w/test-suite/tree/main>`_.
 - For unexpected behavior, output, or errors, please open a `Github Issue <https://github.com/ESGF/esg-publisher/issues>`_.
