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
 * The class <code>ProgressBarCreator</code>creates a progress bar and displays
 * the percentage inside the bar.
 * 
 * @author Carla Hardy 
 * @version 07/14/2010
 */

import java.awt.Dimension;
import java.awt.Insets;

import javax.swing.JButton;
import javax.swing.JPanel;
import javax.swing.JProgressBar;
import javax.swing.SwingUtilities;
import java.awt.event.ActionListener;
import java.awt.event.ActionEvent;

public class ProgressBarCreator extends JPanel {
	private static final long serialVersionUID = 1L;
	JProgressBar pbar;
	protected int minValue = 0;
	protected int maxValue = 100;
	int counter;
  
	public ProgressBarCreator() {
	    pbar = new JProgressBar();
	    pbar.setMinimum(minValue);
	    pbar.setMaximum(maxValue);
	    counter = 0;
	    
	    editProgressBar();
	    displayProgressBar();
	}
	  
   /**
    * Edits progress bar size
    */
	public void editProgressBar() {
	    Dimension prefSize = pbar.getPreferredSize();
	    prefSize.width = 720;
	    prefSize.height = 20;
	    pbar.setPreferredSize(prefSize);
	}
	    
   /**
    * Displays a progress bar and a button
    */
	public void displayProgressBar() {    	    	    
	    pbar.setStringPainted(true);//Display progress in percentages %	    
	    JButton start = new JButton("Status");
	    start.setMargin(new Insets(3,43,3,43));
	    add(start);
	    add(pbar);
	    
	  start.addActionListener(new ActionListener() {
		  public void actionPerformed(ActionEvent e) {
		    Thread runner = new Thread() {
		      public void run() {
		        counter = minValue;
		        while (counter <= maxValue) {
		          Runnable runme = new Runnable() {
		            public void run() {
		              pbar.setValue(counter);
		            }
		          };
		          SwingUtilities.invokeLater(runme);
		          counter++;
		          try {
		            Thread.sleep(100);
		          } 
		          catch (Exception ex) {
		          }
		        }
		      }
		    };
		    runner.start();
		  }
	  });
	}
}

//  public ProgressBarCreator() {
//
//    UIManager.put("ProgressBar.selectionBackground", Color.black);
//    UIManager.put("ProgressBar.selectionForeground", Color.white);
//    UIManager.put("ProgressBar.foreground", new Color(8, 32, 128));
//