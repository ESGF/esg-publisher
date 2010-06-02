#!/usr/bin/env python
#
# The Publisher Editor Viewer Controls -  pub_editorviewer module
#
###############################################################################
#                                                                             #
# Module:       pub_editorviewer module                                       #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  View the output (i.e., errors, debug, etc.) of specific       #
#               datasets.                                                     #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFont
from tkMessageBox import showerror
import gui_support
import pub_controls


#----------------------------------------------------------------------------------------
# Begin the creation of the publisher editor view controls window
#----------------------------------------------------------------------------------------
class create_publisher_editor_output:
   """
   Display the two output windows (i.e., 'Output' and 'Error') at the bottom of the page -- located in the bottom right.
   """
   def __init__( self, root ):

        self.parent = root
        self.output_parent = root.pane2.pane( 'EditPaneBottom' )

        #--------------------------------------------------------------------------------
        # Create and pack the NoteBook
        #--------------------------------------------------------------------------------
        self.parent.bottom_notebook = Pmw.NoteBook(self.output_parent)
        self.parent.bottom_notebook.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        #--------------------------------------------------------------------------------
        # Add the "Output" page to the notebook
        #--------------------------------------------------------------------------------
        tabFont = tkFont.Font(self.parent, family = pub_controls.collection_font_type, size=pub_controls.tab_font_size)
        output_page = self.parent.bottom_notebook.add('Output', tab_bg='lightgreen', tab_font = tabFont)
        self.parent.balloon.bind(output_page, "Information output window.")
        self.parent.bottom_notebook.tab('Output').focus_set()
        self.log_output_page(output_page)

        #--------------------------------------------------------------------------------
        # Add the "Error" page to the notebook
        #--------------------------------------------------------------------------------
        error_page = self.parent.bottom_notebook.add('Error', tab_bg='pink', tab_font = tabFont)
        self.parent.balloon.bind(error_page, "Main error output window.")
        self.log_error_page(error_page)

   def log_output_page( self, parent ):
        #--------------------------------------------------------------------------------
        # Create the Output ScrolledFrame
        #--------------------------------------------------------------------------------
        txtFont = tkFont.Font(self.parent, family = pub_controls.tab_font_type, size=pub_controls.tab_font_size)
        self.parent.log_output_window = Pmw.ScrolledText(parent,
                  text_state='disabled',
	          text_background='lightgreen',
                  text_relief = 'sunken',
                  text_borderwidth = 2,
                  text_font = txtFont,
        )
        self.parent.log_output_window.pack(side = 'top', expand=1, fill='both' , pady = 2)

   def log_error_page( self, parent ):
        #--------------------------------------------------------------------------------
        # Create the Error ScrolledFrame
        #--------------------------------------------------------------------------------
        txtFont = tkFont.Font(self.parent, family = pub_controls.tab_font_type, size=pub_controls.tab_font_size)
        self.parent.log_error_window = Pmw.ScrolledText(parent,
                  text_state='disabled',
	          text_background='pink',
                  text_relief = 'sunken',
                  text_borderwidth = 2,
                  text_font = txtFont,
        )
        self.parent.log_error_window.pack(side = 'top', expand=1, fill='both' , pady = 2)

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
