#!/usr/bin/env python
#
# The Publisher Editor Viewer Controls -  pub_pub_editorviewer module
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
# Description:  View the specific datasets objects and their methods.         #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFont
import gui_support
import pub_controls
import extraction_controls
import logging
import traceback

from pub_controls import MyButton
from pub_controls import font_weight
#from esgcet.publish.messaging import debug, info, warning, error, critical, exception
from esgcet.messaging import debug, info, warning, error, critical, exception
from esgcet.query import updateDatasetFromContext
from esgcet.query import queryDatasets
from esgcet.query import getQueryFields

#--------------------------------------------------------------------------------------
# Reset the dataset by calling load_configuration
#--------------------------------------------------------------------------------------
def evt_reset_project( parent, name ):
    try:
      if  (parent.parent.offline == True):
         parent.parent.pub_buttonexpansion.dataset_widgets.select_project.selectitem( name )
      parent.projectName = name
      extraction_controls.load_configuration( parent )
    except: pass

#--------------------------------------------------------------------------------------
# Show the field of each element on the dataset page
#--------------------------------------------------------------------------------------
def show_field( parent, gui_parent, field_name, field_options, field_value, isMandatory, tag, for_query = False ):

        text_color = 'black'
        fcFont=tkFont.Font(gui_parent, family = pub_controls.combobox_font_type, size=pub_controls.combobox_font_size, weight=font_weight)
        txtFont=tkFont.Font(gui_parent, family = pub_controls.text_font_type, size=pub_controls.text_font_size, weight=font_weight)
        if isMandatory and for_query is False: 
           field_name = "*" + field_name
           text_color = "blue"

        #--------------------------------------------------------------------------------------
        # Restrict the user's choice of selection -- can only select items from the 
        # pulldown menu
        #--------------------------------------------------------------------------------------
        if tag == 1:
           if field_options == None:
                 field_options = ["NO OPTIONS"]
                 field_value = "NO OPTIONS"

           field_combo = Pmw.ComboBox(gui_parent,
                    label_text = field_name + ': ',
                    label_foreground = text_color,
                    label_font = fcFont,
                    labelpos = 'w',
                    entryfield_value = field_value,
                    entry_width = 17,
                    entry_font = fcFont,
                    entry_background="aliceblue",
                    entry_state = "readonly",
                    entry_readonlybackground = "aliceblue",
                    listbox_background="aliceblue",
                    listbox_font = fcFont,
                    scrolledlist_items = field_options,
           )
           if field_name == "*Project":
              field_combo.configure(selectioncommand = pub_controls.Command( evt_reset_project, parent ) )

           field_combo.pack(side = 'top', fill = 'x', padx = 0, pady = 2)
           return field_combo
        #--------------------------------------------------------------------------------------
        # Allow the user's choice to enter the text in the entry window
        #--------------------------------------------------------------------------------------
        elif tag == 2:
           # Create and pack the EntryFields.
           if field_value == None: field_value = ""
           width = 1
           if for_query == False: width = 55
           field_entry = Pmw.EntryField(gui_parent,
                    labelpos = 'w',
                    label_text = field_name + ': ',
                    label_foreground = text_color,
                    label_font = txtFont,
                    entry_font = txtFont,
                    entry_width = width,
                    value = field_value,
                    validate = None,
                    entry_background="aliceblue",
                    )
           field_entry.pack(side = 'top', expand = 1, fill = 'x', padx=0, pady=2)
           return field_entry
        #--------------------------------------------------------------------------------------
        # Allow the user's see the entered text -- but they cannot edit the entry
        #--------------------------------------------------------------------------------------
        elif tag in [ 3, None ]:
           # Create and pack the EntryFields.
           if field_value == None: field_value = ""
           width = 1
 #          if field_name.lower() == 'id': field_value = field_value[:-1]  # GANZ this is where id gets clipped!  
           if for_query == False: width = 50
           state = "normal"
           if for_query == False: state = "readonly"
           field_entry = Pmw.EntryField(gui_parent,
                    labelpos = 'w',
                    label_text = field_name + ': ',
                    label_foreground = text_color,
                    label_font = txtFont,
                    entry_width = width,
                    entry_state = state,
                    entry_readonlybackground = 'pink',
                    entry_background = 'pink',
                    entry_font = txtFont,
                    value = field_value,
                    validate = None,
                    )
           field_entry.pack(side = 'top', expand = 1, fill = 'x', padx=0, pady=2)
           return field_entry
        #--------------------------------------------------------------------------------------
        # Allow the user's see the entered text in a scrolled window
        #--------------------------------------------------------------------------------------
        elif tag == 4:
	   # Create the ScrolledText.
	   scrolled_text = Pmw.ScrolledText(gui_parent,
                    labelpos = 'w',
                    label_text = field_name + ': ',
                    label_foreground = text_color,
                    label_font = txtFont,
                    text_background="aliceblue",
                    text_font = txtFont,
		    borderframe = 1,
		    usehullsize = 1,
	            hull_height = 60,
 		    text_padx = 5,
		    text_pady = 2,
                    label_background="PaleGreen3",
                    hull_background="PaleGreen3",
	   )
           scrolled_text.pack(side = 'top', expand = 1, fill = 'x', padx=0, pady=2)
           if field_value is not None: scrolled_text.settext( field_value )
           return scrolled_text


