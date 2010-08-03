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
 *   Written by: Carla Hardy (hardy21@llnl.gov)                            *
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
 * Displays a Java Swing interface for the ESG Publisher.
 * 
 * @author Carla Hardy 
 * @version 06/15/2010
 */

//package esg.node.publisher_fe;
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
// import javax.swing.DefaultCellEditor;
// import javax.swing.JCheckBox;
// import javax.swing.JComboBox;
// import javax.swing.JFrame;
// import javax.swing.JPanel;
// import javax.swing.JScrollPane;
// import javax.swing.JTable;
import javax.swing.table.JTableHeader;
import javax.swing.table.AbstractTableModel;
// import javax.swing.table.DefaultTableCellRenderer;
// import javax.swing.table.TableCellRenderer;
import javax.swing.table.TableColumn;
//import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagLayout;
import java.awt.BorderLayout;

public class ESGPublisher_draft extends JPanel implements ActionListener, ItemListener {  
	// Creates Top and Bottom Tabbed panes
    JTabbedPane tabbedPaneTop = new JTabbedPane();
    JTabbedPane tabbedPaneBottom = new JTabbedPane();
    
    // Creates two tables to display data from an array / passed by value
    JTable table = new JTable (new MyTableModel());
    JTable tableTab2 = new JTable (3,2);
    
    // Creates a JPanel will hold the content of each tab
    JPanel collection = new JPanel();
    JPanel collection2 = new JPanel();
    JPanel collection1 = new JPanel();
    JPanel collection3 = new JPanel();
	
    JButton closeTabButton = new JButton("X");
    JButton closeTabButton1 = new JButton("X");
    
    //Temporary String Text for Editor Pane
    String output = "This is the text for the Output/Error tab. It will be " + 
	"displayed until data is generated\n" + "\n" +
	"This is the text for the Output/Error tab. It will be " + 
	"displayed until data is generated\n" + "\n" +
	"This is the text for the Output/Error tab. It will be " + 
	"displayed until data is generated using Eclipse\n" + "\n";
    
    public void buildapp() {
        // Creates the window frame
        // Sets decorations
        JFrame.setDefaultLookAndFeelDecorated(true);
        // Creates and set up the frame and name
        JFrame frame = new JFrame("ESG Publisher");
        // Closes application when close button is clicked
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        // Creates the scroll pane and add the table to it
        JScrollPane scrollPane = new JScrollPane(table, JScrollPane.VERTICAL_SCROLLBAR_ALWAYS,
												 JScrollPane.HORIZONTAL_SCROLLBAR_ALWAYS);        
        table.setFillsViewportHeight(true);
        // Adds the scroll pane to the panel CHANGE THIS#####
        add(scrollPane);
        // Sets up the scrolling window size
        table.setPreferredScrollableViewportSize(new Dimension(600, 70));
        
        // Sets up column sizes
        customizeColumns(table);
        
        // Build top Tabs
        buildTopTab();
        buildTopTab2();
        buildBottomTab();
        buildBottomTab2();
        
        // Populates table in tab 2
        populateTable();
        
        // Build buttons to close tabs
        buildCloseTabButtons();
		
        // Add panels and tab names to Tabbed Panes
        tabbedPaneTop.addTab("Collection 1", collection2);   
        tabbedPaneTop.addTab("Collection 2", collection);
        tabbedPaneBottom.addTab("Output", collection1);
        tabbedPaneBottom.addTab("Error", collection3);
        
        // The following lines enable to use scrolling tabs.
        tabbedPaneTop.setTabLayoutPolicy(JTabbedPane.SCROLL_TAB_LAYOUT);
        tabbedPaneBottom.setTabLayoutPolicy(JTabbedPane.SCROLL_TAB_LAYOUT);
        
        /*
         * Adds contents to frame and make it visible
         */
        // Add the JPanels to the frame
        frame.getContentPane().add(tabbedPaneTop);
        frame.getContentPane().add(tabbedPaneBottom, BorderLayout.SOUTH); 
        // Display the frame
        frame.setSize(650, 500);
        frame.setVisible(true); 
    }
    
