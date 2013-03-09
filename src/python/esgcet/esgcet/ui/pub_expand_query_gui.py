#!/usr/bin/env python
#
# The Publisher Button Metadata Query, Update and Delete -  pub_expand_query_gui module
#
###############################################################################
#                                                                             #
# Module:       pub_expand_query_gui module                                   #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Publisher button metadata query expansion that is found on    #
#               the left side of GUI. When a button is selected, it expand to #
#               show additional metadata query controls.                      #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFileDialog, tkFont
import os, string
import pub_editorviewer
import pub_controls
import pub_busy
import thread
import gui_support
import string
from Tkinter import *
from pub_controls import font_weight
from esgcet.messaging import debug, info, warning, error, critical, exception
from pub_controls import MyButton
from pub_editorviewer import show_field
from esgcet.config import splitRecord
from esgcet.config import getHandlerByName, getHandlerFromDataset
from esgcet.model import Dataset, ERROR_LEVEL
from esgcet.query import queryDatasets, queryDatasetMap
from esgcet.query import getQueryFields
from esgcet.publish import pollDatasetPublicationStatus, generateDatasetVersionId, parseDatasetVersionId
from pkg_resources import resource_filename

on_icon  = resource_filename('esgcet.ui', 'on.gif')
off_icon = resource_filename('esgcet.ui', 'off.gif')

#----------------------------------------------------------------------------------------
# Construct a query widgets for query selection of datasets
#----------------------------------------------------------------------------------------
class query_widgets:
    """
    Generate the query widgets seen on the left when "Metadata Query, Update, and 
    Delete" is selected.
    
    """
    
    def __init__(self, parent):
      self.parent = parent
      self.Session = parent.parent.Session
      self.select_button = {}
      self.select_labelV = {}
      self.select_label = {}

      #----------------------------------------------------------------------------------------
      # Begin the creation of the dataset ID pulldown query selection
      #----------------------------------------------------------------------------------------
      glFont=tkFont.Font(self.parent.parent, family = pub_controls.button_group_font_type, size=pub_controls.button_group_font_size, weight=font_weight)
      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type, size=pub_controls.label_button_font_size, weight=font_weight)
      self.group_query = Pmw.Group(self.parent.control_frame4,
                        tag_text = 'Query ID',
                        tag_font = glFont,
                        tagindent = 25)

      #----------------------------------------------------------------------------------------
      # Create and pack the EntryFields
      #----------------------------------------------------------------------------------------
      self.query_entry = Pmw.EntryField(self.group_query.interior(),
		labelpos = 'w',
		label_text = 'Dataset Id:',
                label_font = bnFont,
                entry_width = 200,
		validate = None,
                command = pub_controls.Command( self.evt_show_data_set_from_id )
      )

      self.query_entry.pack(side = 'left', expand = 1, padx = 10, pady = 10)
      #----------------------------------------------------------------------------------------
      # End the creation of the dataset ID pulldown query selection
      #----------------------------------------------------------------------------------------

      #----------------------------------------------------------------------------------------
      # Begin the creation of the project pulldown query selection
      #----------------------------------------------------------------------------------------
      self.button_controls = Pmw.Group(self.parent.control_frame4,
                        tag_text = 'Query Project Infomation',
                        tag_font = glFont,
                        tagindent = 25)

      #----------------------------------------------------------------------------------------
      # Create an instance of the notebook
      #----------------------------------------------------------------------------------------
      ntk = generate_notebook( parent, self.Session )
      parent.parent.ntk = ntk # Set the first instance of the notebook

      self.bdataset_sframe = Pmw.ScrolledFrame ( self.button_controls.interior())
      self.bdataset_sframe.pack(side = 'top')
      self.bdataset_frame = self.bdataset_sframe.interior()

      #----------------------------------------------------------------------------------------
      # Display the Project selection
      #----------------------------------------------------------------------------------------
      projectOption = self.parent.parent.config.get('initialize', 'project_options')
      projectSpecs = splitRecord(projectOption)
      projectName = projectSpecs[0][0]
      projectList = []
      for x in projectSpecs:
          projectList.append( x[0] )
      projectList.sort()

      parent.query_fields = {}
      parent.validate = {}
      parent.query_fields['project'] = show_field( self.parent, self.bdataset_frame, "Project", projectList , projectName, 1, 1, for_query=True )
      parent.validate['project'] = 1

      handler = getHandlerByName(projectName, None, self.Session)
      list_fields = getQueryFields( handler )
      
      validate = []
      mandatory = []
      options = {}
      for x in list_fields:
          if handler.getFieldType( x ) is not None:
             validate.append( handler.getFieldType( x ) )
          else:
             validate.append( 2 )
          options[ x ] = handler.getFieldOptions( x )
          mandatory.append( handler.isMandatory( x ) )

      for j in range(1,5):
         for i in range(len(list_fields)):
             if (list_fields[i] is not 'project'):
                if options[list_fields[i]] is None: 
                   value = ""
                else:
                   value = options[list_fields[i]] # ganz bug fix [0]
                if validate[i] == 1:
                    options[list_fields[i]].insert(0, "-Any-")
                    value = "-Any-"
                if j == validate[i]:
                   parent.query_fields[list_fields[i]] = show_field( self.parent, self.bdataset_frame, list_fields[i].capitalize(), options[list_fields[i]] , value, mandatory[i], validate[i], for_query=True)
                   parent.validate[list_fields[i]] = validate[i]

      Pmw.alignlabels(parent.query_fields.values())

      #----------------------------------------------------------------------------------------
      # Create button to update extraction
      #----------------------------------------------------------------------------------------
      w = Tkinter.Button(self.button_controls.interior(),
                text = 'Query Data Information',
                font = bnFont,
                background = "lightblue",
                command = pub_controls.Command( ntk.new_query_page, parent, None )
      )
      w.pack(side='top',padx = 0, pady = 3)

      self.button_controls.pack(side='top', fill='x', pady=3)

      #----------------------------------------------------------------------------------------
      # End the creation of the project pulldown query selection
      #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    # Display the one dataset in the "Query" page if an ID is given.
    #----------------------------------------------------------------------------------------
    def evt_show_data_set_from_id( self ):
       query_id = self.query_entry.get()
       ntk = generate_notebook( self.parent, self.Session )
       ntk.new_query_page( self.parent, None, query_id )

