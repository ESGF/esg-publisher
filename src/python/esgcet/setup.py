#!/usr/bin/env python
    
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

import sys, os, subprocess, re

MIN_PG_VERSION = (8,0)                  # Minimum postgres version
MIN_XML2_VERSION = (2,6,21)             # Minimum libxml2 version
MIN_XSLT_VERSION = (1,1,15)             # Minimum libxslt version

match_libfile_version = re.compile(r'([.0-9]+)').search

def tryint(s):
    try:
        return int(s)
    except ValueError:
        return s

def run_config(ex, a):
    try:
        config = subprocess.Popen([ex, a], stdout=subprocess.PIPE)
    except OSError, e:
        print 'Error running %s %s'%(ex, a)
        print 'Make sure that %s is in your path, then rerun setup.py'%ex
        sys.exit(1)
    out = config.stdout.readlines()
    return out

def check_version(ex, vers, minvers):
    vers = vers.strip()
    match = match_libfile_version(vers)
    if match is not None:
        version = tuple(map(tryint, match.group(1).split('.')))
        if version<minvers:
            raise RuntimeError("Found %s version %s, must be at least %s"%(ex, `vers`, `minvers`))
        else:
            print "Found %s version %s >= %s: OK"%(ex, vers, minvers)
    else:
        print "Could not find %s version in string '%s'"%(ex, vers)

pgvers = run_config("pg_config", "--version")
xml2vers = run_config("xml2-config", "--version")
xsltvers = run_config("xslt-config", "--version")
check_version("Postgres", pgvers[0], MIN_PG_VERSION)
check_version("libxml2", xml2vers[0], MIN_XML2_VERSION)
check_version("libxslt", xsltvers[0], MIN_XSLT_VERSION)

# Set the version string in esgcet.esgcet.__init__.py
v = file(os.path.join(os.path.dirname(__file__), 'esgcet', '__init__.py'))
VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(v.read()).group(1)
v.close()
print "esgcet version =", VERSION

setup(
    name = 'esgcet',
    version = VERSION,
    description = 'ESGCET publication package',
    author = 'Sasha Ames',
    author_email = 'ames4@llnl.gov',
    url = 'http://esgf.llnl.gov',
    install_requires = [
        "psycopg2>=2.0,<2.7",
        "SQLAlchemy>0.5.3,<1.3",
        "lxml>=2.0",
        "sqlalchemy_migrate>=0.6,<0.12",
        "requests>=2.20.0",
        "MyProxyClient>=2.1.0",
        "esgf-pyclient>=0.1.8",
        "esgfpid>=0.7.12",
        "cdf2cim>=0.3.3.0",
    ],
    setup_requires = [
        "psycopg2>=2.0,<2.7",
        "SQLAlchemy>0.5.3,<1.3",
        "lxml>=2.0",
        "sqlalchemy_migrate>=0.6,<0.12",
        "requests>=2.20.0",
    ],
    packages = find_packages(exclude=['ez_setup']),
    include_package_data = True,
    # test_suite = 'nose.collector',
    # Install the CF standard name table, ESG init file, etc.
    package_data = {
        'esgcet.config.etc': ['*.ini', '*.xml', '*.txt', '*.tmpl'],
        'esgcet.ui': ['*.gif'],
        'esgcet.schema_migration': ['migrate.cfg'],
        'esgcet.schema_migration.versions': ['*.sql'],
    },
    scripts = [
        'scripts/esgcheck_times',
        'scripts/esgextract',
        'scripts/esgcopy_files',
        'scripts/esgcreate_tables',
        'scripts/esgdrop_tables',
        'scripts/esginitialize',
        'scripts/esglist_datasets',
        'scripts/esglist_files',
        'scripts/esgpublish_gui',
        'scripts/esgsetup',
        'scripts/esgpublish',
        'scripts/esgquery_gateway',
        'scripts/esgquery_index',
        'scripts/esgunpublish',
        'scripts/esgupdate_metadata',
        'scripts/esgadd_facetvalues',
        'scripts/esgfind_excludes',
        'scripts/esgtest_publish',
        'scripts/meta_synchro.py',
        'scripts/gen_versions.py',
        'scripts/hsils.py',
        'scripts/ls.py',
        'scripts/msls.py',
        'scripts/srmls.py',
    ],
    zip_safe = False,                   # Migration repository must be a directory
    entry_points = """
      [esgcet.project_handlers]
      handler_dictionary = esgcet.config:builtinProjectHandlers
      [esgcet.format_handlers]
      handler_dictionary = esgcet.config:builtinFormatHandlers
      [esgcet.metadata_handlers]
      handler_name = cf_builtin
      handler = esgcet.config:CFHandler
      """,
)



