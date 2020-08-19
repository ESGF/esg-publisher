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
 * The class <code>ExpandablePanelCreator</code> creates the left expandable 
 * menu panel. Buttons, textfields and combo boxes are used to query/edit data. 
 * 
 * @author Carla Hardy 
 * @version 07/12/2010
 */
package esg.node.publisher_fe;
import java.awt.*;
import java.awt.event.*;
import java.awt.font.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.LinkedList;
import java.util.ListIterator;

import javax.swing.*;
 
public class ExpandablePanelCreator extends MouseAdapter implements ActionListener{
    ActionPanel[] aps;
    JPanel[] panels;
    String[] projectList = {"ipcc3", "ipcc4", "ipcc5"};
    String[] filterFileList = {"Search for files *.nc ", "All Files"};
    String[] creatorList = {"-Any-", "--", "--"};
    String[] experimentList = {"-Any-", "--", "--"};
    String[] modelList = {"gfdl_cm2_0", "gfdl_cm3_0", "gfdl_cm4_0"};
    String[] publisherList = {"-Any-", "--", "--"};
    String[] submodelList = {"-Any-", "--", "--"};
    String[] timeFrequencyList = {"-Any-", "--", "--"};
    LinkedList<TabCreator> remainingTabsList;
   
    static String workOnlineString;
    static String workOfflineString;
	final int MAX = 20;
	int linkListIndex;
    
    JRadioButton workOnlineButton, workOfflineButton;    
    ButtonGroup radioButtonGroup;    
    JComboBox projectComboBox,fileSearchComboBox,projectQueryComboBox,
    		creatorComboBox,experimentComboBox,modelComboBox,publisherComboBox,
    		submodelComboBox,timeFrequencyComboBox;    
    JButton directory,file,selectAll,selectAll2,selectAll3,unselectAll,
    		unselectAll2,unselectAll3,remove;    
    MyTableModel tableModel;    
    JPanel collectionPanel;        
    JSplitPane spTop;
    JTabbedPane tpTop;    
    JFileChooser fileChooser;
    FileExtensionFilter fileExtensionFilter;
    LinkedList<Object> tabList;
    int counter;
        
    public ExpandablePanelCreator(JSplitPane splitPaneTop, JTabbedPane tabbedPaneTop, 
    		JPanel collection) {               
    	spTop = splitPaneTop;
    	tpTop = tabbedPaneTop;
    	collectionPanel = collection;
    	
    	workOnlineString = "On-line";
        workOfflineString = "Off-line";
		remainingTabsList =  new LinkedList<TabCreator>();

    	workOnlineButton = new JRadioButton(workOnlineString);
        workOfflineButton = new JRadioButton(workOfflineString);
    	radioButtonGroup = new ButtonGroup();         
        projectComboBox = new JComboBox(projectList);
        fileSearchComboBox = new JComboBox(filterFileList);
        projectQueryComboBox = new JComboBox(projectList);
        creatorComboBox = new JComboBox(creatorList);
        experimentComboBox = new JComboBox(experimentList);
        modelComboBox = new JComboBox(modelList);
        publisherComboBox = new JComboBox(publisherList);
        submodelComboBox = new JComboBox(submodelList);
        timeFrequencyComboBox = new JComboBox(timeFrequencyList);
        directory = new JButton("Directory");
        file = new JButton("File");
        selectAll = new JButton("Select All");
        selectAll2 = new JButton("Select All");
        selectAll3 = new JButton("Select All");
        unselectAll = new JButton("Unselect All");
        unselectAll2 = new JButton("Unselect All");
        unselectAll3 = new JButton("Unselect All");
        remove = new JButton("Remove");
        fileChooser = new JFileChooser();
        fileExtensionFilter = new FileExtensionFilter();
        counter = 1;
        linkListIndex = 0;
        tableModel = new MyTableModel();
        tabList = new LinkedList<Object>();
        
        assembleActionPanels();
        assemblePanels();
    }
 
