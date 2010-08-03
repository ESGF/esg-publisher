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
 * <code>ESGPublisher3</code> Displays a Java Swing interface for the ESG Publisher tool.
 * 
 * @author Carla Hardy 
 * @version 06/15/2010
 */

import javax.swing.*;
import javax.swing.table.JTableHeader;	
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTable;
import javax.swing.table.TableColumn;
import javax.swing.text.SimpleAttributeSet;
import javax.swing.text.StyleConstants;

import java.awt.*;
import java.awt.event.*;
import java.awt.BorderLayout;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.GridLayout;
import java.awt.Insets;

public class ESGPublisher3 extends JPanel implements ActionListener {  
	private static final long serialVersionUID = 1L;
    JFrame frame;    
    ImageIcon esgLogo;
    JTabbedPane tabbedPaneTop, tabbedPaneBottom;    
    JSplitPane splitPanetop, splitPaneBottom;
    MyTableModel model;    
    JTable table;
    JTable tableTab2; //TODO: delete - created this table to use setValueAt	    
    JPanel collection1,collection2,collection3,collection4,innerPanel,panelLeft,progressBarPanel,
    		bottomTabPanel,bottomPanel,topPanel,initialTopPanel,borderPanelInitialMessage;
    JTextPane initialMessagePane;      
    JEditorPane outputTextArea,	errorTextArea;   
	GridBagConstraints menuConstrain, initialTopPanelConstrain, firstTabConstrain;	
	ProgressBarCreator progressBar;	    
    String tabLabel;
	int actionListenerIndex;
 
	public ESGPublisher3() {
		frame = new JFrame("ESG Data Node: Publisher's Graphical User Interface");
		tabbedPaneTop = new JTabbedPane();
	    tabbedPaneBottom = new JTabbedPane();
		splitPanetop = new JSplitPane();
	    splitPaneBottom = new JSplitPane();
		model = new MyTableModel();
		table = new JTable (model);
	    tableTab2 = new JTable (4,4);
		collection1 = new JPanel(new GridLayout()); //holds table
		collection2 = new JPanel(new GridLayout(1,0)); //table2
	    collection3 = new JPanel(new GridLayout(1,0)); //output
	    collection4 = new JPanel(new GridLayout(1,0)); //error
	    innerPanel = new JPanel(new GridLayout(1,1)); //holds dataset specifications
	    panelLeft = new JPanel(new GridBagLayout()); //holds buttons on left
	    progressBarPanel = new JPanel();
	    bottomTabPanel = new JPanel(new BorderLayout());
	    bottomPanel = new JPanel(new GridLayout()); //holds bottom tab panel and progress bar pan
	    topPanel = new JPanel(new GridLayout());
	    initialTopPanel = new JPanel(new GridBagLayout()); //contains initial message displayed
	    borderPanelInitialMessage = new JPanel();
		initialMessagePane = new JTextPane();
		outputTextArea = new JEditorPane();	 //Editor Panes to display output   
	    errorTextArea = new JEditorPane(); //Editor Panes to display error
		progressBar = new ProgressBarCreator();
		tabLabel = "";
		actionListenerIndex = 1;
	}
	
