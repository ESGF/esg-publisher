import javax.swing.JTable;
import javax.swing.table.TableColumn;

/**
* Sets customized table column sizes
*/
public class TableColumnEditor {
	JTable table;
	
	public TableColumnEditor(JTable table) {	
		this.table = table;
	}
	
	public void editTable() {
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