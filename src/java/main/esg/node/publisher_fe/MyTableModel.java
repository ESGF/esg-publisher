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
 * The class <code>MyTableModel</code> Initializes tables contents and specifies 
 * AbstractTableModel methods.
 * 
 * @author Carla Hardy 
 * @version 06/15/2010
 */

import javax.swing.table.AbstractTableModel;

class MyTableModel extends AbstractTableModel {
	private static final long serialVersionUID = 1L;
	String[] okColumnArray = new String[15];	
	private String[] columnNames = {"Pick", "OK/Error", "Status", "ID", "DataSet", "Project",
									"Model", "Experiment"}; 
    private Object[][] data = {
            {new Boolean(true), "OK", "Published", "106", "pcmdi.ipcc4.1", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "OK", "Published", "107", "pcmdi.ipcc4.2", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "Error", "Scanned", "108", "pcmdi.ipcc4.3", "ipcc4", "gfdl_cm2_0", "20c3m"},
            {new Boolean(true), "OK", "Published", "109", "pcmdi.ipcc4.4", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "OK", "Published", "110", "pcmdi.ipcc4.5", "ipcc4", "gfdl_cm2_0", "20c3m"},
            {new Boolean(true), "OK", "Scanned", "111", "pcmdi.ipcc4.6", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "OK", "Published", "112", "pcmdi.ipcc4.7", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "OK", "Published", "113", "pcmdi.ipcc4.8", "ipcc4", "gfdl_cm2_0", "20c3m"},
            {new Boolean(true), "OK", "Scanned", "114", "pcmdi.ipcc4.9", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "OK", "Published", "115", "pcmdi.ipcc4.10", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "OK", "Published", "115", "pcmdi.ipcc4.11", "ipcc4", "gfdl_cm2_0", "20c3m"},
            {new Boolean(true), "OK", "Published", "115", "pcmdi.ipcc4.12", "ipcc4", "cnrm_cm3", "20c3m"},
            {new Boolean(true), "OK", "Scanned", "115", "pcmdi.ipcc4.13", "ipcc4", "gfdl_cm2_0", "20c3m"},
            {new Boolean(true), "OK", "Published", "115", "pcmdi.ipcc4.14", "ipcc4", "cnrm_cm3", "20c3m"},
    };
            
    /**
     * Counts the number of columns in the table
     * @return the number of columns
     */
    public int getColumnCount() {
        return columnNames.length;
    }

    /**
     * Counts the number of rows in the table
     * @return the number of rows 
     */
    public int getRowCount() {
        return data.length;
    } 
    
    /**
     * Returns column names
     * @param the column number
     * @return the column name
     */
    public String getColumnName(int col) {
        return columnNames[col];
    }

    /**
     * Returns the value at the specified location in the table
     * @param row  row number
     * @param col  column number
     * @return an object at the specified location
     */
    public Object getValueAt(int row, int col) {
        return data[row][col];
    }

    /**
     * JTable uses this method to determine the default renderer / 
     * editor for each cell. Used by the first column to display check boxes
     * @param row  number
     * @return the class of the value at the specified location in the table 
     */
	public Class getColumnClass(int row){
        return getValueAt(0, row).getClass();
    }	
    
    /**
     * Returns true if cell is editable
     * Have to be true to allow setValueAt to change values
     * @param row  row number
     * @param col  column number
     * @return true or false
     */
    public boolean isCellEditable(int row, int col) {
        // The data/cell address is constant,
        // no matter where the cell appears on screen.
        if (col == 0 || col == 4) {
            return true;
        } else {
            return false;
        }
    }
    
    /**
     * Sets the value at the specified location in the table
     * @param value  object value
     * @param row  row number
     * @param col  column number
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