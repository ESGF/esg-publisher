#The ESGF Publication Test Suite

##Introduction - why build a test suite?

Everyone who has come into contact with ESGF knows that it is a complicated system. There are many components within a node, many nodes at a given site and many sites federated across the globe. This complexity leads to inter-dependencies between sub-systems.

Sometimes a node manager will need to reverse or change an action. The desired state of the system is sometimes hard to predict depending on how the she goes about the task. Publication is a typical sub-system in which there are many different tasks that can be performed in different sequences.

One way to counter the inherent unpredictability of the publication process is to develop a test suite that can be run by any node manager to check that a set of prescribed tasks generates a consistent outcome. This document outlines a plan for developing the ESGF Publication Test Suite.

##Existing Publisher Testing Code?

There is only sparse test code in the ESGF stack. Gavin Bell previous wrote a single java class:

  https://github.com/ESGF/esg-publisher/blob/master/src/java/test/esg/node/publisher/connector/ESGPublisherTest.java

This was not well developed with only about 60 lines of actual code. We are not aware of it being functional.

You can ask to publish a test file with:

    $ esg-node --test-pub

But this is mainly broken.

##Existing documentation?

There is a Documentation directory at:

  https://github.com/ESGF/esg-publisher/tree/master/docs

This directory contains two files but no significant documentation.

##Pre-conditions for an ESGF Publication Test Suite

The following pre-conditions are required for the Test Suite:

1. File sets of test data
  * We can use real netcdf files that we have modified
  * We should reduce the resolution so the suite is small
  * These should cover at least 2 projects and 2 publication units
    * Including at least 2 versions of one publication unit
2. Pre-generated mapfile templates:
  * These will point to (1) but will include a {{ BASEDIR }} section that must be replaced by the real path on the local node.
3. Pre-generated ESGF config file set
4. Pre-generated policies file (maps users/roles to which data can be published)

##The Test Suite

The following tests should cover all the workflows required to be able to successfully publish and unpublish datasets to ESGF. This includes handling versions of the same publication unit.

###Test 0: Verify empty

Verify dv1, dv2 not present in db, TDS, Solr. Other tests below, where not explicitly listed as extending other tests, implicitly extend test 0.

###Test 1: Publish dataset

 * Publish dv1 to db.
   * Verify dv1 in db.
 * Publish dv1 to TDS.
   * Verify dv1 in TDS.
 * Publish dv1 to Solr.
   * Verify dv1 in Solr.
   * Verify consistency of dv1 in Solr, TDS, versioning and file contents.

###Test 2: Publish second version of dataset [Extends: Test 1]
 * Publish dv2 to db.
   * Verify dv2 in db.
 * Publish dv2 to TDS.
   * Verify dv2 in TDS.
 * Publish dv2 to Solr.
   * Verify dv2 in Solr.
   * Verify consistency of dv2 in Solr, TDS, versioning and file contents.

 * Verification checks on dv1:
   * Verify dv1 in db.
   * Verify dv1 in TDS.
   * Verify dv1 in Solr.
   * Verify consistency of dv1 in Solr, TDS, versioning and file contents.

###Test 3: Publish “all” datasets in stages

This is a special test in which all datasets are published at each stage. Success in this test requires overcoming a current problem with the ESG Publisher code. The problem was that the publisher was hard-coded to always use the most recent version in the postgres db.

 * Publish all datasets and versions to db.
   * Verify all datasets and versions in db.
 * Publish all datasets and versions to TDS.
   * Verify all datasets and versions in TDS.
 * Publish all datasets and versions to Solr.
   * Verify all datasets and versions in Solr.
   * Verify consistency of all datasets in Solr, TDS, versioning and file contents.

###Test 4: Publish “all” datasets in stages in reverse order

 * Publish all datasets and versions to db in reverse order.
   * Verify all datasets and versions in db.
 * Publish all datasets and versions to TDS in reverse order.
   * Verify all datasets and versions in TDS.
 * Publish all datasets and versions to Solr in reverse order.
   * Verify all datasets and versions in Solr.
   * Verify consistency of all datasets in Solr, TDS, versioning and file contents.

###Test 5: Unpublish sole version [Extends: Test 1]

Run test 1.

 * Unpublish dv1 from Solr.
   * Verify dv1 removed from Solr.
 * Unpublish dv1 from TDS.
   * Verify dv1 removed from TDS.
 * Unpublish dv1 from db.
   * Verify dv1 removed from db.

###Test 6: Unpublish latest version of multi-version dataset [Extends: Test 2]