    /**
     * Builds top tab 1.
     * Contains a table populated with setValueAt().
     * Edits the Layout using GridBagLayout.
     */
    public void buildTopTab() {
        collection.setLayout(new GridBagLayout());
        // New GridBagConstrain to edit component layout
        GridBagConstraints closeTabConstrain = new GridBagConstraints();
		// table header
		closeTabConstrain.fill = GridBagConstraints.HORIZONTAL;
		closeTabConstrain.gridx = 1; // aligned with table header
		collection.add(tableTab2.getTableHeader(), closeTabConstrain);
		// table body
		closeTabConstrain.fill = GridBagConstraints.HORIZONTAL;
		closeTabConstrain.gridx = 1; // aligned with table header
		collection.add(tableTab2, closeTabConstrain);               
		// close button
		closeTabConstrain.fill = GridBagConstraints.NONE;
		closeTabConstrain.ipady = 0; // reset to default
		closeTabConstrain.weighty = 1.0; // request any extra vertical space
		closeTabConstrain.anchor = GridBagConstraints.PAGE_END; // bottom of space
		closeTabConstrain.insets = new Insets(10,0,0,0); // padding T,L,B,R
		collection.add(closeTabButton, closeTabConstrain);
    }
    
    /**
     * Adds contents to table in Top Tab 2
     */
    public void populateTable() {
        tableTab2.setValueAt("Test value", 0,0);
        JTableHeader tableTab2Header = new JTableHeader();
        tableTab2.setTableHeader(tableTab2Header);
    }
    
    /**
     * Builds top tab 2.
     * Contains a table populated using an array.
     * Edits the Layout using GridBagLayout.
     */
    public void buildTopTab2() {
        collection2.setLayout(new GridBagLayout());
        // New GridBagConstrain to edit component layout
        GridBagConstraints closeTabConstrain2 = new GridBagConstraints();
		// table header
		closeTabConstrain2.fill = GridBagConstraints.HORIZONTAL;
		closeTabConstrain2.gridx = 1; // aligned with table
		closeTabConstrain2.anchor = GridBagConstraints.PAGE_START;
		collection2.add(table.getTableHeader(), closeTabConstrain2);
		// table body
		closeTabConstrain2.fill = GridBagConstraints.HORIZONTAL;
		closeTabConstrain2.gridx = 1; // aligned with table header
		collection2.add(table, closeTabConstrain2);
		// close button
		closeTabConstrain2.fill = GridBagConstraints.NONE; // turn off stretchyness 
		closeTabConstrain2.ipady = 0; // reset to default
		closeTabConstrain2.weighty = 1.0; // request any extra vertical space
		closeTabConstrain2.anchor = GridBagConstraints.PAGE_END; // bottom of space
		closeTabConstrain2.insets = new Insets(10,0,0,0);  // top padding
		closeTabConstrain2.gridx = 1; // aligned with button 2
		closeTabConstrain2.gridy = 2; // third row
		collection2.add(closeTabButton1, closeTabConstrain2);
    }
	
    /**
     * Builds Bottom Output tab.
     * Turns editable feature off
     */
    public void buildBottomTab(){
        JEditorPane outputTextArea = new JEditorPane("text", output);
        outputTextArea.setEditable(false);
        outputTextArea.setSize(600, 300);
        collection1.add(outputTextArea);
        
    }
    
    /**
     * Builds Bottom Error tab.
     * Turns editable feature off
     */
    public void buildBottomTab2(){
        JEditorPane errorTextArea = new JEditorPane("text", output);
        errorTextArea.setEditable(false);
        errorTextArea.setSize(600, 300);
        collection3.add(errorTextArea);
    }
    
