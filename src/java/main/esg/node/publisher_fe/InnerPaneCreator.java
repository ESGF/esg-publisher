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
 * The class <code>InnerPaneCreator</code> creates inner tabs using Action Listener's 
 * action events
 * 
 * @author Carla Hardy 
 * @version 07/1/2010
 */

import java.awt.Color;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.GridLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;
import javax.swing.JTable;
import javax.swing.JLabel;
import javax.swing.border.Border;

class InnerPaneCreator implements ActionListener {
	JTabbedPane tabPaneTop, innerTabPane;
	JPanel collectionPanel, tablePanel;
	JTable jtable;
	JScrollPane scrollpane;
	String label;
	int index;	
	GridBagConstraints saveChangesButtonConstrain;	
	MyTableModel tableModel;
	
	public InnerPaneCreator(JTabbedPane tabbedPanel, JScrollPane scrollPane, JPanel panel, 
			          JTable table, String tablabel) {
		tabPaneTop = tabbedPanel;
		scrollpane = scrollPane;
		collectionPanel = panel;				
		jtable = table; 
		label = tablabel;
		
		innerTabPane = new JTabbedPane();
		tablePanel = new JPanel(new GridLayout());
		index = 1;
		tableModel = new MyTableModel();
	}
	
	/**
	 * Calls actionPerformed method
	 * @param e  the action event
	 */
	public void actionPerformed (ActionEvent e) { 				
		if (index == 1) {
			createFirstInnerTab();					
			tabPaneTop.updateUI(); //Updates existing top tab to display new components
			index++;
		}
		else {
			createRemainingInnerTab();
		}
    }
	
	/**
	 * Creates first tab. This is needed to move the table panel(inside a tab pane)
	 * to an inner tab pane. 
	 */
	public void createFirstInnerTab() {
		//Create a Scroll pane for the table
		JScrollPane scrollPaneTable = new JScrollPane(jtable);
		scrollPaneTable.setPreferredSize(new Dimension(530, 280));
		jtable.setFillsViewportHeight(true);
		
		//Create a Scroll pane for the metadata field form
		DatasetMetadataDisplayer metadataDisplayer = new DatasetMetadataDisplayer();
		JPanel metada = metadataDisplayer.returnMetadata();
		JScrollPane scrollPaneDatasetSp = new JScrollPane(metada);
		scrollPaneDatasetSp.setPreferredSize(new Dimension(570, 280));		
		metadataDisplayer.addComponents();
		
		//Add metadata form and 'Save Changes' button to panel
		JPanel metadataButtonPanel = new JPanel(new GridBagLayout());
		JButton saveChangesButton = new JButton("Save Changes");
		saveChangesButton.setMargin(new Insets(3,3,3,3));
		metadataButtonPanel.add(scrollPaneDatasetSp);
		saveChangesButtonConstrain = new GridBagConstraints(0,2,1,1,0,0,GridBagConstraints.PAGE_END,
				GridBagConstraints.NONE,new Insets(5,0,0,0),0,0);
		metadataButtonPanel.add(saveChangesButton, saveChangesButtonConstrain);

		//Add collection table to inner tab
	    tablePanel.add(scrollPaneTable);
		innerTabPane.addTab("Collection Table", tablePanel);
	    
	    //Create close button panel
		JPanel closeButtonPanel = new JPanel();
		Border closeButtonBorder1 = BorderFactory.createEmptyBorder(-2, 2, -2, 2);
		closeButtonPanel.setBorder(closeButtonBorder1);

		//Add label name
		String dataSetName1 = (String) tableModel.getValueAt(1, 4); // TODO:fix this to display any row		
		JLabel tabName1= new JLabel(dataSetName1);
		tabName1.setForeground(new Color(34,24,130));
		closeButtonPanel.add(tabName1);
		
		//Add 'Close x' button
	    JButton closeButton1 = new JButton("x");
		closeButtonPanel.add(closeButton1);
		closeButton1.setPreferredSize(new Dimension(20,20));
		closeButton1.setMargin(new Insets(2,2,2,2));		
		closeButton1.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {				
					int i = innerTabPane.getSelectedIndex();
					if (i != -1) {
						innerTabPane.remove(i);
					}			
			}
		});	
		
		//Add metadata panel + save button panel to inner tab
		innerTabPane.addTab("", metadataButtonPanel);
		innerTabPane.setTabComponentAt(index, closeButtonPanel);
		innerTabPane.setSelectedIndex(innerTabPane.getTabCount() - 1); // make new tab active
		
		/* Add inner tab pane to existing collection panel
		 * The previous component have to be removed to add the new one*/
		collectionPanel.remove(scrollpane);
		collectionPanel.add(innerTabPane);
	}
	
	/**
	 * Creates subsequent tabs in the inner tab pane
	 */
	public void createRemainingInnerTab() {
		DatasetMetadataDisplayer metadataDisplayer = new DatasetMetadataDisplayer();
		
		//Create a Scroll pane for the metadata field form
		JPanel metada2 = metadataDisplayer.returnMetadata();
		JScrollPane scrollPaneDatasetSp = new JScrollPane(metada2);
		scrollPaneDatasetSp.setPreferredSize(new Dimension(570, 280));		
		metadataDisplayer.addComponents();
		
		//Add metadata form and 'Save Changes' button to panel
		JPanel metadataButtonPanel = new JPanel(new GridBagLayout());
		JButton saveChangesButton = new JButton("Save Changes");
		saveChangesButton.setMargin(new Insets(3,3,3,3));
		metadataButtonPanel.add(scrollPaneDatasetSp);
		saveChangesButtonConstrain = new GridBagConstraints(0,2,1,1,0,0,GridBagConstraints.PAGE_END,
				GridBagConstraints.NONE,new Insets(5,0,0,0),0,0);
		metadataButtonPanel.add(saveChangesButton, saveChangesButtonConstrain);
		
		//Add 'Close x' button
		JPanel buttonPanel = new JPanel();
		Border closeButtonBorder = BorderFactory.createEmptyBorder(-2, 2, -2, 2);
		buttonPanel.setBorder(closeButtonBorder);
		
		//Add label name
		String dataSetName = (String) tableModel.getValueAt(5, 4); // TODO:fix this to display any row
		JLabel tabName= new JLabel(dataSetName);
		tabName.setForeground(new Color(34,24,130));
		buttonPanel.add(tabName);
		
		//Add 'Close x' button
		JButton closeButton = new JButton("x");
		buttonPanel.add(closeButton);
		closeButton.setPreferredSize(new Dimension(20,20));
		closeButton.setMargin(new Insets(2,2,2,2));		
		closeButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {				
				int i = innerTabPane.getSelectedIndex();
				if (i != -1) {
					innerTabPane.remove(i);
				}			
			}
		});
		
		//Add metadata panel + save button panel to inner tab
		innerTabPane.addTab("", metadataButtonPanel);
		innerTabPane.setTabComponentAt(innerTabPane.getTabCount() - 1, buttonPanel);
		innerTabPane.setSelectedIndex(innerTabPane.getTabCount() - 1); // make new tab active
	}
}
	