Run test 2.

 * Unpublish dv2 from Solr.
   * Verify dv2 removed from Solr.
   * Verify dv1 in db, TDS and Solr.
   * Verify consistency of dv1 in Solr, TDS, versioning and file contents.
 * Unpublish dv2 from TDS.
   * Verify dv2 removed from TDS.
   * Verify dv1 in db, TDS and Solr.
   * Verify consistency of dv1 in Solr, TDS, versioning and file contents.
 * Unpublish dv2 from db.
   * Verify dv2 removed from db.
   * Verify dv1 in db, TDS and Solr.
   * Verify consistency of dv1 in Solr, TDS, versioning and file contents.

###Test 7: Unpublish old version of multi-version dataset [Extends: Test 2]

Run test 2.

 * Unpublish dv1 from Solr.
   * Verify dv1 removed from Solr.
   * Verify dv2 in db, TDS and Solr.
   * Verify consistency of dv2 in Solr, TDS, versioning and file contents.
 * Unpublish dv1 from TDS.
   * Verify dv1 removed from TDS.
   * Verify dv2 in db, TDS and Solr.
   * Verify consistency of dv2 in Solr, TDS, versioning and file contents.
 * Unpublish dv1 from db.
   * Verify dv1 removed from db.
   * Verify dv2 in db, TDS and Solr.
   * Verify consistency of dv2 in Solr, TDS, versioning and file contents.

###Test 8: Generate mapfiles

 * Generate mapfiles.
   * Verify mapfiles exist and are formatted correctly.

###Test 9: Parallel publication

This test explores whether it is safe to publish in parallel.

 * Publish all datasets and versions to db at the same time.
   * Verify all datasets and versions in db.

 * Publish all datasets and versions to TDS at the same time.
   * Verify all datasets and versions in TDS.

 * Publish all datasets and versions to Solr at the same time.
   * Verify all datasets and versions in Solr.
   * Verify consistency of all datasets in Solr, TDS, versioning and file contents.

###Test 10: Parallel publication of multi-version dataset

This test explores whether it is safe to publish multiple versions of a dataset at the same time. This checks that the code doesn’t get confused when a new version is appearing in the system (e.g. in the db) whilst a process is running.

 * Publish multiple versions to db at the same time.
   * Verify all versions in db.
 * Publish multiple versions to TDS at the same time.
   * Verify all versions in TDS.
 * Publish multiple versions to Solr at the same time.
   * Verify all versions in Solr.
   * Verify consistency of all versions in Solr, TDS, versioning and file contents.

###Test 11: Stress testing parallel publication

Run parallel publication varying the number of parallel processes to determine the maximum number of concurrent processes that it is safe to run.

 * Run tests 9, 10 & 11 with varying numbers of processes and record when they break
 * Maybe need to use a profiler as well.
 * Results should inform recommendations document...

###Test 12: Publish datasets with different “esg.ini” files

This test checks whether using multiple “esg.ini” files (one for each project) cause problems in publication. See GitHub issue:
https://github.com/ESGF/esg-publisher/issues/8

 * Publish dataset from project X using appropriate esg_x.ini
   * Verify dataset is in db, TDS and Solr
 * Publish dataset from project Y using appropriate esg_y.ini
   * Verify dataset is in db, TDS and Solr
 * Unpublish dataset from project X using appropriate esg_x.ini
   * Verify consistency of Solr and TDS metadata related to dataset from project Y

###Test CEDA1: Publication from a non Data Node*** (CEDA ONLY)

This test verifies that a remote computer (i.e. a different host from the Data Node) can perform each stage in publication:

* Publish dv1 to db from remote host.
  * Verify dv1 in db.
* Publish dv1 to TDS from remote host.
  * Verify dv1 in TDS.
* Publish dv1 to Solr from remote host.
  * Verify dv1 in Solr.

##Implementation details

Download test - need to work out best approach, see:
 https://github.com/ESGF/esgf-test-suite/blob/master/esgf-test-suite/test_3_endpoints.py

Need to test all access methods (if we can):

* wget
* globus
* opendap
* http

##Notes about the test suite

The test methods (within each test class) are named using the following convention:

    test_<TNN>_<what_the_test_does>
    
Where \<T\> is the Test Number, \<NN\> is a two-digit number and \<what_the_test_does\> is a short name describing the test contents.

Note that test methods are executed in alphabetical order! It is therefore important to use the <\TNN\> in the method names to prescribe the order in which you want the methods to be executed.
 
##Running the suite

To run the test suite:

 1. Enter the "test_suite" directory.

 2. Run the "test_suite_runner.py" script: 

    $ ./run_tests.py

To run particular tests only:

    $ ./run_tests.py <regexp>

the regexp is applied (with re.search) to the method names, for example,

    $ ./run_test.py '^test_[123]_'

    $ ./run_test.py 'parallel'
