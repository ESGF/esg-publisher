#!/usr/bin/env python
#
# The Publisher Button Expansion Controls for Extraction -  pub_expand_extraction module
#
###############################################################################
#                                                                             #
# Module:       pub_expand_extraction_gui module                              #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Publisher button expansion that is found on the left side of  #
#               GUI. When a button is selected, it expand to show additional  #
#               controls.                                                     #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFileDialog, tkFont
import os, string, types
import pub_controls
import pub_busy
from pub_controls import MyButton
from pub_controls import font_weight
from esgcet.query import getQueryFields
from esgcet.messaging import warning
from esgcet.publish import pollDatasetPublicationStatus, readDatasetMap, CREATE_OP, DELETE_OP, RENAME_OP, UPDATE_OP, REPLACE_OP
from esgcet.ui import extraction_controls
from esgcet.model import Dataset, ERROR_LEVEL
from esgcet.config import getOfflineLister

class dataset_widgets:
    """
    Generate the expansion control widgets seen on the left when "Data Extraction" is selected.
    """

    def __init__(self, parent):
      self.parent = parent
      self.Session = parent.parent.Session

      #----------------------------------------------------------------------------------------
      # Begin the creation of the button controls
      #----------------------------------------------------------------------------------------
      tagFont=tkFont.Font(self.parent.parent, family = pub_controls.button_group_font_type, size=pub_controls.button_group_font_size, weight=font_weight)
      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type, size=pub_controls.label_button_font_size, weight=font_weight)
      #self.button_controls = Pmw.Group(self.parent.control_frame2,
      #                  tag_text = 'Button Controls',
      #                  tag_font = tagFont,
      #                  tagindent = 25)

      # Create and pack the LabeledWidgets to "Select All" datasets
      lw_start1 = Pmw.LabeledWidget(self.parent.control_frame2,
                    labelpos = 'w',
                    label_font = bnFont,
                    label_text = 'Dataset: ')
      lw_start1.component('hull').configure(relief='sunken', borderwidth=2)
      lw_start1.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      cw_start = Tkinter.Button(lw_start1.interior(),
                    text='Select All',
                    font = bnFont,
                    background = "aliceblue",
                    command = pub_controls.Command( self.evt_dataset_select_all ))
      cw_start.pack(padx=10, pady=10, expand='yes', fill='both')

      # Create and pack the LabeledWidgets to "Unselect All" datasets
      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type,  size=pub_controls.label_button_font_size, weight=font_weight)

      lw_start2 = Pmw.LabeledWidget(self.parent.control_frame2,
                    labelpos = 'w',
                    label_font = bnFont,
                    label_text = 'Dataset: ')
      lw_start2.component('hull').configure(relief='sunken', borderwidth=2)
      lw_start2.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      cw_start = Tkinter.Button(lw_start2.interior(),
                    text='Unselect All',
                    font = bnFont,
                    background = "aliceblue",
                    command = pub_controls.Command( self.evt_dataset_unselect_all ))
      cw_start.pack(padx=10, pady=10, expand='yes', fill='both')

      # Create and pack the LabeledWidgets to start extraction
      self.generating_file_list_flg = 0
      lw_start3 = Pmw.LabeledWidget(self.parent.control_frame2,
                    labelpos = 'w',
                    label_font = bnFont,
                    label_text = 'Data extraction:    ')
      lw_start3.component('hull').configure(relief='sunken', borderwidth=2)
      lw_start3.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      cw_start = Tkinter.Button(lw_start3.interior(),
                    text='Create/Replace',
                    background = "lightblue",
                    font= bnFont,
                    command = pub_controls.Command( self.start_update_extraction_button, False ))
      cw_start.pack(padx=10, pady=10, expand='yes', fill='both')

      # Create and pack the LabeledWidgets to update extraction
      self.generating_file_list_flg = 0
      lw_update = Pmw.LabeledWidget(self.parent.control_frame2,
                    labelpos = 'w',
                    label_font = bnFont,
                    label_text = 'Update extraction: ')
      lw_update.component('hull').configure(relief='sunken', borderwidth=2)
      lw_update.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      cw_update = Tkinter.Button(lw_update.interior(),
                    text='Append/Update',
                    background = "lightblue",
                    font = bnFont,
                    command = pub_controls.Command( self.start_update_extraction_button, True ))
      cw_update.pack(padx=10, pady=10, expand='yes', fill='both')

      Pmw.alignlabels( (lw_start1, lw_start2, lw_start3, lw_update) )

      #self.button_controls.pack(side='top', fill='x', pady=3)
      #----------------------------------------------------------------------------------------
      # End the creation of the button controls
      #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    # Event button to Create/Replace or Append/Update the extraction process
    #----------------------------------------------------------------------------------------
    def evt_dataset_select_all( self ):
       self.parent.parent.menu.Dataset.evt_select_all_dataset( self.parent.parent )

    def evt_dataset_unselect_all( self ):
       self.parent.parent.menu.Dataset.evt_unselect_all_dataset( self.parent.parent )

    def start_update_extraction_button( self, append_status=False ):
       from esgcet.publish.utility import filelistIterator, directoryIterator
       from esgcet.publish.utility import StopEvent

       # To prevent unexplained core dumps, the scrollbar to the right and bottom must be removed
       try:
          self.parent.parent.log_output_window.configure(hscrollmode = 'none', vscrollmode = 'none')
       except:
          pass
   
       self.parent.did_start = True
       self.parent.parent.se = StopEvent()
       self.parent.parent.se.wait = False

       # Start the busy routine to indicate to the users something is happening
       self.parent.parent.busyCursor = 'watch'
       self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' ), self.parent.parent.pane2.pane( 'EditPaneBottom' ), self.parent.parent.pane2.pane( 'EditPaneStatus' ), self.parent.parent.pane.pane( 'ControlPane' )]
       pub_busy.busyStart( self.parent.parent )

       self.return_content2( appendOpt = append_status )

       pub_busy.busyEnd( self.parent.parent )

    def return_content2(self, appendOpt=False):
        from esgcet.publish import iterateOverDatasets, processIterator
        from esgcet.config import getHandlerByName
        from esgcet.model import eventName
        from esgcet.config import loadConfig

        # Initialize parameters for interating over datasets
        initcontext = {}
        aggregateOnly = False
        # appendOpt = False
        initcontext = {}
        properties = {}
        publish = False
        publishOnly = False
        thredds = False
        testProgress1 = [self.parent.parent.statusbar.show, 0, 50]
        testProgress2 = [self.parent.parent.statusbar.show, 50, 100]
        handlerDictionary = {}

        # Get the currently selected tab and the selected datasets
        tab_name = self.parent.parent.top_notebook.getcurselection()
        selected_page = self.parent.parent.main_frame.selected_top_page
        datasetNames = []
        datasetNames2 = []
        if (selected_page is None):
           warning("Must generate a list of datasets to scan before data extraction can occur.")
           return

        if (selected_page is not None) or (self.parent.parent.hold_offline[selected_page] == True):
           extraFields = None 
           if (self.parent.parent.hold_offline[selected_page] == False) or (isinstance(self.parent.parent.hold_offline[selected_page], types.DictType)):
              for x in self.parent.parent.main_frame.top_page_id[selected_page]:
                dset_name = self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('text')

                # Retrieve all the datasets in the collection for display
                status = pollDatasetPublicationStatus(dset_name, self.Session)
                status_text = pub_controls.return_status_text( status )
                if status_text != 'Error':
                   datasetNames2.append( self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('text') )
                # Retrieve only the datasets that have been selected
                if self.parent.parent.main_frame.top_page_id[selected_page][x].cget('bg') != 'salmon':
                   datasetNames.append( self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('text') )

              dmap = self.parent.parent.main_frame.dmap[selected_page]
              extraFields = self.parent.parent.main_frame.extraFields[selected_page]
              datasetMapfile = self.parent.parent.main_frame.datasetMapfile[selected_page]
              projectName = self.parent.parent.main_frame.projectName[selected_page]
              directoryMap = self.parent.parent.directoryMap[selected_page]

              if dmap is not None:
                 for x in datasetNames:
                    datasetName = datasetNames[0]
                    firstFile = dmap[datasetName][0][0]
	            self.parent.parent.handlerDictionary[ x ] = getHandlerByName(projectName, firstFile, self.Session)
                    handler = self.parent.parent.handlerDictionary[ x ]
                 # Copy the defaultGlobalValues into initcontext
                 initcontext = self.parent.parent.main_frame.defaultGlobalValues[selected_page]
              else:
                 for x in datasetNames:
                    firstFile = self.parent.parent.main_frame.dirp_firstfile[selected_page]
                    self.parent.parent.handlerDictionary[ x ] = getHandlerByName(projectName, firstFile, self.Session)
                    handler = self.parent.parent.handlerDictionary[ x ]
           else:      # working off-line
              projectName = self.parent.parent.main_frame.projectName[selected_page]
              if self.parent.parent.offline_file_directory[selected_page] == "directory":
                 if self.parent.parent.config is None:
                    extraction_controls.call_sessionmaker( self.parent.parent )
                 datasetPaths = []
                 dmap = {self.parent.parent.offline_datasetName : datasetPaths}
                 listerSection = getOfflineLister(self.parent.parent.config, "project:%s"%projectName, None)
                 offlineLister = self.parent.parent.config.get(listerSection, 'offline_lister_executable')
                 lastargs = self.parent.parent.offline_directories
                 commandArgs = "--config-section %s "%listerSection
                 commandArgs += " ".join(lastargs)
                 for filepath, size in processIterator(offlineLister, commandArgs, filefilt=self.parent.parent.filefilt):
                   datasetPaths.append((filepath, str(size)))
                 datasetNames = self.parent.parent.datasetNames
                 directoryMap = None

                 # get the handler
                 for x in datasetNames:
                    self.parent.parent.handlerDictionary[ x ] = getHandlerByName(projectName, None, self.Session, offline=True)

              elif self.parent.parent.offline_file_directory[selected_page] == "file":
                 dmap = self.parent.parent.main_frame.dmap[selected_page]
                 extraFields = self.parent.parent.main_frame.extraFields[selected_page]
                 datasetMapfile = self.parent.parent.main_frame.datasetMapfile[selected_page]
                 projectName = self.parent.parent.main_frame.projectName[selected_page]
                 directoryMap = None
                 if datasetMapfile is not None:
                     dmap, extraFields = readDatasetMap(datasetMapfile, parse_extra_fields=True)
                     datasetNames = dmap.keys()

                 # get the handlers
                 for x in datasetNames:
                    self.parent.parent.handlerDictionary[ x ] = getHandlerByName(projectName, None, self.Session, offline=True)


           # Iterate over datasets
           if appendOpt:
               operation = UPDATE_OP
           else:
               operation = CREATE_OP
           datasets = iterateOverDatasets(projectName, dmap, directoryMap, datasetNames, self.Session, self.parent.parent.aggregateDimension, operation, self.parent.parent.filefilt, initcontext, self.parent.parent.hold_offline[selected_page], properties, testProgress1, testProgress2, self.parent.parent.handlerDictionary, extraFields=extraFields)

           # If working on-line then replace the scanned list of datasets with 
           # the complete list of datasets
           if not self.parent.parent.hold_offline[selected_page]:
              datasets = []
              for x in datasetNames2:
                  entry = Dataset.lookup(x, self.Session)
                  if entry is not None:
                      datasets.append(entry)

           # Get the summary of errors after doing a data extraction
           dset_error = []
           for dset in datasets:
               status = dset.get_publication_status(self.Session)
               status_name = eventName[status]
               if dset.has_warnings(self.Session):
                   dset_error.append(dset.get_name(self.Session))

           try:
              list_fields = getQueryFields( handler )
           except:
              handler = getHandlerByName(projectName, None, self.Session)
              list_fields = getQueryFields( handler )

           # Display the datasets in the "Collection" page