#----------------------------------------------------------------------------------------
# Construct a notebook to view the results of querying or defining a dataset id. This 
# widget will be viewed in the upper right corner of the Publisher GUI.
#----------------------------------------------------------------------------------------
class generate_notebook:
    """
    Create an instance of the notebook to display queried pages.
    """
    def __init__( self, parent, Session ):
      self.parent = parent
      self.Session = Session
      self.select_button = {}
      self.status = {}
      self.ok_err = {}
      self.select_label = {}
      self.select_labelV = {}
      self.pageFrame = {}
      self.pageFrameLabels = {}
      self.editor_parent = self.parent.parent.pane2.pane( 'EditPaneTop' )

      self.keycolor1 = Pmw.Color.changebrightness(self.editor_parent, 'aliceblue', 0.6 )
      self.keycolor2 = Pmw.Color.changebrightness(self.editor_parent, 'aliceblue', 0.85 )
      self.keycolor3 = Pmw.Color.changebrightness(self.editor_parent, 'aliceblue', 0.25 )
      self.keycolor4 = Pmw.Color.changebrightness(self.editor_parent, 'green', 0.5 )
      self.keycolor5 = Pmw.Color.changebrightness(self.editor_parent, 'green', 0.85 )

      # Set the arrow icons
      self.on  = Tkinter.PhotoImage(file=on_icon)
      self.off = Tkinter.PhotoImage(file=off_icon)

    #----------------------------------------------------------------------------------------
    # Generate a new page (i.e., tab) as a result of querying or defining a dataset id
    #----------------------------------------------------------------------------------------
    def new_query_page( self, parent, tab_name=None, query_id=None ):
      # Start the busy routine to indicate to the users something is happening
      
      self.parent.parent.busyCursor = 'watch'
      self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' ), self.parent.parent.pane2.pane( 'EditPaneBottom' ), self.parent.parent.pane2.pane( 'EditPaneStatus' ), self.parent.parent.pane.pane( 'ControlPane' )]
      pub_busy.busyStart( self.parent.parent )

      try:
         properties = {}
         projectName = self.parent.query_fields['project'].get() # Must have projectName
         handler = getHandlerByName(projectName, None, self.Session)
         tabcolor = Pmw.Color.changebrightness(self.parent.parent, pub_controls.query_tab_color, 0.6 )

# works up to here
      
         if query_id is None:
           for x in self.parent.query_fields.keys():
              query_string = self.parent.query_fields[x].get().lstrip()
              if (query_string == "-Any-") or (len(query_string) == 0):
                 properties[x] = (2, "%")
              elif query_string != "-Any-":
                 properties[x] = (1, query_string)

           if properties['id'] == (2, "%"):
              del properties['id'] # This causes an error because you cannot modify the 'id'
          
           listProperties = False
        
        
      
           result, headers = queryDatasets(projectName, handler, self.Session, properties)
       # works up to here
       
       # running this causes it to fail!
           self.new_page(parent, tabName=None, tab_color=tabcolor, page_type = "query", query_result = result, list_fields = headers)
        
        
         else:
           result, headers = queryDatasets(projectName, handler, self.Session, properties)
           for x in result:
              query_id_found = False
              if query_id == x[0][:-1]:
                 self.new_page(parent, tabName=None, tab_color=tabcolor, page_type = "query", query_result = [x] , list_fields = headers)
                 query_id_found = True
                 break
           if query_id_found is False:
	          warning("The specified dataset id '%s' was not found.", query_id)

