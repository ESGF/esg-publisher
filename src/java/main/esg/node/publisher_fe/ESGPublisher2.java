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
	 * Displays a Java Swing interface for the ESG Publisher.
	 * 
	 * @author Carla Hardy 
	 * @version 06/15/2010
	 */

	import javax.swing.*;
	import java.awt.*;
	import java.awt.event.*;
	import javax.swing.table.JTableHeader;
	
	import javax.swing.DefaultCellEditor;
	import javax.swing.JComboBox;
    import javax.swing.JComponent;
	import javax.swing.JScrollPane;
	import javax.swing.JButton;
	import javax.swing.JTable;
	import javax.swing.table.AbstractTableModel;
	import javax.swing.table.DefaultTableCellRenderer;
	import javax.swing.table.TableCellRenderer;
	import javax.swing.table.TableColumn;
    import javax.swing.table.TableModel;
	
import javax.swing.event.ListSelectionEvent;
import javax.swing.event.ListSelectionListener;
	import javax.swing.plaf.basic.BasicButtonUI;
	import javax.swing.table.TableColumn;
	import java.awt.Component;
	import java.awt.Dimension;
    import java.awt.GridBagConstraints;
	import java.awt.GridBagLayout;
    import java.awt.BorderLayout;
import java.awt.Insets;

	public class ESGPublisher2 extends JPanel implements MouseListener, ActionListener {  

        // Creates the window frame
    	//JFrame.setDefaultLookAndFeelDecorated(true); // Sets decorations
        // Creates and set up the frame and name
        JFrame frame = new JFrame("ESG Publisher");
        
		// Creates Top and Bottom Tabbed panes
	    JTabbedPane tabbedPaneTop = new JTabbedPane();
	    JTabbedPane tabbedPaneBottom = new JTabbedPane();
	    
	    // Creates two tables to display data from an array / passed by value
	    MyTableModel model = new MyTableModel();
	    JTable table = new JTable (model);
	    JTable tableTab2 = new JTable (4,4);
	    
	    // Creates a JPanel will hold the content of each tab
	    JPanel collection1 = new JPanel(new GridLayout(1,0)); //table2
	    JPanel collection2 = new JPanel(new GridLayout(2,0)); //table
	      JPanel collection1a = new JPanel(); //panel inside a panel to display refresh button
	    JPanel collection3 = new JPanel(new GridLayout(1,0));
	    JPanel collection4 = new JPanel(new GridLayout(1,0));
	    JPanel panelLeft = new JPanel(new GridBagLayout());//new BorderLayout());
	    
	    // Creates Editor Panes to display output and error data 
	    JEditorPane outputTextArea = new JEditorPane();
		    //Temporary String Text for Editor Pane
		    String output = "This is the text for the Error tab. This message will be " + 
		                    "displayed until data is generated\n" + "\n" +
		                    "This is the text for the Error tab. This message will be " + 
		                    "displayed until data is generated\n" + "\n" +
		                    "This is the text for the Error tab. This message will be " + 
		                    "displayed until data is generated\n" + "\n";
	    JEditorPane errorTextArea = new JEditorPane("text", output);
	    
	    // Creates close button icons
	    CloseTabIcon closeTabIcon = new CloseTabIcon();
	    CloseTabIcon closeTabIcon0 = new CloseTabIcon();
	    CloseTabIcon closeTabIcon1 = new CloseTabIcon();
	    
	    TableModel dataModel = new AbstractTableModel() {
	          public int getColumnCount() { return 10;}
	          public int getRowCount() { return 10;}
	          public Object getValueAt(int row, int col) { return new Integer(row*col); }
	      };
	    final JTable table2 = new JTable(dataModel);
	    
	    // Creates GUI buttons
	    //JButton refreshButton = new JButton("Refresh");
	    //JButton refreshButton2 = new JButton("Refresh");
	    JButton createTabButton = new JButton("Generate List");
	    JButton populateWindow = new JButton("Output");
	    
	    String tabLabel = "";
	    int actionListenerIndex = 2;
 
	    public void buildapp() {
	        
	    	addMouseListener(this); 
	    	
	    	buildFrame();
	    	
	        // Sets up the scrolling window size
	        table.setPreferredScrollableViewportSize(new Dimension(500, 70));
	        table.setFillsViewportHeight(true);
	        table2.setPreferredScrollableViewportSize(new Dimension(500, 70));
	        table2.setFillsViewportHeight(true);
	   
	        // Creates the scroll pane and add the table to it
	        JScrollPane scrollPane = new JScrollPane(table); 
	        //JScrollPane scrollPane2 = new JScrollPane(table2);
	        // Add the scroll pane to the panel
	        collection1.add(scrollPane);
	        //collection1.add(scrollPane2);
	        // Add a new panel to collection2 to add refresh button
	        //collection1.add(collection1a);
	        	        
	        // Sets up column sizes
	        customizeColumns(table);
	        
	        // Build top Tabs
	        buildTopTab();
	        buildTopTab2();
	        buildBottomTab();
	        buildBottomTab2();
	        
	        // Populates table in tab 1
	        populateTable();
	               
	        // Add panels and tab names to Tabbed Panes
	        tabbedPaneTop.addTab("Collection 1", closeTabIcon0, collection1);   
	        //tabbedPaneTop.addTab("Collection 2", closeTabIcon1, collection2);
	        tabbedPaneTop.addMouseListener(this);
	        tabbedPaneBottom.addTab("Output", collection3);
	        tabbedPaneBottom.addTab("Error", collection4);
	        
	        GridBagConstraints createTabConstrain = new GridBagConstraints();
	        createTabConstrain.fill = GridBagConstraints.HORIZONTAL; // turn off stretchyness 
	        createTabConstrain.ipady = 0; // reset to default
	        createTabConstrain.weighty = 1.0; // request any extra vertical space
	        createTabConstrain.anchor = GridBagConstraints.PAGE_START; // bottom of space
	        createTabConstrain.insets = new Insets(20,0,0,0);  // top padding
	        createTabConstrain.gridx = 0; // aligned with button 2
	        createTabConstrain.gridy = 1; // third row
	        panelLeft.add(createTabButton, createTabConstrain);//, BorderLayout.NORTH);
	        
	        GridBagConstraints createTabConstrain2 = new GridBagConstraints();
	        createTabConstrain2.fill = GridBagConstraints.HORIZONTAL; // turn off stretchyness 
	        createTabConstrain2.ipady = 0; // reset to default
	        createTabConstrain2.weighty = 1.0; // request any extra vertical space
	        createTabConstrain2.anchor = GridBagConstraints.PAGE_END; // bottom of space
	        createTabConstrain2.insets = new Insets(10,0,0,0);  // top padding
	        createTabConstrain2.gridx = 0; // aligned with button 2
	        createTabConstrain2.gridy = 2; // third row
	        panelLeft.add(populateWindow, createTabConstrain2);//,BorderLayout.SOUTH);
	        
	        createTabButton.setAlignmentX(CENTER_ALIGNMENT);
	        
	        // Add an Action Listener to 'Generate List' button to create new tabs
	        createTabButton.addActionListener(new CreateTabs());
	        // Add an Action Listener to 'Output' button for bottom output tab
	        populateWindow.addActionListener(this);
	    }
	    
	    /**
	     * Builds window frame and adds tab panes
	     */
	    public void buildFrame() {
            // Closes application when close button is clicked
	        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE); 
	        
	        // Add the JPanels to the frame
	        frame.getContentPane().add(tabbedPaneTop);
	        frame.getContentPane().add(tabbedPaneBottom, BorderLayout.SOUTH); 
	        frame.getContentPane().add(panelLeft, BorderLayout.WEST); 
	        
	        // Display the frame
	        frame.pack();
	        frame.setSize(550, 450);
	        frame.setVisible(true); 
	    }
	    
	    /**
	     * Builds top tab 1.
	     * Contains a table populated with setValueAt().
	     * Edits the Layout using GridBagLayout.
	     */
	    public void buildTopTab() {
            collection2.add(table2);
            	//refresh button
        	//collection1.add(refreshButton);
	    }
	    
	    /**
	     * Builds top tab 2.
	     * Contains a table populated using an array.
	     * Edits the Layout using GridBagLayout.
	     */
	    public void buildTopTab2() {
	        //collection1a.setLayout(new FlowLayout());
	        // adjust refresh button size
	        //refreshButton2.setPreferredSize(new Dimension (90,30));
	        //collection1a.add(refreshButton2);
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
	     * Edits Bottom 'Output' tab and Adds it to panel.
	     * Turns editable feature off
	     */
	    public void buildBottomTab(){
	        outputTextArea.setEditable(false);
	        outputTextArea.setSize(600, 300);
	        collection3.add(outputTextArea);        
	    }
	    
	    /**
	     * Edits Bottom 'Error' tab and Adds it to panel.
	     * Turns editable feature off
	     */
	    public void buildBottomTab2(){
	        errorTextArea.setEditable(false);
	        errorTextArea.setSize(600, 300);
	        collection4.add(errorTextArea);
	    }
	    
	    
	    /**
	     * Removes Tabs using an Icon and Mouse event
	     */
	     public void mouseClicked(MouseEvent e){
	        int tabNumber = tabbedPaneTop.indexAtLocation(e.getX(), e.getY());
	        if (tabNumber < 0) return;
	        else if (tabNumber == 0) {
	        	Rectangle rectangle = closeTabIcon0.getBounds();
	        	if (rectangle.contains(e.getX(), e.getY())) {
	        		tabbedPaneTop.removeTabAt(tabNumber);
	        	}
	        }
	        else if (tabNumber == 1) {
	        	Rectangle rectangle = closeTabIcon1.getBounds();
	        	if (rectangle.contains(e.getX(), e.getY())) {
	        		tabbedPaneTop.removeTabAt(tabNumber);
	        	}
	        }
//	        else {
//	        	Rectangle rectangle = closeTabIcon.getBounds();
//	        	if (rectangle.contains(e.getX(), e.getY())) {
//	        		tabbedPaneTop.removeTabAt(tabNumber);
//	        	}
//	        }
	    }
	    
	    public void mouseEntered(MouseEvent e) {}
	    public void mouseExited(MouseEvent e) {}
	    public void mousePressed(MouseEvent e) {}
	    public void mouseReleased(MouseEvent e) {}
	    
	    
	    /**
	     * Configure button's display and functionality to close tabs. 
	     * Adds a Mnemonic to close the window (Alt + C) and tool tips
	     */   
	    public void buildCloseTabButtons() {
	    }
	    
	    
	    /**
	     * Sets Action Listener action events
	     */
	    public void actionPerformed (ActionEvent e) {
	    	outputTextArea.setText("Scanning /ipcc/20c3m/atm/da/hfls/gfdl_cm2_0/run1...");	        
	    }
	    
	    /**
	     * Sets Action Listener action events.
	     * actionListenerIndex = 2
	     */
	    class CreateTabs implements ActionListener, MouseListener {
	    	CloseTabIcon closeTabIcon = new CloseTabIcon();
		    public void actionPerformed (ActionEvent e) {  
		    	tabLabel = "Collection " + actionListenerIndex;	
		    	if (actionListenerIndex == 2) {
		    		tabbedPaneTop.addTab(tabLabel, closeTabIcon, collection2);
		    	}
		    	else {
		    		tabbedPaneTop.addTab(tabLabel, closeTabIcon, new JPanel(new GridLayout(1,0)));
		    	}
		    	actionListenerIndex++; //TODO: Perhaps we need to set a limit # of tabs to open
		    }
		    
		    public void mouseClicked(MouseEvent e){
		    	int tabNumber = tabbedPaneTop.indexAtLocation(e.getX(), e.getY());
		    	int temp = actionListenerIndex;
		        if (tabNumber < 0) return;
		        else if (tabNumber == temp && closeTabIcon.ID == tabNumber){
		        	Rectangle rectangle = closeTabIcon.getBounds();
		        	if (rectangle.contains(e.getX(), e.getY())) {
		        		tabbedPaneTop.removeTabAt(tabNumber);
		        	}
		        }
		    }
		    
		    public void mouseEntered(MouseEvent e) {}
		    public void mouseExited(MouseEvent e) {}
		    public void mousePressed(MouseEvent e) {}
		    public void mouseReleased(MouseEvent e) {}
	    }
	    
	    
	    /**
	     * Sets customized table column sizes
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
	     * Configure button's display to refresh window. 
	     */
	    public void refreshButton (){
	    	//refreshButton.setToolTipText("Refresh");
	    	//refreshButton2.setToolTipText("Refresh");
	    }
	    
	    
	    /**
	     * The <code>MyTableModel</code> class creates table contents and specify 
	     * AbstractTableModel methods.
	     */
	    class MyTableModel extends AbstractTableModel {

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
	                {new Boolean(false), "OK", "Published", "115", "pcmdi.ipcc6"},
	        };
	                
	    
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
	            // The data/cell address is constant,
	            // no matter where the cell appears on screen.
	            if (col < 2) {
	                return false;
	            } else {
	                return true;
	            }
	        }
	        
	        /*
	         * Sets the value in the cell
	         */
	        public void setValueAt(Object value, int row, int col) {
	            data[row][col] = value;
	            fireTableCellUpdated(row, col); // update specified cell
	        }
	        