#           if self.parent.parent.hold_offline[selected_page] == True:
#              tab_name = "Collection_Offline"
#              from_tab = "Collection"
#              pub_editorviewer = self.parent.parent.create_publisher_editor_viewer( self.parent.parent, tab_name, dataset, from_tab, self.Session)

           # Show the extracted datasets
           self.set_column_labels( len(datasets), list_fields )
           self.show_extracted_info(datasets, dset_error, list_fields)

        # Enable the "Data Publication" button
        self.parent.ControlButton3.configure( state = 'normal' )



    #----------------------------------------------------------------------------------------
    # Show the extraction information for the "Collection" tab
    #----------------------------------------------------------------------------------------
    def set_column_labels( self, dset_ct, list_fields ):
      selected_page = self.parent.parent.main_frame.selected_top_page

      refreshBtn = self.parent.parent.refreshButton[selected_page]
      btn_name = refreshBtn.cget('text')
      if btn_name[:8] != "Refresh ":
         new_tabName = "Refresh " + btn_name
         refreshBtn.configure(relief = 'raised', text = new_tabName, bg = 'aliceblue')

      rowFrameLabel2 = self.parent.parent.main_frame.row_frame_label2[selected_page]
      rowFrameLabels = self.parent.parent.main_frame.row_frame_labels[selected_page]
      if rowFrameLabel2.cget('width') < 100: return # This means that the labels are in place

      labelFont=tkFont.Font(self.parent.parent, family = pub_controls.collection_font_type, size=pub_controls.collection_font_size)

      lcolor1 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.8 )
      lcolor2 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.7 )
      lcolor3 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.5 )
      lcolor4 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.6 )
      lcolor5 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.7 )
      lcolor6 = Pmw.Color.changebrightness(self.parent.parent, 'green', 0.8 )