    /**
     * Expands the panel with a press of the mouse
     * Uses togglePanelVisibility(ActionPanel ap) method
     */
    public void mousePressed(MouseEvent e) {
        ActionPanel ap = (ActionPanel)e.getSource();
        if(ap.contains(e.getPoint())) { //ap.target.contains(e.getPoint()) 
            ap.toggleSelection();
            togglePanelVisibility(ap);
        }
    }	    
 
    /**
     * Makes the panels visible/not visible.
     * Uses getPanelIndex(ActionPanel ap)
     * @param ap  the action panel
     */
    private void togglePanelVisibility(ActionPanel ap) {
        int index = getPanelIndex(ap);
        if(panels[index].isShowing())
            panels[index].setVisible(false);
        else
            panels[index].setVisible(true);
        ap.getParent().validate();
    }
 
    /**
     * Returns the panel index
     * @param ap  the action panel
     * @return the panel index
     */
    private int getPanelIndex(ActionPanel ap) {
        for(int j = 0; j < aps.length; j++)
            if(ap == aps[j])
                return j;
        return -1;
    }
 
    /**
     * Assembles the action panels.
     * Creates a String array of the panel names
     */
    private void assembleActionPanels() {
        String[] ids = { "Specify Project and Dataset", "Data Extraction", "Data Publication", 
        		"Dataset Query", "Dataset Deletion" };
        aps = new ActionPanel[ids.length];
        for(int j = 0; j < aps.length; j++) {
            aps[j] = new ActionPanel(ids[j], this);
        }
    }
    
