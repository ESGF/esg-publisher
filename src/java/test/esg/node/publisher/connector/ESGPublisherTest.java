/***************************************************************************
*                                                                          *
*  Organization: Lawrence Livermore National Lab (LLNL)                    *
*   Directorate: Computation                                               *
*    Department: Computing Applications and Research                       *
*      Division: S&T Global Security                                       *
*        Matrix: Atmospheric, Earth and Energy Division                    *
*       Program: PCMDI                                                     *
*       Project: Earth Systems Grid (ESG) Data Node Software Stack         *
*  First Author: Gavin M. Bell (gavin@llnl.gov)                            *
*                                                                          *
****************************************************************************
*                                                                          *
*   Copyright (c) 2009, Lawrence Livermore National Security, LLC.         *
*   Produced at the Lawrence Livermore National Laboratory                 *
*   Written by: Gavin M. Bell (gavin@llnl.gov)                             *
*   LLNL-CODE-420962                                                       *
*                                                                          *
*   All rights reserved. This file is part of the:                         *
*   Earth System Grid (ESG) Data Node Software Stack, Version 1.0          *
*                                                                          *
*   For details, see http://esg-repo.llnl.gov/esg-node/                    *
*   Please also read this link                                             *
*    http://esg-repo.llnl.gov/LICENSE                                      *
*                                                                          *
*   * Redistribution and use in source and binary forms, with or           *
*   without modification, are permitted provided that the following        *
*   conditions are met:                                                    *
*                                                                          *
*   * Redistributions of source code must retain the above copyright       *
*   notice, this list of conditions and the disclaimer below.              *
*                                                                          *
*   * Redistributions in binary form must reproduce the above copyright    *
*   notice, this list of conditions and the disclaimer (as noted below)    *
*   in the documentation and/or other materials provided with the          *
*   distribution.                                                          *
*                                                                          *
*   Neither the name of the LLNS/LLNL nor the names of its contributors    *
*   may be used to endorse or promote products derived from this           *
*   software without specific prior written permission.                    *
*                                                                          *
*   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS    *
*   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT      *
*   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS      *
*   FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL LAWRENCE    *
*   LIVERMORE NATIONAL SECURITY, LLC, THE U.S. DEPARTMENT OF ENERGY OR     *
*   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,           *
*   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT       *
*   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF       *
*   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND    *
*   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,     *
*   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT     *
*   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF     *
*   SUCH DAMAGE.                                                           *
*                                                                          *
***************************************************************************/

/**
   Description:

   Simple Boostrap pseudo "main" program for running Tests

**/
package esg.node.publisher.connector;

import org.junit.*;
import static org.junit.Assert.*;
import static org.junit.Assume.*;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.commons.logging.impl.*;

//TODO... this is a place holder skel... 
//Intended for bootstrapping basic JUnit testing...

public class ESGPublisherTest {
    private static final Log log = LogFactory.getLog(ESGPublisherTest.class);

    private static ESGPublisher pub = null;

    public ESGPublisherTest() {
	log.info("Instantiating ESGPublisherTest...");
    }
    
    /**
       This is performed once before even this test class is instantiated!
       Note: It must be static
     */
    @BeforeClass
    public static void initialSetup() {
	log.trace("Performing initial setup");
	pub = new ESGPublisher("mytest");	
    }

    /**
       This will be called before each test method is run
     */
    @Before
    public void setup() {
	log.trace("Setting up test");
    }
    
    /**
       This is here just to illustrate that you may have multiple
       "Before" methods (or After) methods but that they get fired in
       no guaranteed order, only that they both happen before your
       tests. Basically you should probably just have one
       (BeforeClass,Before,After,AfterClass) set of methods per test
       suite (test class).  Using that as a guildline for how to break
       up unit testing code.
     */
    @Before
    public void setup2() {
	log.trace("Setting up test too");
    }

    /**
       Test method (notice assertions)
     */
    @Test
    public void testSum() {
	log.trace("test...");
	assertTrue(pub.sum(3,5) == 8);
	assertTrue(pub.sum(3,2) == 5);
    }

    @Test
    public void testSum2() {
	log.trace("test2...");
	assumeNotNull(pub);
	assertTrue(pub.sum(3,5) == 8);
	assertTrue(pub.sum(3,2) == 5);
	assumeTrue(pub.sum(2,2) > 4);
    }

    /**
       Simply illustrating the use of the @Ignore annotation
     */
    @Ignore
    @Test
    public void testSum3() {
	log.trace("test3...");
	assertTrue(pub.sum(3,5) == 8);
	assertTrue(pub.sum(3,2) == 5);
    }

    /**
       This will be called after each test method is run
     */
    @After
    public void tearDown() {
	log.trace("Tearing down test");
    }
    
    /**
       This is performed once when all the tests in this class have been run.
       Note: It must be static
     */
    @AfterClass
    public static void finalTearDown() {
	log.trace("Performing final tear down");
	pub = null;
    }
}