# fails here
      
      # Enable the "Data Publication" button
         self.parent.ControlButton3.configure( state = 'normal' )

         datasetNames = []
         for x in result:
             datasetNames.append( x[1] )
         dmap, offline_map, extraFields = queryDatasetMap( datasetNames, self.Session, extra_fields=True )
      # Check if offline or not, then set the iteration values for each page
      
      
         selected_page = self.parent.parent.main_frame.selected_top_page
         self.parent.parent.hold_offline[selected_page] = offline_map
         self.parent.parent.main_frame.projectName[selected_page] = projectName
         self.parent.parent.main_frame.dmap[selected_page] = dmap
         self.parent.parent.main_frame.extraFields[selected_page] = extraFields
         self.parent.parent.main_frame.datasetMapfile[selected_page] = None
         self.parent.parent.directoryMap[selected_page] = None
         self.parent.parent.main_frame.dirp_firstfile[selected_page] = None
         self.parent.parent.defaultGlobalValues[selected_page] = {}

      except:
            pub_busy.busyEnd( self.parent.parent )  # catch here in order to turn off the busy cursor ganz
            raise
      finally:
           pub_busy.busyEnd( self.parent.parent )
      #pub_busy.busyEnd( self.parent.parent )
 
    #----------------------------------------------------------------------------------------
    # Generate a new page (i.e., tab) as a result of querying or defining a dataset id
    #----------------------------------------------------------------------------------------
    def new_page( self, parent, tabName=None, tab_color='lightgreen', page_type='collection', query_result = None, list_fields = None ):
      #--------------------------------------------------------------------------------------
      # Show the tab (or page) name and generate a unique ID for the tab
      #--------------------------------------------------------------------------------------
      tab_name = tabName
      if tab_name == None:
         tab_name= "Query %i" % self.parent.parent.top_ct
      self.parent.parent.main_frame.top_tab_id[tab_name] = self.parent.parent.top_ct

      # Destroy the initial background canvas and replace it with the notebook
      try:
         if self.parent.parent.canvas is not None:
            self.parent.parent.canvas.pack_forget()
            self.parent.parent.canvas = None
      except:
         pass

      # Add new query "page" to the notebook
      tabFont = tkFont.Font(self.parent.parent, family = pub_controls.tab_font_type, size=pub_controls.tab_font_size)

      # Sort the Queries, Collections, Offlines, and Datasets
      ct = 0
      opages = self.parent.parent.top_notebook.pagenames()
      pages = []
      for x in opages:
          pages.append(x.split()[0])
      if len(pages) != 0:
         ct = 0
         if page_type == "query":
            for x in pages:
                if x != "Query":break
                else: ct += 1
         elif page_type == "collection":
            for x in pages:
                if x in ["Query", "Collection"]: ct += 1
                else: break
         elif page_type == "offline":
            for x in pages:
                if x in ["Query", "Collection", "Offline"]: ct += 1
                else: break
         try:
            prev_tab = opages[ct-1]
         except: pass

      # Insert the page in its appropriate place
      query_page = self.parent.parent.top_notebook.insert(tab_name, before=ct, tab_bg=tab_color, tab_font = tabFont)
      self.parent.parent.top_notebook.selectpage(tab_name)

      # Generate the group with the remove page icon
      group_page = Pmw.Group( query_page,
		tag_pyclass = MyButton,
		tag_text='Remove',
                tagindent = 0,
                tag_command = pub_controls.Command( self.parent.parent.main_frame.evt_remove_top_tab, tab_name, "Collection" )
      )
      group_page.pack(fill = 'both', expand = 1, padx = 0, pady = 0)
      self.parent.parent.balloon.bind(group_page, "Use the button in the upper left to remove the page.")

      labelFont=tkFont.Font(self.parent.parent, family = pub_controls.collection_font_type, size=pub_controls.collection_font_size)
      labelFontBold=tkFont.Font(self.parent.parent, family = pub_controls.tab_font_type, size=pub_controls.tab_font_size,weight=font_weight)
      text_height=-labelFont.cget('size')*1.1

      bnframe = Tkinter.Frame( group_page.interior() )
      bnframe.pack( side='top' )
      selected_page = self.parent.parent.main_frame.selected_top_page
      self.parent.parent.refreshButton[selected_page] = Tkinter.Button(bnframe,
                text = tab_name,
                relief = "flat",
                font = labelFontBold,
                command = pub_controls.Command( self.evt_refresh_list_of_datasets, selected_page ),
         )
      self.parent.parent.refreshButton[selected_page].pack(side='left', expand=1, fill='both')
      if page_type == "query":
         self.parent.parent.refreshButton[selected_page].configure(relief = 'raised', text = "Refresh "+tab_name, bg = 'aliceblue')


      frame_ct = self.parent.parent.top_ct
      
      self.pageFrameLabels[ frame_ct ] = Pmw.ScrolledFrame(group_page.interior(),
                vscrollmode = 'none',
                hscrollmode = 'none',
                usehullsize = 1,
                hull_width = 400,
                hull_height = 2*text_height
      )
      self.pageFrameLabels[ frame_ct ].pack(fill='x', padx = 2, pady = 3)
      bwidth=149 # was 170
      btext='          Dataset'
      banchor = 'w'
      if page_type == "query":
         btext = 'Ok/Err'
         bwidth = 4 
         banchor = 'n'
      self.label = Tkinter.Button(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Pick',
                relief = 'sunken',
                borderwidth = 1,
                justify='left',
                anchor='n',
                #font = labelFont,
                bg = self.keycolor4,
                width = 2,
      )
      self.label.pack(side='left', expand=1, fill='both')

