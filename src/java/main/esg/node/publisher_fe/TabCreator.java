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
 * The class <code>TabCreator</code> 
 * Begins at tab 2
 * 
 * @author Carla Hardy 
 * @version 06/15/2010
 */

import java.awt.Dimension;
import java.awt.GridLayout;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;
import javax.swing.JTable;
import javax.swing.border.Border;

class TabCreator{
	JButton closeButton;
	JPanel buttonPanel;
	JTabbedPane tpTop;
	int tabCounter;
	String tabLabel, labelName;
	JTable table;
    TableColumnEditor tableColumnEditor;
    JScrollPane dataTableScrollpane;
	MyTableModel model; 
	JPanel tablePanel;
	boolean tabCreatorClass;
	boolean removedTab;
	
	public TabCreator(JTabbedPane tabbedPane, int counter) {
		tpTop = tabbedPane;	
		tabCounter = counter;
		model = new MyTableModel(); 		
		closeButton = new JButton("x");
		buttonPanel = new JPanel();
		table = new JTable(model);
		tablePanel = new JPanel(new GridLayout());
		dataTableScrollpane = new JScrollPane(table);
		tableColumnEditor = new TableColumnEditor(table);
		tabLabel = "";
		tabCreatorClass = true;
		removedTab = false;
	}

	public void createRemainingTabs() {
		Border closeButtonBorder = BorderFactory.createEmptyBorder(-2, 2, -2, 2);
		buttonPanel.setOpaque(false);//makes the panel transparent
		buttonPanel.setBorder(closeButtonBorder);
		labelName = "Collection " + tabCounter;
		buttonPanel.add(new JLabel(labelName));
		closeButton.setPreferredSize(new Dimension(20,20));
		closeButton.setMargin(new Insets(2,2,2,2));
		buttonPanel.add(closeButton);
		
		closeButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {				
					int i = tpTop.getSelectedIndex();
					if (i != -1) {
						//collectionPanel.removeAll();
						tpTop.remove(i);
						removedTab = true;
						//returnRemovedTab();
					}				
			}
		});
		tableColumnEditor.editTable();
		table.setRowHeight(20);
		table.setAutoCreateRowSorter(true); //table sorter
		table.setRowSelectionAllowed(false);//selection disabler
	    table.setPreferredScrollableViewportSize(new Dimension(530, 280));
	    table.setFillsViewportHeight(true);

		tablePanel.add(dataTableScrollpane);
		
		// Creates buttons in inner table at column 5 (DataSet)
	    ButtonRenderer buttonRenderer = new ButtonRenderer();		
	    TableButtonEditor tableButtonEditor = new TableButtonEditor(new JCheckBox(), 
	    			                          new InnerPaneCreator(tpTop, dataTableScrollpane, tablePanel, table, tabLabel));
	    table.getColumnModel().getColumn(4).setCellRenderer(buttonRenderer);
	    table.getColumnModel().getColumn(4).setCellEditor(tableButtonEditor);
		
		tpTop.addTab("", tablePanel);
		tpTop.setSelectedIndex(tpTop.getTabCount() - 1); //make new tab active
		//tpTop.setForeground(new Color(142, 35, 35));
		tpTop.setToolTipTextAt(tpTop.getTabCount() - 1, labelName);
		tpTop.setTabComponentAt(tpTop.getTabCount() - 1, buttonPanel); 
	}
	
	public void unselectCheckbox() {
		for (int i = 0; i < model.getRowCount(); i++) {
	    	model.setValueAt(false, i, 0);
	    }
	}
	
	public void selectCheckbox() {
		for (int i = 0; i < model.getRowCount(); i++) {
	    	model.setValueAt(true, i, 0);
	    }
	}
	
	public String returnLabelName() {
		return labelName;
	}
	
	public int returnIndex() {
		return tabCounter;
	}	
	
	public int returnRemovedTab() {
		System.out.println("tab removed" + tabCounter);
		return tabCounter;
	}
}