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
 * The class <code>DatasetMetadataDisplayer</code> Builds the dataset's metadata
 * form to be filled/edited by the user. There is one form per dataset 
 * 
 * @author Carla Hardy 
 * @version 07/28/2010
 */

import java.awt.Color;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;

import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JTextField;

public class DatasetMetadataDisplayer {
		GridBagConstraints textFieldConstrain1;
		JPanel textFieldPanel; 
	
	public DatasetMetadataDisplayer() {
		textFieldPanel = new JPanel(new GridBagLayout()); //inner panel
	}
	
	/**
	 * Returns the dataset's metadata form panel
	 * @return the form's panel
	 */
	public JPanel returnMetadata() {
		return textFieldPanel;
	}

	/**
	 * Add Labels and text fields to a panel to build Dataset's metadata
	 * form 
	 */
	public void addComponents() {		
		String nameString = "Name:";
		String projectString = "Project:";
		String modelString = "Model:";
		String experimentString = "Experiment:";
		String runNameString = "Run Name:";
		String timeFrequencyString = "Time Frequency:";
		String otherString = "Other:";
				
		JLabel nameLabel = new JLabel(nameString);
		JLabel projectLabel = new JLabel(projectString);
		JLabel modelLabel = new JLabel(modelString);
		JLabel experimentLabel = new JLabel(experimentString);
		JLabel runnameLabel = new JLabel(runNameString);
		JLabel timefrequencyLabel = new JLabel(timeFrequencyString);
		JLabel otherLabel = new JLabel(otherString);
		
		JTextField name = new JTextField ("name", 30);
		JTextField project = new JTextField ("project", 30);
		JTextField model = new JTextField ("model", 30);
		JTextField experiment = new JTextField ("experiment", 30);
		JTextField runName = new JTextField ("runname", 30);
		JTextField timeFrequency = new JTextField ("timefrequency", 30);
		JTextField other = new JTextField ("other", 30);	
		
		// Add Labels to Panel and changes color or required labels to blue				
		textFieldConstrain1 = new GridBagConstraints(0,0,1,1,1.0,0,GridBagConstraints.WEST, 
				GridBagConstraints.BOTH,new Insets(5,15,5,5),1,0);
			textFieldPanel.add(nameLabel, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(0,2,1,1,1.0,0,GridBagConstraints.WEST, 
				GridBagConstraints.BOTH,new Insets(5,15,5,5),0,0);
			projectLabel.setForeground(new Color(34,24,130));
			textFieldPanel.add(projectLabel, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(0,4,1,1,1.0,0,GridBagConstraints.WEST, 
				GridBagConstraints.BOTH,new Insets(5,15,5,5),0,0);
			modelLabel.setForeground(new Color(34,24,130));
			textFieldPanel.add(modelLabel, textFieldConstrain1);	
		
		textFieldConstrain1 = new GridBagConstraints(0,6,1,1,1.0,0,GridBagConstraints.WEST, 
				GridBagConstraints.BOTH,new Insets(5,15,5,5),0,0);
			experimentLabel.setForeground(new Color(34,24,130));
			textFieldPanel.add(experimentLabel, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(0,8,1,1,1.0,0,GridBagConstraints.WEST, 
				GridBagConstraints.BOTH,new Insets(5,15,5,5),0,0);
			runnameLabel.setForeground(new Color(34,24,130));
			textFieldPanel.add(runnameLabel, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(0,10,1,1,1.0,0,GridBagConstraints.WEST, 
				GridBagConstraints.BOTH,new Insets(5,15,5,5),0,0);
			timefrequencyLabel.setForeground(new Color(34,24,130));
			textFieldPanel.add(timefrequencyLabel, textFieldConstrain1);
			
		textFieldConstrain1 = new GridBagConstraints(0,12,1,1,1.0,0,GridBagConstraints.WEST, 
				GridBagConstraints.BOTH,new Insets(5,15,5,5),0,0);
			textFieldPanel.add(otherLabel, textFieldConstrain1);
		
		// Add TextFields to Panel
		textFieldConstrain1 = new GridBagConstraints(1,0,1,1,0,0,GridBagConstraints.WEST, 
				GridBagConstraints.HORIZONTAL,new Insets(5,5,5,15),0,0);
			textFieldPanel.add(name, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(1,2,1,1,0,0,GridBagConstraints.WEST, 
				GridBagConstraints.HORIZONTAL,new Insets(5,5,5,15),0,0);
    		textFieldPanel.add(project, textFieldConstrain1);
    	
    	textFieldConstrain1 = new GridBagConstraints(1,4,1,1,0,0,GridBagConstraints.WEST, 
    			GridBagConstraints.HORIZONTAL,new Insets(5,5,5,15),0,0);
			textFieldPanel.add(model, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(1,6,1,1,0.1,0,GridBagConstraints.WEST, 
				GridBagConstraints.HORIZONTAL,new Insets(5,5,5,15),0,0);
			textFieldPanel.add(experiment, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(1,8,1,1,0.1,0,GridBagConstraints.WEST, 
				GridBagConstraints.HORIZONTAL,new Insets(5,5,5,15),0,0);
			textFieldPanel.add(runName, textFieldConstrain1);
		
		textFieldConstrain1 = new GridBagConstraints(1,10,1,1,0.1,0,GridBagConstraints.WEST, 
				GridBagConstraints.HORIZONTAL,new Insets(5,5,5,15),0,0);
			textFieldPanel.add(timeFrequency, textFieldConstrain1);
			
		textFieldConstrain1 = new GridBagConstraints(1,12,1,1,0.1,0,GridBagConstraints.WEST, 
				GridBagConstraints.HORIZONTAL,new Insets(5,5,5,15),0,0);
			textFieldPanel.add(other, textFieldConstrain1);
	}
}