#      if btext == '          Dataset':   # version should preceed the Dataset
# ganz added this to see about putting in a version 2nd try
      self.label4v = ""
      
      #ganz this code should go in query below (433)
      # ganz commented this out 1/19/11
#      lcolorV = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.8 )
#      if list_fields != None: 
       #if  'version' in list_fields:
#        self.label4v = Tkinter.Button(self.pageFrameLabels[ frame_ct ].interior(),
#                text = 'Ver',
#                relief = 'sunken',
#                borderwidth = 1,
                #font = labelFont,
#                bg = lcolorV,
#                width = 9
#         )
#        self.label4v.pack(side='left', expand=1, fill='both')
##########################################################################
#
#        popup = Menu(self.pageFrameLabels[ frame_ct ].interior(), tearoff=0)
#        popup.add_command(label="Show All Versions") # , command=next) etc...
#        popup.add_command(label="Show Latest Version")
        #popup.add_separator()
        #popup.add_command(label="Home 0")

#        def do_popup(event):
                # display the popup menu
#                try:
#                    popup.tk_popup(event.x_root, event.y_root, 0)
#                finally:
                    # make sure to release the grab (Tk 8.0a1 only)
#                    popup.grab_release()

#        self.label4v.bind("<Button-3>", do_popup)


      self.label2 = Tkinter.Button(self.pageFrameLabels[ frame_ct ].interior(),
                anchor=banchor,
                justify='left',
                text = btext,
                relief = 'sunken',
                borderwidth = 1,
                #font = labelFont,
                bg = self.keycolor5,
                width = bwidth 
      )
      self.label2.pack(side='left', expand=1, fill='both')

      if page_type == "query":
         lcolor1 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.8 )
         lcolor2 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.7 )
         lcolor3 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.5 )
         lcolor4 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.6 )
         lcolor5 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.7 )
         lcolor6 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.8 )
         self.label3a = Tkinter.Label(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Status',
                relief = 'sunken',
                borderwidth = 1,
                #font = labelFont,
                bg = lcolor1,
                width = 10
         )
         self.label3a.pack(side='left', expand=1, fill='both')

         if 'id' in list_fields:
            self.label3 = Tkinter.Label(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Id',
                relief = 'sunken',
                borderwidth = 1,
                #font = labelFont,
                bg = lcolor1,
                width = 6
            )
            self.label3.pack(side='left', expand=1, fill='both')