    /**
     * Builds buttons to close tabs. 
     * Adds a Mnemonic to close the window (Alt + C) and tool tips
     */   
    public void buildCloseTabButtons() {
        closeTabButton.setMnemonic(KeyEvent.VK_C);
        closeTabButton.setToolTipText("Close Tab");
        closeTabButton.setPreferredSize(new Dimension (20, 20));
        closeTabButton.addActionListener(this);
        
        // Close Button for second tab        
        closeTabButton1.setMnemonic(KeyEvent.VK_C);
        closeTabButton1.setToolTipText("Close Tab");
        closeTabButton1.setPreferredSize(new Dimension (20, 20));
        closeTabButton1.addActionListener(this);
    }
    
    /**
     * Removes Tabs using 'Close Tab' button
     */
    public void actionPerformed (ActionEvent e) {
        tabbedPaneTop.remove(tabbedPaneTop.getSelectedIndex());
    }
    
    //#Not being used for now
    public void itemStateChanged (ItemEvent e) {
        //Object source = e.getItemSelectable();
    }
    
    /**
     * Sets customized column sizes
     */
    private void customizeColumns (JTable table) {
		
        TableColumn column = null;
        
        for (int i = 0; i < 5; i++){
            column = table.getColumnModel().getColumn(i);
            if ( i == 4 ) {
                column.setPreferredWidth(200);
            } 
            else if ( i == 2 ) {
                column.setPreferredWidth(70);
            }
            else {
                column.setPreferredWidth(45);
            }
        }
    }
    
    /**
     * The <code>MyTableModel</code> class creates table contents and specify 
     * AbstractTableModel methods.
     */
    class MyTableModel extends AbstractTableModel {
		
        /**
		 * 
		 */
		private static final long serialVersionUID = 1L;
		private String[] columnNames = {"Pick", "OK/Error", "Status", "ID", "DataSet"}; 
        private Object[][] data = {
		{new Boolean(false), "OK", "Published", "109", "pcmdi.ipcc4.gfdl"},
		{new Boolean(false), "OK", "Published", "109", "pcmdi.ipcc4"},
		{new Boolean(false), "OK", "Published", "109", "pcmdi.ipcc4"},
		{new Boolean(true), "OK", "Published", "109", "pcmdi.ipcc4"},
		{new Boolean(false), "OK", "Published", "110", "pcmdi.ipcc6"},
		{new Boolean(false), "OK", "Published", "111", "pcmdi.ipcc5"},
		{new Boolean(false), "OK", "Published", "112", "pcmdi.ipcc6"},
		{new Boolean(false), "OK", "Published", "113", "pcmdi.ipcc6.gfdl"},
		{new Boolean(false), "OK", "Published", "114", "pcmdi.ipcc6"},
		{new Boolean(false), "OK", "Published", "115", "pcmdi.ipcc6"},};
		
		
        public int getColumnCount() {
            return columnNames.length;
        }
		
        public int getRowCount() {
            return data.length;
        } 
        
        public String getColumnName(int col) {
            return columnNames[col];
        }
		
        public Object getValueAt(int row, int col) {
            return data[row][col];
        }
		
        /* 
         * JTable uses this method to determine the default renderer / 
         * editor for each cell. Used by the first column to display checkboxes
         */
        @SuppressWarnings("unchecked")
		public Class getColumnClass(int index){
            return getValueAt(0, index).getClass();
        }
        
        /*
         * Returns true if cell is editable
         * Have to be true to allow setValueAt to change values
         */
        public boolean isCellEditable(int row, int col) {
            //Note that the data/cell address is constant,
            //no matter where the cell appears onscreen.
            if (col < 2) {
                return false;
            } else {
                return true;
            }
        }
        
        /*
         * Sets the value in the cell
         * value - new value
         */
        public void setValueAt(Object value, int row, int col) {
            data[row][col] = value;
            fireTableCellUpdated(row, col); // update specified cell
        }
    }
    
}