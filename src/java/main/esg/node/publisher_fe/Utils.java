/***************************************************************************
 *                                                                          *
 *  Organization: Lawrence Livermore National Lab (LLNL)                    *
 *   Directorate: Computation                                               *
 *    Department: Computing Applications and Research                       *
 *      Division: S&T Global Security                                       *
 *        Matrix: Atmospheric, Earth and Energy Division                    *
 *       Program: PCMDI                                                     *
 *       Project: Earth Systems Grid (ESG) Data Node Software Stack         *
 *  First Author: Carla Hardy (hardy21@llnl.gov)                            *
 *                                                                          *
 ****************************************************************************
 *                                                                          *
 *   Copyright (c) 2010, Lawrence Livermore National Security, LLC.         *
 *   Produced at the Lawrence Livermore National Laboratory                 *
 *   Written by: Carla Hardy (hardy21@llnl.gov)                             *
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
 * The class <code>Utils</code> is used by FileExtensionFilter.java to return
 * a file extension
 * 
 * @author Carla Hardy 
 * @version 07/28/2010
 */

import java.io.File;

public class Utils {
    public final static String nc = "nc";
    
    public Utils(){   	
    }

    /**
     * Gets the extension of a file.
     * @param f  file name
     * @return the file extension
     */
    public static String getExtension(File f) {
        String extension = null;
        String fileName = f.getName();
        int i = fileName.lastIndexOf('.');

        if (i > 0 && i < fileName.length() - 1) {
        	extension = fileName.substring(i+1).toLowerCase();
        }
        return extension;
    }
}