# ganz added this to see about putting in a version
         self.label4v = Tkinter.Button(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Ver',
                relief = 'sunken',
                borderwidth = 1,
                font = labelFont,
                bg = lcolor2,
                width = 9
         )
         self.label4v.pack(side='left', expand=1, fill='both')

         self.label4 = Tkinter.Button(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Dataset',
                relief = 'sunken',
                borderwidth = 1,
                font = labelFont,
                bg = lcolor2,
                width = 71
         )
         self.label4.pack(side='left', expand=1, fill='both')

         if 'project' in list_fields:
            self.label5 = Tkinter.Label(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Project',
                relief = 'sunken',
                borderwidth = 1,
                #font = labelFont,
                bg = lcolor3,
                width = 20
            )
            self.label5.pack(side='left', expand=1, fill='both')

         if 'model' in list_fields:
            self.label6 = Tkinter.Label(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Model',
                relief = 'sunken',
                borderwidth = 1,
                #font = labelFont,
                bg = lcolor4,
                width = 21
            )
            self.label6.pack(side='left', expand=1, fill='both')

         if 'experiment' in list_fields:
            self.label7 = Tkinter.Label(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Experiment',
                relief = 'sunken',
                borderwidth = 1,
                #font = labelFont,
                bg = lcolor5,
                width = 20
            )
            self.label7.pack(side='left', expand=1, fill='both')

         if 'run_name' in list_fields:
            self.label8 = Tkinter.Label(self.pageFrameLabels[ frame_ct ].interior(),
                text = 'Run Name',
                relief = 'sunken',
                borderwidth = 1,
                #font = labelFont,
                bg = lcolor6,
                width = 21
            ) # width was 23
            self.label8.pack(side='left', expand=1, fill='both')

      # Show the background
      self.pageFrame[ frame_ct ] = Pmw.ScrolledFrame(group_page.interior(),
		usehullsize = 1,
		hull_width = 400,
		hull_height = 420,
                vscrollmode = "static",
		clipper_background = 'aliceblue',
      )
      self.pageFrame[ frame_ct ].pack(padx = 2, pady = 2,expand=1, fill='both' )
      hsbr = self.pageFrameLabels[ frame_ct ].component('horizscrollbar')
      hsbr2 = self.pageFrame[ frame_ct ].component('horizscrollbar')
      hsbr2.config(command=pub_controls.Command( self.sync_scroll_move, self.parent.parent.top_ct) )

      # Display the datasets in the page
      
      self.display_datasets( page_type, query_result, list_fields )
      
      # Now view the newly created notebook page
      self.parent.parent.top_notebook.pack(side = 'top', fill = 'both', expand = 1, padx = 10, pady = 10)

      self.parent.parent.top_ct = self.parent.parent.top_ct + 1 # increment the unique page ID number
      
    #----------------------------------------------------------------------------------------
    # Refresh the displayed "Query" page or "Collection" page and show the updated status of
    # each dataset
    #----------------------------------------------------------------------------------------
    def evt_refresh_list_of_datasets( self, selected_page ):

        # Start the busy routine to indicate to the users something is happening
        self.parent.parent.busyCursor = 'watch'
        self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' ), self.parent.parent.pane2.pane( 'EditPaneBottom' ), self.parent.parent.pane2.pane( 'EditPaneStatus' ), self.parent.parent.pane.pane( 'ControlPane' )]
        pub_busy.busyStart( self.parent.parent )

        try:              
           if self.parent.parent.refreshButton[selected_page].cget('relief') == 'raised':
              for x in self.parent.parent.main_frame.top_page_id[selected_page]:
                  if self.parent.parent.main_frame.top_page_id[selected_page][x].cget('relief') == 'raised':
                     dsetVersionName = self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('text')
                  
                  # ganz added this 1/18/11
                     query_name = self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('text')               
                     versionNum = self.parent.parent.main_frame.version_label[selected_page][x].cget('text')                 
                  #####################################################################################
                                   
                     query_name, versionNum = parseDatasetVersionId(dsetVersionName)