    /**
     * Assembles all the panels.
     * Uses GridBagConstraints to format the layout
     */
    private void assemblePanels() {
        GridBagConstraints gbc = new GridBagConstraints();

        //Panel 1 - Specify Project and dataset             
        JPanel p1 = new JPanel(new GridBagLayout());
        gbc = new GridBagConstraints(0,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        JLabel project = new JLabel("Project");
        project.setForeground(new Color(0,0,128)); //change color
        p1.add(project, gbc);
        gbc = new GridBagConstraints(0,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p1.add(new JLabel("Set additional mandatory"), gbc);
        gbc = new GridBagConstraints(0,4,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p1.add(new JLabel("Work"), gbc);
        gbc = new GridBagConstraints(0,6,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p1.add(new JLabel("Filter File Search"), gbc);
        gbc = new GridBagConstraints(0,8,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p1.add(new JLabel("Generate list from"), gbc);
        
        gbc = new GridBagConstraints(1,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,18,5,5),0,0);
        projectComboBox.addActionListener(this); //ActionListener
        p1.add(projectComboBox, gbc);
        gbc = new GridBagConstraints(1,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,18,5,5),0,0);
        p1.add(new JButton("Fields"), gbc);        
        gbc = new GridBagConstraints(1,4,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,18,5,5),0,0); 
    	workOnlineButton.setSelected(true);
        p1.add(workOnlineButton, gbc);
        gbc = new GridBagConstraints(2,4,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,-80,5,5),0,0);        
        p1.add(workOfflineButton, gbc); 
        radioButtonGroup.add(workOnlineButton);
        radioButtonGroup.add(workOfflineButton);
        gbc = new GridBagConstraints(1,6,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,18,5,5),0,0);
        p1.add(fileSearchComboBox, gbc);
        fileSearchComboBox.setEditable(true);
        fileSearchComboBox.addActionListener(this); //ActionListener
        gbc = new GridBagConstraints(1,8,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,18,5,5),0,0);
        directory.setMargin(new Insets(3,12,3,12));
        directory.addActionListener(this); //ActionListener
        p1.add(directory, gbc);
        gbc = new GridBagConstraints(2,8,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,-62,5,5),0,0);
        file.setMargin(new Insets(3,13,3,13));
        file.addActionListener(this); //ActionListener
        p1.add(file, gbc);

        
        //Panel 2 - Data Extraction
        JPanel p2 = new JPanel(new GridBagLayout());
        gbc = new GridBagConstraints(0,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p2.add(new JLabel("Dataset"), gbc);
        gbc = new GridBagConstraints(0,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p2.add(new JLabel("Data extraction"), gbc);
        gbc = new GridBagConstraints(0,4,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p2.add(new JLabel("Update extraction"), gbc);
        
        gbc = new GridBagConstraints(1,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,40,5,5),0,0);
        selectAll.setForeground(new Color(25,25,112)); //change color
        selectAll.setMargin(new Insets(3,3,3,3));
        p2.add(selectAll, gbc);
        selectAll.addActionListener(this); //ActionListener
        gbc = new GridBagConstraints(2,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,-70,5,5),0,0);
        unselectAll.setMargin(new Insets(3,3,3,3));
        p2.add(unselectAll, gbc);
        unselectAll.addActionListener(this); //ActionListener
        gbc = new GridBagConstraints(1,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,40,5,5),0,0);
        p2.add(new JButton("Create/Replace"), gbc);
        gbc = new GridBagConstraints(1,4,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,40,5,5),0,0);
        p2.add(new JButton("Append/Update"), gbc);
 
        
        //Panel 3 - Data Publication
        JPanel p3 = new JPanel(new GridBagLayout());
        gbc = new GridBagConstraints(0,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p3.add(new JLabel("Dataset"), gbc);
        gbc = new GridBagConstraints(0,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p3.add(new JLabel("Release Data"), gbc);

        gbc = new GridBagConstraints(1,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,65,5,5),0,0);
        selectAll2.setForeground(new Color(25,25,112)); //change color
        selectAll2.setMargin(new Insets(3,3,3,3));
        p3.add(selectAll2, gbc);
        selectAll2.addActionListener(this); //ActionListener
        gbc = new GridBagConstraints(2,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,-20,5,5),0,0);
        unselectAll2.setMargin(new Insets(3,3,3,3));
        p3.add(unselectAll2, gbc);
        unselectAll2.addActionListener(this); //ActionListener
        gbc = new GridBagConstraints(1,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,65,5,5),0,0);
        p3.add(new JButton("Publish"), gbc);
        
        
        //Panel 4 - Dataset Query
        JPanel p4 = new JPanel(new GridBagLayout());
        gbc = new GridBagConstraints(0,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Project"), gbc);
        gbc = new GridBagConstraints(0,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Creator"), gbc);
        gbc = new GridBagConstraints(0,4,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Experiment"), gbc);
        gbc = new GridBagConstraints(0,6,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Model"), gbc);
        gbc = new GridBagConstraints(0,8,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Publisher"), gbc);
        gbc = new GridBagConstraints(0,10,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Submodel"), gbc);
        gbc = new GridBagConstraints(0,12,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Time Frequency"), gbc);
        gbc = new GridBagConstraints(0,14,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Creation time"), gbc);
        gbc = new GridBagConstraints(0,16,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Id"), gbc);
        gbc = new GridBagConstraints(0,18,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Name"), gbc);
        gbc = new GridBagConstraints(0,20,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p4.add(new JLabel("Parent"), gbc);
        
        gbc = new GridBagConstraints(1,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,0,5,5),0,0);
        projectQueryComboBox.setForeground(new Color(0,0,128));
        p4.add(projectQueryComboBox, gbc);        
        gbc = new GridBagConstraints(1,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(creatorComboBox, gbc);        
        gbc = new GridBagConstraints(1,4,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(experimentComboBox, gbc);        
        gbc = new GridBagConstraints(1,6,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(modelComboBox, gbc);        
        gbc = new GridBagConstraints(1,8,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(publisherComboBox, gbc);        
        gbc = new GridBagConstraints(1,10,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(submodelComboBox, gbc);       
        gbc = new GridBagConstraints(1,12,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(timeFrequencyComboBox, gbc);
        
        gbc = new GridBagConstraints(1,14,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(new JTextField(), gbc);        
        gbc = new GridBagConstraints(1,16,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(new JTextField(), gbc);        
        gbc = new GridBagConstraints(1,18,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(new JTextField(), gbc);        
        gbc = new GridBagConstraints(1,20,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,0,5,5),0,0);
        p4.add(new JTextField(), gbc);        
            JPanel p5 = new JPanel(new GridBagLayout());
            gbc = new GridBagConstraints(1,22,1,1,0.1,0,GridBagConstraints.WEST, 
            GridBagConstraints.NONE,new Insets(0,-50,5,5),0,0);
            p5.add(new JButton("Query Data Information"));
            p4.add(p5, gbc);
            
            
        //Panel 6 - Dataset Deletion
        JPanel p6 = new JPanel(new GridBagLayout());
        gbc = new GridBagConstraints(0,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p6.add(new JLabel("Dataset"), gbc);
        gbc = new GridBagConstraints(0,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.BOTH,new Insets(5,5,5,0),0,0);
        p6.add(new JLabel("Dataset Deletion"), gbc);
        
        gbc = new GridBagConstraints(1,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,40,5,5),0,0);
        selectAll3.setMargin(new Insets(3,3,3,3));
        selectAll3.setForeground(new Color(25,25,112)); //change color
        p6.add(selectAll3, gbc);
        selectAll3.addActionListener(this); //ActionListener
        gbc = new GridBagConstraints(2,0,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,-22,5,5),0,0);
        unselectAll3.setMargin(new Insets(3,3,3,3));
        p6.add(unselectAll3, gbc);
        unselectAll3.addActionListener(this); //ActionListener
        gbc = new GridBagConstraints(1,2,1,1,0.1,0,GridBagConstraints.WEST, 
        GridBagConstraints.NONE,new Insets(5,40,5,5),0,0);
        remove.setForeground(new Color(142, 35, 35));
        remove.setMargin(new Insets(3,13,3,13));
        p6.add(remove, gbc);
        
        //Add each panel to an array
        panels = new JPanel[] { p1, p2, p3, p4, p6 };
    }
 
    /**
     * Edits the visibility and layout of the panels
     * @return  the panel with action panels and menu panel
     */
    protected JPanel getComponent() {
        JPanel panel = new JPanel(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(1,3,0,3);
        gbc.weightx = 1.0;
        gbc.fill = GridBagConstraints.HORIZONTAL;
        gbc.gridwidth = GridBagConstraints.REMAINDER;
        for(int j = 0; j < aps.length; j++) {
            panel.add(aps[j], gbc);
            panel.add(panels[j], gbc);
            panels[j].setVisible(false);
        }
        JLabel padding = new JLabel();
        gbc.weighty = 1.0;
        panel.add(padding, gbc);
        return panel;
    }
 
    /**
     * Adds action events to buttons inside each panel
     */
    public void actionPerformed(ActionEvent e) {  	
    	if(e.getSource() == projectComboBox) {
    		@SuppressWarnings("unused")
			int selectedIndex = projectComboBox.getSelectedIndex();
    		String valueSelected = projectComboBox.getSelectedItem().toString();
    		System.out.println("Selected:" + valueSelected);
    	} 
    	else if (e.getSource() == fileSearchComboBox) {
    		@SuppressWarnings("unused")
			int selectedIndex = fileSearchComboBox.getSelectedIndex();
    		String valueSelected = fileSearchComboBox.getSelectedItem().toString();
    		System.out.println("Selected:" + valueSelected);
    	}
    	else if (e.getSource() == directory) {
            fileChooser.setFileSelectionMode(JFileChooser.FILES_AND_DIRECTORIES);//DIRECTORIES_ONLY);
    		fileChooser.addChoosableFileFilter(fileExtensionFilter);
    		int returnVal = fileChooser.showOpenDialog(spTop);
    		if (returnVal == JFileChooser.APPROVE_OPTION) {
                File fileSelected = fileChooser.getSelectedFile();
        		System.out.println("Selected button Directory" + fileSelected);
    		} 
    	}
    	else if (e.getSource() == file) {    			
        	if (tpTop.getTabCount() == 0 ) {
        		clearAllTabs();
        		CreateTabs createTabs = new CreateTabs(spTop, collectionPanel, tpTop, counter);
        		createTabs.createFirstTab(); 
        		tabList.addFirst(createTabs);
        		counter = 1;
        	}        	
        	else {
                TabCreator tabCreator = new TabCreator(tpTop, counter);
                tabCreator.createRemainingTabs();
                tabList.add(tabCreator);
                System.out.println("\nlinkedList" + tabList);
        	}
        	counter++;
    	}
    	else if (e.getSource() == selectAll) {  
    		int index = 0;
    		int selectedIndex = tpTop.getSelectedIndex() + 1;
    		String tabTitle = tpTop.getToolTipTextAt(selectedIndex-1);
    		System.out.println(selectedIndex);
    		ListIterator<Object> iterator = tabList.listIterator();
    		CreateTabs ct = null;
    		TabCreator tc = null;
    		String cls = null;
    		boolean tabCreatorClass = false;
    		boolean removedTab = false;
    		System.out.println("Title: " + tabTitle);
    		while (iterator.hasNext()) {
    			Object o = iterator.next();
    			cls = o.getClass().getName();
    			if (cls == "CreateTabs") {
    				ct = (CreateTabs)o;
    				if (selectedIndex == 1) {
    					cls = "CreateTabs";    					
    					index = selectedIndex;
    					removedTab = ct.removedTab;
    					System.out.println(cls + " " + index);
    				}
    			}
    			else if (cls.equalsIgnoreCase("TabCreator")) {
    				System.out.println("*this is a TabCreator*");
    				tc = (TabCreator)o;
    				if (tc.removedTab == true){
    					index = selectedIndex;
    					removedTab = tc.removedTab;
    					tabTitle = null;
    				}
    				else if (tc.removedTab == false && tabTitle == tc.returnLabelName()) {
    					//cls = TabCreator.class;
    					index = selectedIndex;
        				tabCreatorClass = true;
    					removedTab = tc.removedTab;
    					System.out.println("tab title: " + tabTitle + " tab title label: " + tc.returnLabelName());
    					System.out.println(cls + " Index:" + index + " Removed?" + removedTab);//class CreateTabs			
    				}				
    			}
    		}
			if (index == 1 && tabTitle == ct.returnLabelName() && ct.removedTab == false) {
				System.out.println("o equals CT" + ct.returnLabelName());
				((CreateTabs)tabList.get(0)).selectCheckbox();
			}
			else if (index == 1 && tabCreatorClass == true) {
				System.out.println("o equals TC");
				((TabCreator)tabList.get(0)).selectCheckbox();
			}
			else if (index == 1 && ct.removedTab == true && tpTop.getTabCount() >= 1) {
				deleteTabs(1);
				System.out.println("Collection 1 DELETED " + tabList);
					((TabCreator)tabList.get(0)).selectCheckbox(); //fix this -> if empty
			}
			else if (index == 1 && tc.removedTab == true && tpTop.getTabCount() >= 1) {
				System.out.println("\nlinkedList:" + tabList);
				deleteTabs(1);
				System.out.println("Collection DELETED " + tabList);
					((CreateTabs)tabList.get(0)).selectCheckbox(); //fix this -> if empty
			}	
			else if ((cls == "TabCreator" && tc.removedTab == true)) {
				System.out.println("\nlinkedList:" + tabList);
				//deleteTabs(index - 1);
				if (tpTop.getTabCount() >= 2) {
					((TabCreator)tabList.get(index - 1)).selectCheckbox();
				}
				System.out.println("removed tab:" + index + "\nlinkedList:" + tabList);
			}			
			else if (cls== "TabCreator" && removedTab == false) {
				System.out.println("o equals TC");
				((TabCreator)tabList.get(index - 1)).selectCheckbox();
				cls = "";
				removedTab = false;
			}
    	}
//    	else if (e.getSource() == selectAll2) {
//    		for (int i = 0; i < tableModel.getRowCount(); i++)
//    			tableModel.setValueAt(true, i, 0);   		
//    	}
//    	else if (e.getSource() == selectAll3) {
//    		for (int i = 0; i < tableModel.getRowCount(); i++)
//    			tableModel.setValueAt(true, i, 0);   		
//    	}
    	else if (e.getSource() == unselectAll) {
    		int index = 0;
    		int selectedIndex = tpTop.getSelectedIndex() + 1;
    		String tabTitle = tpTop.getToolTipTextAt(selectedIndex-1);
    		System.out.println(selectedIndex);
    		ListIterator<Object> iterator = tabList.listIterator();
    		CreateTabs ct = null;
    		TabCreator tc = null;
    		Class cls = null;
    		boolean removedTab = false;
    		System.out.println("Title: " + tabTitle);
    		while (iterator.hasNext()) {
    			Object o = iterator.next();
    			cls = o.getClass();
    			if (cls.equals(CreateTabs.class)) {
    				ct = (CreateTabs)o;
    				if (selectedIndex == 1) {//ct.returnIndex()) {
    					cls = CreateTabs.class;    					
    					index = selectedIndex;
    					System.out.println(cls + " " + index);//class CreateTabs
    				}
    			}
    			else if (cls.equals(TabCreator.class)) {
    				System.out.println("*this is a TabCreator*");
    				tc = (TabCreator)o;
    				if (tc.removedTab == true){
    					index = selectedIndex;
    					removedTab = tc.removedTab;
    					tabTitle = null;
    				}
    				else if (tabTitle == tc.returnLabelName()) {//selectedIndex == tc.returnIndex() ) {
    					cls = TabCreator.class;
    					index = selectedIndex;
    					removedTab = tc.removedTab;
    					System.out.println("tab title: " + tabTitle + " tab title label: " + tc.returnLabelName());
    					System.out.println(cls + " Index:" + index + " Removed?" + removedTab);//class CreateTabs			
    				}				
    			}
    		}
			if (index == 1) {
				System.out.println("o equals CT");
				((CreateTabs)tabList.get(0)).unselectCheckbox();
			}
			else if (cls.equals(TabCreator.class) && removedTab == true) {
				System.out.println("\nlinkedList:" + tabList);
				deleteTabs(index - 1);
				((TabCreator)tabList.get(index - 1)).unselectCheckbox();
				System.out.println("removed tab:" + index + "\nlinkedList:" + tabList);
			}
			else if (cls.equals(TabCreator.class) && removedTab == false) {
				System.out.println("o equals TC");
				((TabCreator)tabList.get(index - 1)).unselectCheckbox();
				removedTab = false;
			}
//			else if (cls.equals(TabCreator.class)) {
//				System.out.println("o equals TC");
//				((TabCreator)tabList.get(index - 1)).unselectCheckbox();
//			}    	
    	}
//    	else if (e.getSource() == unselectAll2) {
//    		for (int i = 0; i < tableModel.getRowCount(); i++)
//    			tableModel.setValueAt(false, i, 0);
//    	}
//    	else if (e.getSource() == unselectAll3) {
//    		for (int i = 0; i < tableModel.getRowCount(); i++)
//    			tableModel.setValueAt(false, i, 0);
//    	}
    }
    
    public void deleteTabs(int index) {
    	if (tabList.isEmpty() == false) {  	
	    		tabList.remove(index);
    	}
    }
    
    /**
     * Removes all tabs from the Linked List 
     */
    public void clearAllTabs() {
    	if (tabList.isEmpty() == false) {
    		tabList.clear();
			System.out.println("removing...");
    	}
    }
}
    

/**
 * The class <code>ActionPanel</code> creates the graphical elements of the  
 * action panel. 
 * Draws the triangle to open and close. 
 * Edits the text and its layout.
 * 
 * @author Carla Hardy 
 * @version 07/12/2010
 */
class ActionPanel extends JPanel { 
	private static final long serialVersionUID = 1L;	
	String text;
    Font font;
    private boolean selected;
    BufferedImage open, closed;
    Rectangle target;
    final int
        OFFSET = 30,
        PAD    =  5;
 
    /**
     * Constructor
     * @param text  the panel label
     * @param ml  the mouse listener
     */
    public ActionPanel(String text, MouseListener ml) {
        this.text = text;
        addMouseListener(ml);
        font = new Font("sans-serif", Font.PLAIN, 12);
        selected = false;
        setBackground(new Color(185, 211, 238));//200,200,200
        setPreferredSize(new Dimension(330,20));
        setBorder(BorderFactory.createRaisedBevelBorder());
        setPreferredSize(new Dimension(330,20));
        createImages();
        setRequestFocusEnabled(true);
    }
 
    /**
     * Toggle action panel selection
     */
    public void toggleSelection() {
        selected = !selected;
        repaint();
    }
 
    /**
     * Overrides the paintComponent Class of JComponent to edit elements
     * KEY_ANTIALIASING blends the existing colors of the pixels along 
     * the boundary of a shape. Achieves a smooth image.
     * LINEMETRICS allows access to the metrics needed to layout characters
     * along a line and to layout of a set of lines
     */
    @Override
    protected void paintComponent(Graphics g) {
        super.paintComponent(g);
        Graphics2D g2 = (Graphics2D)g;
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                            RenderingHints.VALUE_ANTIALIAS_ON);
		int w = getWidth();
        int h = getHeight();
        if (selected) {
            g2.drawImage(open, PAD, 0, this);//PAD moves the triangle along the x-axis
        }
        else {
            g2.drawImage(closed, PAD, 0, this);//PAD moves the triangle along the x-axis
        }
        g2.setFont(font);
        FontRenderContext frc = g2.getFontRenderContext();
        LineMetrics lm = font.getLineMetrics(text, frc);
        float height = lm.getAscent() + lm.getDescent();
        float x = OFFSET;
        float y = (h + height)/2 - lm.getDescent();
        g2.drawString(text, x, y);
    }
 
    /**
     * Creates the triangles inside the action panels
     */
    private void createImages() {
        int w = 20;
        int h = getPreferredSize().height;
        target = new Rectangle(2, 0, 20, 18);
        
        //triangle facing down (open)
        open = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
        Graphics2D g2 = open.createGraphics();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                            RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setPaint(getBackground());
        g2.fillRect(0,0,w,h);
        int[] x = { 2, w/2, 18 };
        int[] y = { 4, 15,   4 };
        Polygon p = new Polygon(x, y, 3); //triangle
        g2.setPaint(new Color(250,250,250)); //open arrow
        g2.fill(p);
        g2.setPaint(new Color(84,84,84)); //border
        g2.draw(p);
        g2.dispose();
        
        //triangle facing right (closed)
        closed = new BufferedImage(w, h, BufferedImage.TYPE_INT_RGB);
        g2 = closed.createGraphics();
        g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING,
                            RenderingHints.VALUE_ANTIALIAS_ON);
        g2.setPaint(getBackground());
        g2.fillRect(0,0,w,h);
        x = new int[] { 3, 13,   3 };
        y = new int[] { 4, h/2, 16 };
        p = new Polygon(x, y, 3);
        g2.setPaint(new Color(34,24,130)); //closed arrow848484
        g2.fill(p);
        g2.setPaint(new Color(34,24,130)); //border
        g2.draw(p);
        g2.dispose();
    }
}