#----------------------------------------------------------------------------------------
# Begin the creation of the publisher editor view controls window
#----------------------------------------------------------------------------------------
class create_publisher_editor_viewer:
   """
   Show the selected dataset page with all of its methods and attributes.
   """
   def __init__( self, root, dataset_tab_name, dataset_name, from_tab, Session ):
        self.parent = root
        self.Session = Session

        #--------------------------------------------------------------------------------
        # Set the color for dataset name button widget and overall font size and style.
        #--------------------------------------------------------------------------------
        keycolor1 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.25 )
        keycolor2 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.85 )
        tabFont = tkFont.Font(self.parent, family = pub_controls.tab_font_type, size=pub_controls.tab_font_size)
        self.dataset_tab_name = self.parent.top_notebook.add(dataset_tab_name, tab_bg=keycolor1, tab_fg=keycolor2, tab_font = tabFont)
        txtFont=tkFont.Font(self.parent, family = pub_controls.text_font_type, size=pub_controls.text_font_size, weight=font_weight)

        #--------------------------------------------------------------------------------
        # Generate the group with the remove page icon
        #--------------------------------------------------------------------------------
        self.group_it = Pmw.Group( self.dataset_tab_name,
                tag_pyclass = MyButton,
                tag_text='Remove',
                tagindent = 0,
                tag_command = pub_controls.Command( self.parent.main_frame.evt_remove_top_tab, dataset_tab_name, "Dataset" )
        )
        self.group_it.pack(fill = 'both', expand = 1, padx = 0, pady = 0)

        #--------------------------------------------------------------------------------
        # Display the Query or Collection button -- returns the user to the collection 
        # of datasets
        #--------------------------------------------------------------------------------
        bg_color = "lightgreen"
        if from_tab[:5] == "Query":
           bg_color = Pmw.Color.changebrightness(self.parent.parent, pub_controls.query_tab_color, 0.6 )
        elif from_tab[:7] == "Offline":
           bg_color = "orange"
        q_frame = Tkinter.Frame ( self.group_it.interior() )
        b = Tkinter.Button( q_frame,
                text = from_tab + ": ",
                font = txtFont,
                background = bg_color,
                command = pub_controls.Command( self.evt_show_query_page, from_tab )
        )
        b.pack(side='left')
        l = Tkinter.Label( q_frame,
                text = dataset_name, 
                font = txtFont,
        )
        l.pack(side='left')
        #--------------------------------------------------------------------------------
        # Display the Save Changes button -- save dataset edits
        #--------------------------------------------------------------------------------
        s = Tkinter.Button( q_frame,
                text = "Save Changes",
                font = txtFont,
                background = keycolor1,
                foreground = keycolor2,
                command = pub_controls.Command( self.evt_save_dataset_page, dataset_name )
        )
        s.pack(side='left')

        q_frame.pack(side = 'top' )

        self.dataset_sframe = Pmw.ScrolledFrame ( self.group_it.interior(),
        )
        self.dataset_sframe.pack(side = 'top', expand=1, fill='both' , pady = 2)

        self.dataset_frame = Tkinter.Frame ( self.dataset_sframe.interior() )

   def evt_show_query_page(self, from_tab):
       self.parent.parent.top_notebook.selectpage( from_tab )

   def evt_save_dataset_page(self, datasetName):
       import types
       from esgcet.messaging import debug, info
       new_settings = {}
       for x in self.field_list.keys():
           field_value = self.field_list[ x ].get()
           if type(field_value) == types.UnicodeType:
              field_value = str( field_value )[:-1]
           new_settings[ x ] = field_value

       del new_settings[ 'id' ]    # Don't reset the 'id'
       updateDatasetFromContext(new_settings, datasetName, self.Session)

       info("The changes have been accepted for the dataset: %s." % datasetName)
           

   #--------------------------------------------------------------------------------
   # Generate the dataset group page with the remove icon
   #--------------------------------------------------------------------------------
   def dataset_page( self, dataset = None, Session = None, handler = None ):
        if handler != None:
           try: self.parent.canvas.pack_forget()  # Remove the white canvas
           except: pass

        self.field_list = {}
        validate = []
        mandatory = []
        options = {}
        values = {}
        #--------------------------------------------------------------------------------
        # Generate a dataset page with dummy fields if no dataset was given
        #--------------------------------------------------------------------------------
        if handler == None:
           return_fields = ["Project", "Dataset name", "Model", "Experiment", "Run number", "Product", "Format"]
           validate = [1,2,3,4,1,2,3,4,1]
           mandatory = [True,False,True,False,True,False,True,False,True]
           options = values = {"Project":None, "Dataset name":None, "Model":None, "Experiment":None, "Run number":None, "Product":None, "Format":None}
        else:
           #--------------------------------------------------------------------------------
           # Retrieve the dataset fields and properties from the queryDataset command
           #--------------------------------------------------------------------------------
           list_fields = getQueryFields( handler )
           properties = {'id':(1, dataset.get_id( Session ))}
           for x in list_fields:
               if x is not "id": properties[ x ] = (2, "%")
           values, return_fields = queryDatasets(dataset.get_project( Session ), handler, Session, properties)
           for x in return_fields:
                validate.append( handler.getFieldType( x ) )
                options[ x ] = handler.getFieldOptions( x )
                mandatory.append( handler.isMandatory( x ) )

        #--------------------------------------------------------------------------------
        # View the dataset fields in the page
        #--------------------------------------------------------------------------------
        for i in range(len(return_fields)):
            #print " ganz dataset test %s", return_fields[i]
            #print values[0][i]
            value = values[0][i]
            try:
                self.field_list[return_fields[i]] = show_field( self.parent, self.dataset_frame, return_fields[i].capitalize(), options[ return_fields[i] ], value, mandatory[i], validate[i] )
            except:
                field = return_fields[i]
                opts = options[field]
                mand = mandatory[i]
                valid = validate[i]
                error("Error in show_fields: field=%s, options=%s, value=%s, mandatory=%s, validate=%s"%(field, `opts`, `value`, mand, valid))
                error(traceback.format_exc())
                raise

        Pmw.alignlabels (self.field_list.values()) # alien the labels for a clean look

        self.dataset_frame.pack(side = 'left', expand=1, fill='both' , pady = 2)

        #--------------------------------------------------------------------------------
        # Create and pack the Group to display the message about mandatory fields
        #--------------------------------------------------------------------------------
        txtFont=tkFont.Font(self.parent, family = pub_controls.text_font_type, size=pub_controls.text_font_size, weight=font_weight)
	g = Pmw.Group(self.dataset_sframe.interior(),
                      tag_text='Mandatory Fields',
                      tag_font=txtFont
                     )
	g.pack(fill = 'x', padx = 36)
	cw = Tkinter.Label(g.interior(),
		text = 'All fields that begin with an asterisk\n"*" and in blue, must have an entry.',
                font = txtFont
             )
	cw.pack(padx = 2, pady = 2, expand='yes', fill='both')

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
