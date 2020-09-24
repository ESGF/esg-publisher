Autocurator
===========

Install
-------

If you do not wish to install autocurator via conda, the option also exists to clone and install it from git::

    git clone http://github.com/sashakames/autocurator.git
    cd autocurator
    make

After running this, there should be an autocurator executable saved as ``.../autocurator/bin/autocurator``.
You will need to update the config if you choose to do this with the correct path to the autocurator folder, as the default is just the ``autocurator`` command.

Running Autocurator
-------------------

If you want to run ``autocurator`` as a stand alone, use the following format::

    bash autocurator.sh <path to autocurator executable> <full mapfile path> <scan file name (output file)>

The executable itself can also be run like so::

    bin/autocurator --out_pretty --out_json <scan file name> --files <dataset directory>

However, this mode is sometimes difficult as specifying multiple files requires using a ``dir/*.nc`` format which sometimes causes issues.
Overall, we recommend using the script above as it cleans up a few things. You can also use the conda install as above, but the path/command will just be "autocurator".
Once you have your scan file, you can use that to run ``esgmkpubrec`` (see that page for more info).