//	        public void valueChanged(ListSelectionEvent e) {
//	        	if (e.getValueIsAdjusting()) {
//	        		int i = e.getFirstIndex();
//	        		model.setValueAt(Boolean.TRUE, i, 0);
//	        	}
//	        }
	    }
	   
	    /**
	     * The <code>CloseTabIcon</code> class creates a close button 
	     * implementing the icon class.
	     */
	    class CloseTabIcon implements Icon {
	        private int x_pos;
	        private int y_pos;
	        private int width;
	        private int height;
	        private int ID;
	        private Icon fileIcon;
	        
	        public CloseTabIcon() {
	            //this.fileIcon=fileIcon;
	            width=16;
	            height=16;
	            ID = 0;
	        }
	        
	        public void paintIcon(Component c, Graphics g, int x, int y) {
	            this.x_pos=x;
	            this.y_pos=y;
	            
	            Color col=g.getColor();
	            
	            g.setColor(Color.black);
	            int y_p=y+2;
	            g.drawLine(x+1, y_p, x+12, y_p);
	            g.drawLine(x+1, y_p+13, x+12, y_p+13);
	            g.drawLine(x, y_p+1, x, y_p+12);
	            g.drawLine(x+13, y_p+1, x+13, y_p+12);
	            g.drawLine(x+3, y_p+3, x+10, y_p+10);
	            g.drawLine(x+3, y_p+4, x+9, y_p+10);
	            g.drawLine(x+4, y_p+3, x+10, y_p+9);
	            g.drawLine(x+10, y_p+3, x+3, y_p+10);
	            g.drawLine(x+10, y_p+4, x+4, y_p+10);
	            g.drawLine(x+9, y_p+3, x+3, y_p+9);
	            g.setColor(col);
	            if (fileIcon != null) {
	                fileIcon.paintIcon(c, g, x+width, y_p);
	            }
	            ID++;
	        }
	        
	        public int getIconWidth() {
	            return width + (fileIcon != null? fileIcon.getIconWidth() : 0);
	        }
	        
	        public int getIconHeight() {
	            return height;
	        }
	        
	        public Rectangle getBounds() {
	            return new Rectangle(x_pos, y_pos, width, height);
	        }
	    }	    
}