	/**
	 *****Builds the GUI****
	 */
	public void buildapp() {
	    buildFrame();
	    
	    buildInitialMessagePanel();
	    		   	       
	    tableSettings();
	    
        // Creates the scroll pane and add the table to it
        JScrollPane scrollPane = new JScrollPane(table);
        
        // Adds the scroll pane to the panel
        firstTabConstrain = new GridBagConstraints(0,0,1,1,1.0,0.5,GridBagConstraints.CENTER,
				GridBagConstraints.BOTH,new Insets(0,0,0,0),0,0);
        collection1.add(scrollPane);//, firstTabConstrain);
        	  
        
        ExpandablePanelCreator expandableLeftMenu = new ExpandablePanelCreator(splitPanetop, 
				tabbedPaneTop, collection1, table, model);
        
     // Inserts and edits *Expandable Menu* using GridBagConstraints Layout
	    menuConstrain = new GridBagConstraints(0,0,1,1,0.1,1.0,GridBagConstraints.PAGE_START, 
				GridBagConstraints.BOTH,new Insets(0,0,5,0),0,0);
	    panelLeft.add(new JScrollPane(expandableLeftMenu.getComponent()), menuConstrain);
        
        
        // Creates buttons in inner table at column 5 (DataSet)
	    ButtonRenderer buttonRenderer = new ButtonRenderer();		
	    TableButtonEditor tableButtonEditor = new TableButtonEditor(new JCheckBox(), 
	    			                          new InnerPaneCreator(tabbedPaneTop, scrollPane, collection1, table, tabLabel));
    	table.getColumnModel().getColumn(4).setCellRenderer(buttonRenderer);
    	table.getColumnModel().getColumn(4).setCellEditor(tableButtonEditor);

    	
        // Builds *Bottom Tabs*
        buildBottomTab();
        buildBottomTab2();
        
        
        // Populates table in tab - NOT USED NOW
        populateTable();

        tabbedPaneBottom.addTab("Output", collection3);
        tabbedPaneBottom.addTab("Error", collection4);
        tabbedPaneBottom.setForegroundAt(1, new Color(142, 35, 35));

        // Adds *Bottom Tab* and *Progress Bar* to panel
	    progressBarPanel.add(progressBar); //Use FlowLayout
        bottomTabPanel.add(tabbedPaneBottom); //Use BorderLayout
        bottomTabPanel.add(progressBarPanel, BorderLayout.SOUTH);

        // Adds an Action Listeners to 'Output' and 'Generate Tabs' button
        //populateWindow.addActionListener(this);

        //Creates split panes
        createTopSplitPane(panelLeft, initialTopPanel);
        createBottomSplitPane(topPanel, bottomTabPanel);//bottomPanel);
    }
    
    /**
     * Builds window frame and adds tab panes
     */
    public void buildFrame() {
        // Closes application when close button is clicked
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE); 
        
        //Add MenuBar to Frame
        MenuBarCreator mb = new MenuBarCreator(frame);
        JMenuBar jmb = mb.createMenu();
        frame.setJMenuBar(jmb);
        
        // Add the split panels to the frame
        frame.getContentPane().add(splitPaneBottom);
        