# ganz TODO test only remove
#                  print query_name
#                  print versionNum
                  
                     status = pollDatasetPublicationStatus(query_name, self.Session)
                     # ganz catch non selected Red entries to skip 3/20/2011
                     try:
                       self.parent.parent.main_frame.status_label[selected_page][x].configure(text=pub_controls.return_status_text( status))
                     except:
                         continue

                  # Make sure you update the Ok/Err button
                  # ganz added this (1/18/11) here to catch the case when dset=None (e.g. no local db entry exists)
                     dset = Dataset.lookup(query_name, self.Session)
                     if (dset == None):
                        buttonColor = "yellow"
                        buttonText = "Warning"
                        self.parent.parent.main_frame.ok_err[selected_page][x].configure(bg=buttonColor, text=buttonText)                     
                     elif dset.has_warnings(self.Session):
                        warningLevel = dset.get_max_warning_level(self.Session)
                        if warningLevel>=ERROR_LEVEL:
                            buttonColor = "pink"
                            buttonText = "Error"
                        else:
                            buttonColor = "yellow"
                            buttonText = "Warning"
                        self.parent.parent.main_frame.ok_err[selected_page][x].configure(bg=buttonColor, text=buttonText)
        except:
            pub_busy.busyEnd( self.parent.parent )  # catch here in order to turn off the busy cursor ganz
            raise
        finally:
           pub_busy.busyEnd( self.parent.parent )
      #  pub_busy.busyEnd( self.parent.parent )
        info("Completed refreshing the display.")

    #----------------------------------------------------------------------------------------
    # Sync the two scroll frames to use the bottom scrollbar 
    #----------------------------------------------------------------------------------------
    def sync_scroll_move( self, frame_ct, *args ):
        self.pageFrame[ frame_ct ].xview(mode=args[0], value =args[1], units=[2])
        self.pageFrameLabels[ frame_ct ].xview(mode=args[0], value =args[1], units=[2])

    #----------------------------------------------------------------------------------------
    # Display the datasets on the page as a result of querying or defining a dataset id
    #----------------------------------------------------------------------------------------
     #----------------------------------------------------------------------------------------
    # Display the datasets on the page as a result of querying or defining a dataset id
    #----------------------------------------------------------------------------------------
    def display_datasets( self, page_type = "collection", query_result = None, list_fields = None ):
   
      self.row = 0
      self.row_frame_labels = {}
      self.row_frame_label2 = {}
      self.add_row_frame = {}
      self.select_button = {}
      self.select_label = {}
      self.label4v = {}
      self.select_labelV = {}
      self.status = {}
      self.ok_err = {}

      # loop through all the datasets for display
      temp_datasetlist = {}
      if page_type in ["collection", "offline"]:
         for i in range( len(self.parent.parent.datasetNames) ):
             temp_datasetlist[ i ] = self.parent.parent.datasetNames[ i ]
      
      if page_type in ["collection", "offline"]:
         for x in temp_datasetlist:
             self.addPageRow( x, temp_datasetlist[x], page_type = page_type)
      else:
         i = 0
         for x in query_result:
             self.addQueryPageRow( i, x, list_fields )
             i += 1
         
        
      self.parent.parent.main_frame.row_frame_labels[self.parent.parent.main_frame.selected_top_page] = self.pageFrameLabels
      self.parent.parent.main_frame.row_frame_label2[self.parent.parent.main_frame.selected_top_page] = self.label2
      #self.parent.parent.main_frame.version_label[self.parent.parent.main_frame.selected_top_page] =  self.label4v # ganz 1/19/11
      self.parent.parent.main_frame.add_row_frame[self.parent.parent.main_frame.selected_top_page] = self.add_row_frame
      self.parent.parent.main_frame.top_page_id[ self.parent.parent.main_frame.selected_top_page ] = self.select_button
      self.parent.parent.main_frame.top_page_id2[ self.parent.parent.main_frame.selected_top_page ] = self.select_label
      self.parent.parent.main_frame.version_label[self.parent.parent.main_frame.selected_top_page] =  self.select_labelV # TODO ganz added this to test
      self.parent.parent.main_frame.status_label[ self.parent.parent.main_frame.selected_top_page ] = self.status
      self.parent.parent.main_frame.ok_err[ self.parent.parent.main_frame.selected_top_page ] = self.ok_err
   
    
    

    #----------------------------------------------------------------------------------------
    # Add one dataset information row to the "Query" page QUERY COLLECTION
    #----------------------------------------------------------------------------------------
    def addQueryPageRow( self, num_tag, query_result, list_fields ):
        
        
      # set the color for each item in the row
      dcolor1 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.8 )
      dcolor2 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.7 )
      dcolor3 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.5 )
      dcolor4 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.6 )
      dcolor5 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.7 )
      dcolor6 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.8 )
      dcolor7 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.9 )

      frame_ct = self.parent.parent.top_ct
      labelFont=tkFont.Font(self.parent.parent, family= pub_controls.collection_font_type, size=pub_controls.collection_font_size)
      self.add_row_frame[ num_tag ] = self.pageFrame[ frame_ct ].interior()





      self.select_button[ num_tag ] = Tkinter.Button(self.add_row_frame[ num_tag ],
#                compound = Tkinter.LEFT,
#                justify = Tkinter.LEFT,
#                anchor = Tkinter.W,
                text = num_tag,
#                font = labelFont,
                image = self.on,
                bg = self.keycolor1,
                relief = 'raised',
#                width = 70,
                height = 1,
                command = pub_controls.Command( self.evt_selected_dataset, num_tag ),
      )
      self.select_button[ num_tag ].image = self.on # save the image from garbage collection
      self.select_button[ num_tag ].grid(row = self.row, column = 0, sticky = 'nsew')

      dset = Dataset.lookup(query_result[1], self.Session)
      if dset.has_warnings(self.Session):
         warningLevel = dset.get_max_warning_level(self.Session)
         if warningLevel>=ERROR_LEVEL:
             buttonColor = "pink"
             buttonText = "Error"
         else:
             buttonColor = "yellow"
             buttonText = "Warning"
         self.ok_err[ num_tag ] = Tkinter.Button( self.add_row_frame[ num_tag ],
                text = buttonText,
                bg = buttonColor,
                width = 4,
                relief = 'raised',
                command = pub_controls.Command( self.parent.parent.pub_buttonexpansion.extraction_widgets.error_extraction_button,dset )
         )
         self.ok_err[ num_tag ].grid(row = self.row, column = 1, sticky = 'nsew')
      else:
         self.ok_err[ num_tag ] = Tkinter.Button( self.add_row_frame[ num_tag ], text = 'Ok', bg = dcolor1, highlightcolor = dcolor1, width = 4, relief = 'sunken')
         self.ok_err[ num_tag ].grid(row = self.row, column = 1, sticky = 'nsew')

      status = pollDatasetPublicationStatus(query_result[1], self.Session)
      status_text = pub_controls.return_status_text( status )
      self.status[ num_tag ] = Tkinter.Label( self.add_row_frame[ num_tag ], text = status_text, bg = dcolor1, highlightcolor = dcolor1, width = 10, relief = 'sunken')
      self.status[ num_tag ].grid(row = self.row, column = 2, sticky = 'nsew')


      if 'id' in list_fields:
         id = Tkinter.Label( self.add_row_frame[ num_tag ], text = query_result[0], bg = dcolor2, width = 6, relief = 'sunken')
         id.grid(row = self.row, column = 3, sticky = 'nsew')

      dsetName = query_result[1]
      versionNum = -1
      try:
          versionIndex = list_fields.index('version')
          versionNum = string.atoi(query_result[versionIndex])
      except:
          pass
      
   
      dsetTuple = (dsetName, versionNum)
      dsetName = generateDatasetVersionId(dsetTuple)