#      run_name_size = 23
#      if dset_ct > 1: run_name_size = 23

      #rowFrameLabel2.configure(text = 'Ok/Err', anchor='n', borderwidth = 1, width = 4)
      rowFrameLabel2.destroy()
      self.parent.parent.main_frame.row_frame_label2[selected_page] = Tkinter.Button( rowFrameLabels[selected_page].interior(),
                text = 'Ok/Err',
                bg = lcolor1,
                #font = labelFont,
                width = 4,
                relief = 'sunken')
      self.parent.parent.main_frame.row_frame_label2[selected_page].pack(side='left', expand=1, fill='both')

      status_id = Tkinter.Label(rowFrameLabels[selected_page].interior(),
                text = 'Status',
                #font = labelFont,
                bg = lcolor1,
                relief = 'sunken',
                borderwidth = 1,
                width = 10,
      )
      status_id.pack(side='left', expand=1, fill='both')

      if 'id' in list_fields:
         labels_id = Tkinter.Label(rowFrameLabels[selected_page].interior(),
                text = 'Id',
               #font = labelFont,
                bg = lcolor1,
                relief = 'sunken',
                borderwidth = 1,
                width = 6,
         )
         labels_id.pack(side='left', expand=1, fill='both')

      labels_dataset = Tkinter.Button(rowFrameLabels[selected_page].interior(),
                text = 'Dataset',
                font = labelFont,
                bg = lcolor2,
                relief = 'sunken',
                borderwidth = 1,
                width = 71
      )
      labels_dataset.pack(side='left', expand=1, fill='both')

      if 'project' in list_fields:
         labels_project = Tkinter.Label(rowFrameLabels[selected_page].interior(),
                text = 'Project',
                #font = labelFont,
                bg = lcolor3,
                relief = 'sunken',
                borderwidth = 1,
                width = 20
         )
         labels_project.pack(side='left', expand=1, fill='both')

      if 'model' in list_fields:
         labels_model = Tkinter.Label(rowFrameLabels[selected_page].interior(),
                text = 'Model',
                #font = labelFont,
                bg = lcolor4,
                relief = 'sunken',
                borderwidth = 1,
                width = 21
         )
         labels_model.pack(side='left', expand=1, fill='both')

      if 'experiment' in list_fields:
         labels_experiment = Tkinter.Label(rowFrameLabels[selected_page].interior(),
                text = 'Experiment',
                #font = labelFont,
                bg = lcolor5,
                relief = 'sunken',
                borderwidth = 1,
                width = 20
         )
         labels_experiment.pack(side='left', expand=1, fill='both')

      if 'run_name' in list_fields:
         labels_run_name = Tkinter.Label(rowFrameLabels[selected_page].interior(),
                text = 'Run Name',
                #font = labelFont,
                bg = lcolor6,
                relief = 'sunken',
                borderwidth = 1,
                width = 23
         )
         labels_run_name.pack(side='left', expand=1, fill='both')

    #----------------------------------------------------------------------------------------
    # Show the extraction information for the "Collection" tab
    #----------------------------------------------------------------------------------------
    def show_extracted_info( self, datasets, dset_error, list_fields ):
      # set the color for each item in the row
      dcolor1 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.8 )
      dcolor2 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.7 )
      dcolor3 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.5 )
      dcolor4 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.6 )
      dcolor5 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.7 )
      dcolor6 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.8 )
      dcolor7 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.85 )

      selected_page = self.parent.parent.main_frame.selected_top_page
      dobj = {}
      for dset in datasets:
          dobj[dset.name] = dset
      for x in self.parent.parent.main_frame.top_page_id[selected_page]:
         dset_row = self.parent.parent.main_frame.top_page_id[selected_page][x].cget('text')
         dset_text = self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('text')
         if dset_text in dobj.keys():
            dset = dobj[ dset_text ]
            if self.parent.parent.main_frame.top_page_id[selected_page][x].cget('relief') == 'raised':
               frame = self.parent.parent.main_frame.add_row_frame[selected_page][x]
               if not dset.has_warnings(self.Session):
                  ok_err = Tkinter.Button( frame, text = 'Ok', bg = dcolor1, highlightcolor = dcolor1, width = 4, relief = 'sunken')
               else:
                  warningLevel = dset.get_max_warning_level(self.Session) 
                  if warningLevel>=ERROR_LEVEL:
                      buttonColor = "pink"
                      buttonText = "Error"
                  else:
                      buttonColor = "yellow"
                      buttonText = "Warning"
                  ok_err = Tkinter.Button( frame, 
                        text = buttonText,
                        bg = buttonColor,
                        width = 4,
                        relief = 'raised',
                        command = pub_controls.Command( self.error_extraction_button,dset ) )
               ok_err.grid(row = dset_row, column = 1, sticky = 'nsew')
               self.parent.parent.main_frame.ok_err[selected_page][x] = ok_err
   
               status = pollDatasetPublicationStatus(dset.get_name(self.Session), self.Session)
               status_text = pub_controls.return_status_text( status )
               self.parent.parent.main_frame.status_label[selected_page][x] = Tkinter.Label( frame, text = status_text, bg = dcolor1, width = 10, relief = 'sunken')
               self.parent.parent.main_frame.status_label[selected_page][x].grid(row = dset_row, column = 2, sticky = 'nsew')
   
               if 'id' in list_fields:
                  id = Tkinter.Label( frame, text = dset.get_id(self.Session), bg = dcolor2, width = 6, relief = 'sunken')
                  id.grid(row = dset_row, column = 3, sticky = 'nsew')
   
               self.parent.parent.main_frame.top_page_id2[selected_page][x].configure( width=71, relief='raised', bg = dcolor7)
               self.parent.parent.main_frame.top_page_id2[selected_page][x].grid(row=dset_row,column = 4, columnspan=2, sticky = 'nsew')
   
               if 'project' in list_fields:
                  project = Tkinter.Label( frame, text = dset.get_project(self.Session), bg = dcolor3, width = 20, relief = 'sunken', borderwidth = 2)
                  project.grid(row = dset_row, column = 6, sticky = 'nsew')
   
               if 'model' in list_fields:
                  model = Tkinter.Label( frame, text = dset.get_model(self.Session), bg = dcolor4, width = 20, relief = 'sunken', borderwidth = 2)
                  model.grid(row = dset_row, column = 7, sticky = 'nsew')
   
               if 'experiment' in list_fields:
                  experiment = Tkinter.Label( frame, text = dset.get_experiment(self.Session), bg = dcolor5, width = 20, relief = 'sunken', borderwidth = 2)
                  experiment.grid(row = dset_row, column = 8, sticky = 'nsew')
   
               if 'run_name' in list_fields:
                  run_name = Tkinter.Label( frame, text = dset.get_run_name(self.Session), bg = dcolor6, width = 20, relief = 'sunken', borderwidth = 2)
                  run_name.grid(row = dset_row, column = 9, sticky = 'nsew')
         else:
            frame = self.parent.parent.main_frame.add_row_frame[selected_page][x]
            ok_err = Tkinter.Button( frame, text = 'N/A', bg = 'salmon', highlightcolor = dcolor1, width = 4, relief = 'sunken')
            ok_err.grid(row = dset_row, column = 1, sticky = 'nsew')

            status = Tkinter.Label( frame, text = 'N/A', bg = 'salmon', width = 10, relief = 'sunken')
            status.grid(row = dset_row, column = 2, sticky = 'nsew')

            id = Tkinter.Label( frame, text = 'N/A', bg = 'salmon', width = 6, relief = 'sunken')
            id.grid(row = dset_row, column = 3, sticky = 'nsew')

            self.parent.parent.main_frame.top_page_id2[selected_page][x].configure( width=71, relief='sunken', bg = 'salmon', fg = 'black' )
            self.parent.parent.main_frame.top_page_id2[selected_page][x].grid(row=dset_row,column = 4, columnspan=2, sticky = 'nsew')

         x += 1

    #----------------------------------------------------------------------------------------
    # Show the extraction errors in the output tab window below
    #----------------------------------------------------------------------------------------
    def error_extraction_button( self, dset ):
       from pkg_resources import resource_filename
       remove_gif = resource_filename('esgcet.ui', 'remove.gif')

       dset_name = dset.get_name(self.Session)
       tab_name = dset_name.replace('_', '-')
       list_of_tabs = self.parent.parent.bottom_notebook.pagenames( )
       tabFont = tkFont.Font(self.parent.parent, family = pub_controls.tab_font_type, size=pub_controls.tab_font_size)

       dset = Dataset.lookup(dset_name, self.Session)
       if dset.has_warnings(self.Session):
          warningLevel = dset.get_max_warning_level(self.Session)
          if warningLevel>=ERROR_LEVEL:
             tab_color = "pink"
          else:
             tab_color = "yellow"
       else:
           tab_color = "lightgreen"

       if tab_name in list_of_tabs:
          self.parent.parent.bottom_notebook.selectpage( tab_name )
       else:
          dset_error_page = self.parent.parent.bottom_notebook.add( tab_name, tab_bg=tab_color, tab_font = tabFont )

          # Generate the group with the remove page icon
          group_error_page = Pmw.Group( dset_error_page,
                tag_pyclass = MyButton,
                tag_text='Remove',
                tagindent = 0,
                tag_command = pub_controls.Command( self.evt_remove_error_page, tab_name )
          )
          group_error_page.pack(fill = 'both', expand = 1, padx = 0, pady = 0)
          self.parent.parent.balloon.bind(group_error_page, "Use the button in the upper left to remove the page.")

          # Create the ScrolledFrame.
          dset_output_window = Pmw.ScrolledText(group_error_page.interior(),
                  text_state='disabled',
                  text_background=tab_color,
                  text_relief = 'sunken',
                  text_borderwidth = 2,
          )
          dset_output_window.pack(side = 'top', expand=1, fill='both' , pady = 2)

          dset_warnings = dset.get_warnings(self.Session)
          for x in dset_warnings:
              dset_output_window.appendtext( x+"\n" )

          self.parent.parent.bottom_notebook.selectpage( tab_name )

          # Button remove
          tab = self.parent.parent.bottom_notebook.tab(tab_name)
          remove_icon = Tkinter.PhotoImage(file=remove_gif)
          b = Tkinter.Button(tab,image=remove_icon,command=pub_controls.Command(self.evt_remove_error_page, tab_name) )
          b.pack(side='right')
          b.image = remove_icon

    #----------------------------------------------------------------------------------------
    # Remove the dataset error tab
    #----------------------------------------------------------------------------------------
    def evt_remove_error_page(self, tab_name):
       self.parent.parent.bottom_notebook.delete( tab_name )

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------