        // Display the frame
        frame.pack();
        frame.setSize(980, 650);
        frame.setVisible(true); 
    }    
    
    /**
     * Creates an initial message to be displayed when GUI is opened
     * Use of StyledDocument to edit the message
     * Adds the message to a panel to edit the border
     * Adds border panel to a final panel
     */
    public void buildInitialMessagePanel() {
        String initialMessageString = "Publisher Software. Version 1.0 Beta @ Copyright LLNL/PCMDI." +
        " Earth Systems Grid Center for Enabling Technologies." +
        " Funded by the US Department Of Energy";
    	initialMessagePane.setText(initialMessageString);
	    initialMessagePane.setPreferredSize(new Dimension(450, 150));
	    
	    SimpleAttributeSet attribute = new SimpleAttributeSet();
	    StyleConstants.setAlignment(attribute, StyleConstants.ALIGN_CENTER);
	    StyleConstants.setLineSpacing(attribute, (float) 1.0);
	    StyleConstants.setFontFamily(attribute, "Serif");
	    StyleConstants.setFontSize(attribute, 14);
	    StyleConstants.ColorConstants.setForeground(attribute, Color.DARK_GRAY);
	    
	    initialMessagePane.setParagraphAttributes(attribute, true);
	    initialMessagePane.setEditable(false);
	    
	    esgLogo = new ImageIcon("/Users/hardy21/projects/esg-publisher/src/java/main/esg/node/publisher_fe/ESGLogo.png");
	    JLabel labelImage = new JLabel();
	    labelImage.setIcon(esgLogo);
	    initialTopPanel.setBackground(Color.WHITE);
	    initialTopPanelConstrain = new GridBagConstraints(0,0,0,2,0.2,0,GridBagConstraints.NORTH,
				GridBagConstraints.HORIZONTAL,new Insets(-140,0,0,0),0,0);
	    initialTopPanel.add(labelImage, initialTopPanelConstrain);
	    
	    //borderPanelInitialMessage.add(initialMessagePane);
	    //Border initialMessageBorder = BorderFactory.createEmptyBorder(30, 20, 30, 20);
	    //Border border = BorderFactory.createEtchedBorder(EtchedBorder.LOWERED);
	    //initialMessagePane.setBorder(BorderFactory.createCompoundBorder(border, initialMessageBorder));
		initialTopPanelConstrain = new GridBagConstraints(0,2,0,2,0.2,0,GridBagConstraints.CENTER,
								GridBagConstraints.BOTH,new Insets(5,15,0,15),0,0);
	    initialTopPanel.add(initialMessagePane, initialTopPanelConstrain);
    }
    
    /**
     * Sets up the scrolling window size, table sorter and row selection for tables
     */
    public void tableSettings() {
	    table.setRowHeight(20);
	    table.setAutoCreateRowSorter(true); //table sorter
	    table.setRowSelectionAllowed(false);//selection disabler
	    customizeColumns(table);
	    //table.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);//turns off expandability with window
        table.setPreferredScrollableViewportSize(new Dimension(530, 280));
        table.setFillsViewportHeight(true);
    }
    
    /**
     * Creates a split pane for top panels
     */  
    public void createTopSplitPane(Component leftComponent, Component rightComponent) {
    	splitPanetop.setOrientation(JSplitPane.HORIZONTAL_SPLIT);
    	splitPanetop.setLeftComponent(leftComponent); //panelLeft
    	splitPanetop.setRightComponent(rightComponent); //initialTopPanel
    	splitPanetop.setOneTouchExpandable(true);
    	splitPanetop.setDividerLocation(360); // Sets the initial size of the divider
    	
    	Dimension minSplitPaneTopSize = new Dimension(360, 200);
    	leftComponent.setMinimumSize(minSplitPaneTopSize);
    	topPanel.add(splitPanetop);
    }
   
    
    /**
     * Creates a split pane for bottom panels
     */
    public void createBottomSplitPane(Component topComponent, Component bottomComponent) {
    	splitPaneBottom.setOrientation(JSplitPane.VERTICAL_SPLIT);
    	splitPaneBottom.setTopComponent(topComponent);//topPanel
    	splitPaneBottom.setBottomComponent(bottomComponent);//bottomPanel 
        splitPaneBottom.setOneTouchExpandable(true);        
        splitPaneBottom.setDividerLocation(420); // +Sets the initial size of the divider (higher=smaller)
        splitPaneBottom.setResizeWeight(0.8);
        
        Dimension minSplitPaneBottomSize = new Dimension(410, 200);
        bottomComponent.setMinimumSize(minSplitPaneBottomSize);
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
        outputTextArea.setSize(610, 300);
        String outputText = "Scanning /ipcc/20c3m/atm/da/hfls/gfdl_cm2_0/run1/19651...\n" +
        "Scanning /ipcc/20c3m/atm/da/hfls/gfdl_cm2_0/run1/19652...\n" +
        "Scanning /ipcc/20c3m/atm/da/hfls/gfdl_cm2_0/run1/19653...";
        outputTextArea.setText(outputText);	
        JScrollPane outputTextScrollPane = new JScrollPane(outputTextArea);
        outputTextScrollPane.setPreferredSize(new Dimension(1000, 220));//NOT WORKING
        outputTextArea.setBackground(new Color(185, 211, 238));
        collection3.add(outputTextScrollPane);        
    }
    
    /**
     * Edits Bottom 'Error' tab and Adds it to panel.
     * Turns editable feature off
     */
    public void buildBottomTab2(){
        errorTextArea.setEditable(false);
        errorTextArea.setSize(600, 300);
	    String errorText = "Error scanning /ipcc/20c3m/atm/da/hfls/gfdl_cm2_0/run1/19655\n" + 
	                    	"Error scanning /ipcc/20c3m/atm/da/hfls/gfdl_cm2_0/run1/19656\n" + 
	                    	"Error publishing /ipcc/20c3m/atm/da/hfls/gfdl_cm2_0/run1/19656\n" + "...";
	    errorTextArea.setText(errorText);
        errorTextArea.setForeground(new Color(142, 35, 35));//209, 146, 117));
        errorTextArea.setBackground(Color.WHITE);
        collection4.add(errorTextArea);
    }
    
    /**
     * Sets Action Listener action events
     */
    public void actionPerformed (ActionEvent e) {
    	        
    }  	    
    	    
    /**
     * Sets customized table column sizes
     */
    private void customizeColumns (JTable table) {

    	TableColumn column = null;

    	for (int i = 0; i < 7; i++){
    		column = table.getColumnModel().getColumn(i);
    		if ( i == 4 ) {
    			column.setPreferredWidth(200);
    		} 
    		else if ( i == 2 && i == 6) {
    			column.setPreferredWidth(70);
    		}
    		else if ( i == 6) {
    			column.setPreferredWidth(90);
    		}
    		else {
    			column.setPreferredWidth(65);
    		}
    	}
    }
}