#ganz adding rows here...need to add versions
      datasetName = dsetTuple[0] # dataset[0]  #parseDatasetVersionId(dataset)
      versionno = dsetTuple[1] # dataset[1]

      ver_1 = versionno
      if (ver_1 ==-1):
            ver_1 = "N/A"

      self.select_labelV[ num_tag ] = Tkinter.Label( self.add_row_frame[ num_tag ], text = ver_1, bg = dcolor2, width = 11, relief = 'sunken')
      self.select_labelV[ num_tag ].grid(row = self.row, column = 4, sticky = 'nsew')
       

      self.select_label[ num_tag ] = Tkinter.Button(self.add_row_frame[ num_tag ],
                text = datasetName, #dsetName,
                font = labelFont,
                bg = self.keycolor2,
                relief = 'raised',
                borderwidth = 2,
                anchor='w',
                justify='left',
                width = 71,
                command = pub_controls.Command( self.evt_selected_dataset_text, dsetTuple, num_tag, 0 ),
        )
      self.select_label[ num_tag ].grid(row = self.row, column = 5, columnspan=2, sticky = 'nsew')

      if 'project' in list_fields:
         project = Tkinter.Label( self.add_row_frame[ num_tag ], text = query_result[2], bg = dcolor3, width = 20, relief = 'sunken', borderwidth = 2)
         project.grid(row = self.row, column = 7, sticky = 'nsew')

      if 'model' in list_fields:
         model = Tkinter.Label( self.add_row_frame[ num_tag ], text = query_result[3], bg = dcolor4, width = 20, relief = 'sunken', borderwidth = 2)
         model.grid(row = self.row, column = 8, sticky = 'nsew')

      if 'experiment' in list_fields:
         experiment = Tkinter.Label( self.add_row_frame[ num_tag ], text = query_result[4], bg = dcolor5, width = 20, relief = 'sunken', borderwidth = 2)
         experiment.grid(row = self.row, column = 9, sticky = 'nsew')

      if 'run_name' in list_fields:
         run_name = Tkinter.Label( self.add_row_frame[ num_tag ], text = query_result[5], bg = dcolor6, width = 20, relief = 'sunken', borderwidth = 2)
         run_name.grid(row = self.row, column = 10, sticky = 'nsew')

      self.add_row_frame[ num_tag ].grid_rowconfigure(self.row, weight = 1)
      self.add_row_frame[ num_tag ].grid_columnconfigure(1, weight = 1)
      if self.pageFrame[ frame_ct ].cget('horizflex') == 'expand' or \
                self.pageFrame[ frame_ct ].cget('vertflex') == 'expand':
            self.pageFrame[ frame_ct ].reposition()

      self.row = self.row + 1 # increment to the next dataset row

    #---------------------------------------------------------------------
    # Add one dataset information row to the "Collection" page INITIAL COLLECTION
    #---------------------------------------------------------------------
    def addPageRow( self, num_tag, dataset, page_type = "collection" ):
        
       
        
        frame_ct = self.parent.parent.top_ct
        labelFont=tkFont.Font(self.parent.parent, family = pub_controls.collection_font_type, size=pub_controls.collection_font_size)
        self.add_row_frame[ num_tag ] = self.pageFrame[ frame_ct ].interior()

	self.select_button[ num_tag ] = Tkinter.Button(self.add_row_frame[ num_tag ],
                text = num_tag,
#                font = labelFont,
                image = self.on,
                bg = self.keycolor1,
                relief = 'raised', 
#                width = 3,
                height = 1,
                command = pub_controls.Command( self.evt_selected_dataset, num_tag ),
        )
	self.select_button[ num_tag ].grid(row = self.row, column = 0, sticky = 'nsew')
