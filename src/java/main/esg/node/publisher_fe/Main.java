import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.commons.logging.impl.*;


/**
 Description:
 The main program to bootstrap the Publisher GUI
 */
public class Main {
		public static void main(String[] args) {
			try {
	             UIManager.setLookAndFeel("javax.swing.plaf.metal.MetalLookAndFeel");
	         } catch (UnsupportedLookAndFeelException ex) {
	             ex.printStackTrace();
	         } catch (IllegalAccessException ex) {
	             ex.printStackTrace();
	         } catch (InstantiationException ex) {
	             ex.printStackTrace();
	         } catch (ClassNotFoundException ex) {
	             ex.printStackTrace();
	         }
	         /* Turn off metal's use of bold fonts */
	         //UIManager.put("swing.boldMetal", Boolean.FALSE);
				
		ESGPublisher3 esgDraft = new ESGPublisher3();
		esgDraft.buildapp();
		System.out.println("done");
    }
}
