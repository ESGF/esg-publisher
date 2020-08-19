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
 * The class <code>CreateTabs</code> sets Action Listener action events.
 * actionListenerIndex = 2
 * 
 * @author Carla Hardy 
 * @version 06/15/2010
 */
package esg.node.publisher_fe;
import java.awt.Dimension;
import java.awt.Insets;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTabbedPane;
import javax.swing.JTable;
import javax.swing.border.Border;
import javax.swing.table.JTableHeader;

class CreateTabs extends JButton {
	private static final long serialVersionUID = 1L;
	JSplitPane spTop;
	JPanel buttonPanel, collectionPanel;	
	JTabbedPane tpTop;
	int tabCounter;
	String tabLabel, label;
    JTable dataTable;
    TableColumnEditor tableColumnEditor;
    JScrollPane scrollPane;
	MyTableModel model; 
	ExpandablePanelCreator epc;
	JButton closeButton;
	boolean tabCreatorClass, removedTab;
	
	public CreateTabs(JSplitPane splitPaneTop, JPanel jPanel, JTabbedPane tabbedPaneTop, 
															int counter) {
		spTop = splitPaneTop;
		collectionPanel = jPanel; //collection1
		tpTop = tabbedPaneTop;		
		tabCounter = counter;		
		buttonPanel = new JPanel();
		tabLabel = "";	
		label = "Collection 1" ;
		tableColumnEditor = new TableColumnEditor(dataTable);
		scrollPane = new JScrollPane(dataTable);
		model = new MyTableModel(); 
		dataTable = new JTable(model);
		epc = new ExpandablePanelCreator(spTop, tpTop, collectionPanel);
		closeButton = new JButton("x");
		tabCreatorClass = false;
		removedTab = false;
	}
	
	/**
	 * Creates first tab, adds a close button to remove the tab
	 * Adds tab to a panel and sets it as right component in splitpane
	 */
	public void createFirstTab() {		
		// Creates a close button for the tab
		Border closeButtonBorder = BorderFactory.createEmptyBorder(-2, 2, -2, 2);
		buttonPanel.setOpaque(false);//makes the panel transparent
		buttonPanel.setBorder(closeButtonBorder);
		buttonPanel.add(new JLabel(label));
		buttonPanel.add(closeButton);
		closeButton.setPreferredSize(new Dimension(20,20));
		closeButton.setMargin(new Insets(2,2,2,2));
		
		closeButton.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent e) {				
				int i = tpTop.getSelectedIndex();
				if (i != -1) {
					collectionPanel.removeAll();
					tpTop.remove(i);
					removedTab = true;
				}			
			}
		}); 
		TableColumnEditor tableColumnEditor = new TableColumnEditor(dataTable);
		tableColumnEditor.editTableColumn();
		tableColumnEditor.tableSettings();
	    	
		JScrollPane dataTableScrollpane = new JScrollPane(dataTable);
		collectionPanel.add(dataTableScrollpane);
		
		// Creates buttons in inner table at column 5 (DataSet)
	    ButtonRenderer buttonRenderer = new ButtonRenderer();		
	    TableButtonEditor tableButtonEditor = new TableButtonEditor(new JCheckBox(), 
	    			                          new InnerPaneCreator(tpTop, dataTableScrollpane, 
	    			                        		  collectionPanel, dataTable, tabLabel));
	    dataTable.getColumnModel().getColumn(4).setCellRenderer(buttonRenderer);
	    dataTable.getColumnModel().getColumn(4).setCellEditor(tableButtonEditor);
		
		tpTop.addTab("", collectionPanel);      
		tpTop.setTabComponentAt(0, buttonPanel);
		tpTop.setToolTipTextAt(tpTop.getTabCount() - 1, label);
		spTop.setRightComponent(tpTop); //set right component of split pane
		tpTop.updateUI();
    }
	
	public void unselectCheckbox() {
		System.out.println("select/deselect:" + model);
		for (int i = 0; i < model.getRowCount(); i++) {
	    	model.setValueAt(false, i, 0);
	    }
	}
	
	public void selectCheckbox() {
		for (int i = 0; i < model.getRowCount(); i++) {
	    	model.setValueAt(true, i, 0);
	    }
	}
	
	public int returnIndex() {
		return tabCounter;
	}
	
	public String returnLabelName() {
		return label;
	}
	
    /**
     * Adds contents to table in Top Tab 2
     */
    public void populateTable() {
       dataTable.setValueAt("Test value", 0,0);
       JTableHeader tableTab2Header = new JTableHeader();
       dataTable.setTableHeader(tableTab2Header);
    }
}