#ganz adding rows here...need to add versions
        datasetName = dataset[0]  #parseDatasetVersionId(dataset)
	versionno = dataset[1]



# ganz changed colunmspan from 5 to one here
#	self.select_labelV[ num_tag ].grid(row = self.row, column = 1, columnspan=1,sticky = 'nsew')
        self.add_row_frame[ num_tag ].grid_rowconfigure(self.row, weight = 1)
	self.add_row_frame[ num_tag ].grid_columnconfigure(1, weight = 1)
###################################################################################################
	self.select_label[ num_tag ] = Tkinter.Button(self.add_row_frame[ num_tag ], 
                text = datasetName, # generateDatasetVersionId(dataset),
                font = labelFont,
                bg = self.keycolor2, 
                disabledforeground = 'black',
                relief = 'sunken',
                borderwidth = 2,
                anchor='w',
                justify='left',
                width = 170,
                command = pub_controls.Command( self.evt_selected_dataset_text, dataset, num_tag, 0),
        )   # ganz the above genFrom was 1 3/22/11
# ganz changed colunmspan from 5 to 4 here fix return to column=1 from 2 and columnspan to 5 from 4
	self.select_label[ num_tag ].grid(row = self.row, column = 1, columnspan=5,sticky = 'nsew')


      #  if page_type == "offline":
      #     self.select_label[ num_tag ].configure(state="disabled")

	self.add_row_frame[ num_tag ].grid_rowconfigure(self.row, weight = 1)
	self.add_row_frame[ num_tag ].grid_columnconfigure(2, weight = 1)
	if self.pageFrame[ frame_ct ].cget('horizflex') == 'expand' or \
                self.pageFrame[ frame_ct ].cget('vertflex') == 'expand':
            self.pageFrame[ frame_ct ].reposition()

	self.row = self.row + 1 # increment to the next dataset row

    #---------------------------------------------------------------------
    # Select or unselect the dataset button on the "Query" or 
    # "Collection" page
    #---------------------------------------------------------------------
    def evt_selected_dataset( self, num_tag ):
        if self.parent.parent.main_frame.top_page_id[self.parent.parent.main_frame.selected_top_page][num_tag].cget('bg') == 'salmon':
           self.parent.parent.main_frame.top_page_id[self.parent.parent.main_frame.selected_top_page][ num_tag ].configure(relief = 'raised', background = self.keycolor1, image = self.on)
        else:
           self.parent.parent.main_frame.top_page_id[self.parent.parent.main_frame.selected_top_page][ num_tag ].configure(relief = 'raised', background = 'salmon', image = self.off)

    #---------------------------------------------------------------------
    # Display the dataset and its attributes when the dataset text button 
    # is selected on the "Query" or "Collection" or "Offline" page 
    #---------------------------------------------------------------------
    def evt_selected_dataset_text( self, datasetTuple, num_tag, genFrom ):
       dataset,vers = datasetTuple
       datasetVersId = generateDatasetVersionId(datasetTuple) 
       list_of_dataset_tabs = self.parent.parent.top_notebook.pagenames()
       tab_name = datasetVersId.replace('_', '-' )
       dset = None
       if self.parent.parent.main_frame.top_page_id2[self.parent.parent.main_frame.selected_top_page][num_tag].cget('relief') == 'raised':
          if tab_name in list_of_dataset_tabs:
             self.parent.parent.top_notebook.selectpage( tab_name )
          else:
             self.parent.parent.main_frame.top_page_id2[self.parent.parent.main_frame.selected_top_page][ num_tag ].configure(bg = self.keycolor3, fg = self.keycolor2)
   
             from_tab = self.parent.parent.top_notebook.getcurselection()
             dset = Dataset.lookup(dataset, self.Session)
             if genFrom:
                handler = self.parent.parent.handlerDictionary[ dataset ]
             else:
                handler = getHandlerFromDataset(dset, self.Session)

             pub_editorviewer = self.parent.parent.create_publisher_editor_viewer( self.parent.parent, tab_name, dataset, from_tab, self.Session)
             pub_editorviewer.dataset_page( dataset = dset, Session = self.Session, handler = handler )
             self.parent.parent.top_notebook.selectpage( tab_name )

             # Disable the "Data Publication" button
             self.parent.parent.pub_buttonexpansion.control_frame3.pack_forget( )
             self.parent.parent.pub_buttonexpansion.control_toggle3 = 0
             self.parent.parent.pub_buttonexpansion.ControlButton3.configure( image = self.parent.parent.pub_buttonexpansion.right, state = 'disabled' )

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
