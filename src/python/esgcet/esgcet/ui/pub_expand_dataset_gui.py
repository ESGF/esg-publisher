#!/usr/bin/env python
#
# The Publisher Buttion Expansion Controls for Dataset -  pub_expand_dataset module
#
###############################################################################
#                                                                             #
# Module:       pub_expand_dateset_gui module                                 #
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
import os, string
import pub_editorviewer
import pub_controls
import pub_busy
import thread
import extraction_controls

from pub_controls import font_weight
from pub_editorviewer import show_field
from esgcet.config import splitRecord
from esgcet.publish import iterateOverDatasets
from esgcet.config import getHandlerByName, getHandlerFromDataset
from esgcet.messaging import debug, info, warning, error, critical, exception
from esgcet.query import getQueryFields

from pkg_resources import resource_filename
file2_gif = resource_filename('esgcet.ui', 'file2.gif')
folder2_gif = resource_filename('esgcet.ui', 'folder2.gif')
stop_gif = resource_filename('esgcet.ui', 'stop.gif')

#------------------------------------------------------------------------
# Return directory and file information -  its files and sub-directories
#------------------------------------------------------------------------
def _scn_a_dir( self ):
   d = []
   f = []
   search_pattern = None
   self.file_search_pattern='All Files'
   if (self.file_search_pattern is not None):
      sct=string.count( self.file_search_pattern, "*" )
      l = string.find( self.file_search_pattern, "*" )
      r = string.rfind( self.file_search_pattern, "*" )
      if sct == 0:  # No wild cards
        search_pattern = self.file_search_pattern
        sct = 2
      elif sct >= 2:
        search_pattern = self.file_search_pattern[(l+1):r]
      elif l == 0:
        search_pattern = self.file_search_pattern[1:]
      elif l > 0:
        search_pattern = self.file_search_pattern[0:-1]
        sct = 1
   else:
       sct = -1
   for x in os.listdir( './' ):
      if self.file_search_pattern is None:
         if os.path.isfile( x ):
           if x.lower()[-5:] in [ ".cdms", "*.cdml"]:
              f.append( x )
           elif  x.lower()[-4:] in [".cdf",".dic",".hdf", ".ctl", ".xml"] :
              f.append( x )
           elif  x.lower()[-3:] in [".nc","*.pp"] :
              f.append( x )
         elif os.path.isdir(x):
            d.append( x )
      elif( sct == -1 ):
         if os.path.isfile( x ):
            f.append( x )
         else:
            d.append( x )
      elif sct == 0:
         if os.path.isfile( x ):
            if  (string.find( x, search_pattern ) != 0) and (string.find( x, search_pattern ) != -1):
               f.append( x )
         else:
            d.append( x )
      elif sct == 1:
         if os.path.isfile( x ):
            if  (string.find( x, search_pattern ) >= 0):
               if self.file_search_pattern[0]=='*':
                  n=len(search_pattern)
                  if x[-n:]==search_pattern:
                     f.append( x )
               elif self.file_search_pattern[-1]=='*':
                  n=len(search_pattern)
                  if x[:n]==search_pattern:
                     f.append( x )
               else:
                  f.append(x)
         else:
            d.append( x )
      elif sct >= 2:           # looking for "*[string]", e.g., "*.nc" or "*.cdms"
         if os.path.isfile( x ):
            if string.find( x, search_pattern ) != -1 or search_pattern=='All Files':
               f.append( x )
         else:
            d.append( x )
   d.sort()
   dirp = os.getcwd()
   i = 0
   while dirp != "" and dirp !=  "/":
        d.insert(i, dirp)
        s=string.split( dirp, '/' )[-1]
        dirp = dirp[0:(len(dirp)-len(s)-1)]
        i += 1
   d.insert(i, "/")
   d.insert(i+1, "============================================================================")
   f.sort()
   return d,f


class dataset_widgets:
    """
    Generate the datasets control widgets seen on the left when "Specify Datasets" is selected.
    """
    def __init__(self, parent):
      self.parent = parent
      self.Session = parent.parent.Session

      #----------------------------------------------------------------------------------------
      # Display the Project selection
      #----------------------------------------------------------------------------------------
      self.dataset_fields = {}

      projectOption = self.parent.parent.config.get('initialize', 'project_options')
      projectSpecs = splitRecord(projectOption)
      projectName = projectSpecs[0][0]
      projectList = []
      for x in projectSpecs:
          projectList.append( x[0] )
      projectList.sort()
      self.dataset_fields["Project"] = self.project_dataset=show_field( self.parent, self.parent.control_frame1, "Project", projectList , projectName, 1, 1 )

      # Create and pack the LabeledWidgets for setting additional mandatory fields
      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type, size=pub_controls.label_button_font_size, weight=font_weight)
      self.evt_fields_flg = False
      self.defaultGlobalValues = {}
      lw_dir = Pmw.LabeledWidget(self.parent.control_frame1,
		    labelpos = 'w',
                    label_font = bnFont,
		    label_text = 'Set additional mandatory: ')
      lw_dir.component('hull').configure(relief='sunken', borderwidth=2)
      lw_dir.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      cw_dir = Tkinter.Button(lw_dir.interior(),
                    text='Fields',
                    font = bnFont,
                    background = "lightblue",
                    foreground='black',
                    command = pub_controls.Command(self.evt_popup_fields_window, self.parent.parent, projectName) )
      cw_dir.pack(padx=10, pady=10, expand='yes', fill='both')
      self.save_dir_btn_color = cw_dir.cget( "background" )

      # Add additional mandatory fields to allow the user to set default settings
  #    handler = getHandlerByName(projectName, None, self.Session)
  #    list_fields = getQueryFields( handler )
  #    for x in list_fields:
  #        if handler.isMandatory( x ):
  #           if x.lower() != "project":
  #              field_options = handler.getFieldOptions(x)
  #              if field_options is not None:
  #                 field_options.insert(0, x+" (Default Global Setting)")
  #                 self.dataset_fields[x] = show_field( self.parent, self.parent.control_frame1, x.capitalize(), field_options , x+" (Default Global Setting)", 1, 1 )

  #    Pmw.alignlabels( self.dataset_fields.values() )

      #----------------------------------------------------------------------------------------
      # Create and pack a work online or off line RadioSelect widget
      #----------------------------------------------------------------------------------------
      self.parent.parent.offline = False
      self.parent.parent.offline_directories = None
      self.parent.parent.offline_datasetName = None
      self.on_off = Pmw.RadioSelect(self.parent.control_frame1,
		buttontype = 'radiobutton',
		orient = 'horizontal',
		labelpos = 'w',
		command = pub_controls.Command( self.evt_work_on_or_off_line, ),
		label_text = 'Work: ',
                label_font = bnFont,
		hull_borderwidth = 2,
		hull_relief = 'ridge',
      )
      self.on_off.pack(side = 'top', expand = 1, padx = 10, pady = 10)

      # Add some buttons to the radiobutton RadioSelect.
      for text in ('On-line', 'Off-line'):
          self.on_off.add(text, font = bnFont)
      self.on_off.setvalue('On-line')

      #----------------------------------------------------------------------------------------
      # Begin the creation of the file type selection
      #----------------------------------------------------------------------------------------
      tagFont=tkFont.Font(self.parent.parent, family = pub_controls.button_group_font_type, size=pub_controls.button_group_font_size, weight=font_weight)
      self.group_file_filter = Pmw.Group(self.parent.control_frame1,
                        tag_text = 'Filter File Search',
                        tag_font = tagFont,
                        #hull_background = 'blue',
                        tagindent = 25)

      dfFont=tkFont.Font(self.parent.parent, family = pub_controls.combobox_font_type, size=pub_controls.combobox_font_size, weight=font_weight)
      self.data_filter = Pmw.ComboBox( self.group_file_filter.interior(),
                             entryfield_value = pub_controls.datatypes[0],
                             entry_font = dfFont,
                             entry_state = 'readonly',
                             entry_readonlybackground="aliceblue",
                             listbox_font = dfFont,
                             listbox_background = "aliceblue",
                             scrolledlist_items = pub_controls.datatypes,
                             )

      self.data_filter.pack(side = 'top', fill='x', pady = 5)
      self.group_file_filter.pack(side='top', fill='x', pady=3)
      #----------------------------------------------------------------------------------------
      # End the creation of the file type selection
      #----------------------------------------------------------------------------------------

      #----------------------------------------------------------------------------------------
      # Begin the creation of the directory, file, and combo directoy box
      #----------------------------------------------------------------------------------------
      glFont=tkFont.Font(self.parent.parent, family = pub_controls.button_group_font_type, size=pub_controls.button_group_font_size, weight=font_weight)
      self.group_list_generation = Pmw.Group(self.parent.control_frame1,
                        tag_text = 'Generate List',
                        tag_font = glFont,
                        tagindent = 25)
      self.parent.control_frame2 = self.group_list_generation.interior()

      self.directory_icon = Tkinter.PhotoImage(file=file2_gif)
      self.file_icon = Tkinter.PhotoImage(file=folder2_gif)
      self.stop_icon = Tkinter.PhotoImage(file=stop_gif)

      # Create and pack the LabeledWidgets for the directory selction
      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type, size=pub_controls.label_button_font_size, weight=font_weight)
      self.generating_file_list_flg = 0
      self.lw_dir = Pmw.LabeledWidget(self.parent.control_frame2,
		    labelpos = 'w',
                    label_font = bnFont,
		    label_text = 'Generate list from: ')
      self.lw_dir.component('hull').configure(relief='sunken', borderwidth=2)
      self.lw_dir.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      self.cw_dir = Tkinter.Button(self.lw_dir.interior(),
                    text='Directory',
                    font = bnFont,
                    background = "lightblue",
                    foreground='black',
                    command = pub_controls.Command(self.evt_popup_directory_window) )
      self.cw_dir.pack(padx=10, pady=10, expand='yes', fill='both')
      self.save_dir_btn_color = self.cw_dir.cget( "background" )

      # Create and pack the LabeledWidgets for the file selction
      self.lw_file = Pmw.LabeledWidget(self.parent.control_frame2,
		    labelpos = 'w',
                    label_font = bnFont,
		    label_text = 'Generate list from: ')
      self.lw_file.component('hull').configure(relief='sunken', borderwidth=2)
      self.lw_file.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      self.cw_file = Tkinter.Button(self.lw_file.interior(),
                    text='Map File',
                    font = bnFont,
                    background = "lightblue",
                    foreground='black',
                    command = pub_controls.Command(self.evt_popup_file_window) )
      self.cw_file.pack(padx=10, pady=10, expand='yes', fill='both')
      self.save_file_btn_color = self.cw_file.cget( "background" )

      # Set up directory combo box
      d,f = _scn_a_dir( self.parent )
      self.directory_combo = Pmw.ComboBox( self.parent.control_frame2,
                             scrolledlist_items = d,
                             entryfield_value = os.getcwd(),
                             entry_font = ('Times', 16, 'bold'),
                             entry_background='white', entry_foreground='black',
                             selectioncommand=pub_controls.Command(self.evt_enter_directory)
                             )
      self.directory_combo.component('entry').bind( "<Key>", pub_controls.Command(self.evt_change_color) )
      self.directory_combo.component('entry').bind( "<Return>", pub_controls.Command(self.evt_enter_directory) )
      self.directory_combo.component('entry').bind('<Tab>', pub_controls.Command(self.evt_tab) )
      self.directory_combo.component('entry').bind( "<BackSpace>", pub_controls.Command(self.evt_backspace) )

      self.parent.control_frame2.pack(side="top", fill = 'x', pady=5)
      self.group_list_generation.pack(side='top', fill='x', pady=3)
      #----------------------------------------------------------------------------------------
      # End the creation of the directory, file, and combo directoy box
      #----------------------------------------------------------------------------------------

      #----------------------------------------------------------------------------------------
      # Begin the regular expression widget
      #
      # We've decided that regular expression is no longer needed.
      #----------------------------------------------------------------------------------------
      self.group_list = Pmw.Group(self.parent.control_frame1,
                        tag_text = 'Regular Expressions',
                        tag_font = ('Times', 18, 'bold'),
                        hull_background = 'orange',
                        tagindent = 25)
###################################################################################
# To redisplay regular expression widget, just uncomment the 'pack' command below
#      self.group_list.pack(side='top', fill='x')
###################################################################################

      self.scl1 = Pmw.ScrolledText( self.group_list.interior(),
                                 text_background='aliceblue',
                                 text_foreground='black',
                                 text_wrap = 'none',
                                 text_padx = 5,
                                 text_pady = 5,
                                 usehullsize = 1,
                                 hull_width = 100,
                                 hull_height = 50)
                                 #horizscrollbar_width=50,
                                 #vertscrollbar_width=50 )
      self.scl1.pack(side='top', expand=1, fill='both')

      # Create and pack the LabeledWidgets for the compiling of the regular expression 
      self.generating_file_list_flg = 0
      self.lw_reg = Pmw.LabeledWidget(self.group_list.interior(),
                    labelpos = 'w',
                    label_text = 'Regular expression: ')
      self.lw_reg.component('hull').configure(relief='sunken', borderwidth=2)
      self.lw_reg.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      self.cw_reg = Tkinter.Button(self.lw_reg.interior(),
                    text='Go',
                    command = pub_controls.Command(self.evt_compile_regular_expression)
                    )
      self.cw_reg.pack(padx=10, pady=10, expand='yes', fill='both')
      self.save_reg_btn_color = self.cw_reg.cget( "background" )

      #----------------------------------------------------------------------------------------
      # End the regular expression widget
      #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    # From a directory path name, generate the dynamic list of files and thier
    # sizes in the directoy tree.
    #----------------------------------------------------------------------------------------
    def evt_compile_regular_expression( self ):
       from esgcet.publish.utility import fnmatchIterator
       from tkMessageBox import showerror

       # Reset the button colors
       self.cw_dir.configure( background=self.save_dir_btn_color, foreground='black' )
       self.cw_file.configure( background=self.save_file_btn_color, foreground='black' )
       self.cw_reg.configure( background=self.save_reg_btn_color, foreground='black' )

       regexp = self.scl1.get().strip()

       # Change the color of the selected button
       self.cw_reg.configure( background='green' )

       self.parent.parent.firstFile = fnmatchIterator(regexp).next()[0]
       self.parent.parent.datasetMapfile = None
       self.parent.parent.regexp = regexp

       extraction_controls.load_configuration(self.parent.parent)


    #----------------------------------------------------------------------------------------
    # From a directory path name, generate the dynamic list of files and thier
    # sizes in the directoy tree.
    #----------------------------------------------------------------------------------------
    def myfun3( self, dirp, lock ):
       import fnmatch, time

       index_count = 0
       lock.acquire()
       self.parent.parent.file_list = []
       self.parent.parent.file_size = []

       for root, dirs, files in os.walk(dirp):
          for filename in files:
              if fnmatch.fnmatch(filename, self.extension[0]):
                  sfilename = os.path.join(root, filename)
                  filesize = os.path.getsize(sfilename)
                  self.parent.parent.file_list.append( sfilename )
                  self.parent.parent.file_size.append( filesize )
                  self.parent.parent.file_line.append(pub_editorviewer.create_publisher_editor_viewer_row(self.parent.parent, index = index_count, size = filesize, status_flg = 1, filename = sfilename))
                  index_count+=1

                  time.sleep(0.1)    # Must wait for the row to be generated before moving on.

              if self.stop_listing_flg == 1 and index_count > 0:
                 pub_busy.busyEnd( self.parent.parent )
                 self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
                 self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')
                 self.parent.parent.file_counter = index_count
                 time.sleep(0.1)    # Must wait for the row to be generated before moving on.
                 self.parent.parent.log_output_window.appendtext("File list creation stopped. %s files in list.\n" % index_count)
                 self.generating_file_list_flg = 0
                 thread.exit()
       lock.release()

       self.parent.parent.file_counter = index_count

       pub_busy.busyEnd( self.parent.parent )

       if index_count > 0:
          self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
          self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')

       self.parent.parent.log_output_window.appendtext("Finished creating the file list. %s files in list.\n" % index_count)
       self.generating_file_list_flg = 0

    #----------------------------------------------------------------------------------------
    # From a file, generate the dynamic list of files and their sizes
    #----------------------------------------------------------------------------------------
    def open_text_file( self, dirfilename, lock ):
       import time
       import gc

       index_count = 0
       lock.acquire()

       f = open(dirfilename,'r')
       self.parent.parent.file_list = []
       self.parent.parent.file_size = []
       for dirfile in f:
           sfilename = dirfile[:-1]
           filesize = os.path.getsize(sfilename)
           self.parent.parent.file_list.append( sfilename )
           self.parent.parent.file_size.append( filesize )
           self.parent.parent.file_line.append(pub_editorviewer.create_publisher_editor_viewer_row(self.parent.parent, index = index_count, size = filesize, status_flg = 0, filename = sfilename))
           index_count+=1

           time.sleep(0.1)    # Must wait for the row to be generated before moving on.

           if self.stop_listing_flg == 1:
              pub_busy.busyEnd( self.parent.parent )
              self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
              self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')
              self.parent.parent.file_counter = index_count
              time.sleep(0.1)    # Must wait for the row to be generated before moving on.
              self.parent.parent.log_output_window.appendtext("File list creation stopped. %s files in list.\n" % index_count)
              self.generating_file_list_flg = 0
              thread.exit()

       f.close()

       lock.release()

       self.parent.parent.file_counter = index_count

       pub_busy.busyEnd( self.parent.parent )
       self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
       self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')

       self.parent.parent.log_output_window.appendtext("Finished creating the file list. %s files in list.\n" % index_count)
       self.generating_file_list_flg = 0

    def fill_in_data_information_file( self, dirfilename, onoff_line = "online" ):
       from esgcet.publish import readDatasetMap

       dmap, extraFields = readDatasetMap( dirfilename, parse_extra_fields=True )
       datasetNames = dmap.keys()
       datasetNames.sort()
       self.parent.parent.dmap = dmap
       self.parent.parent.extraFields = extraFields
       self.parent.parent.datasetNames = datasetNames
       self.parent.parent.datasetMapfile = dirfilename

       if onoff_line == "online":
          tab_name= "Collection %i" % self.parent.parent.top_ct
          page_type = "collection"
          tcolor='lightgreen'
          onoff_flag = False
       else:
          tab_name= "Offline %i" % self.parent.parent.top_ct
          page_type = "offline"
          tcolor='orange'
          onoff_flag = True
       self.parent.parent.ntk.new_page( self.parent.parent, tab_name, tab_color = tcolor, page_type = page_type )

       # Copy the defaultGlobalValues into initcontext
       setdefaultGlobalValues = {}
       initcontext = {}
       for x in self.defaultGlobalValues.keys():
           if self.defaultGlobalValues[ x ].find("Default Global Setting") == -1:
              setdefaultGlobalValues[ x ] = self.defaultGlobalValues[ x ]
       initcontext.update( setdefaultGlobalValues ) # Update the initcontext

       # Set the iteration values for each page
       selected_page = self.parent.parent.main_frame.selected_top_page
       self.parent.parent.main_frame.dmap[selected_page] = dmap
       self.parent.parent.main_frame.extraFields[selected_page] = extraFields
       self.parent.parent.main_frame.datasetMapfile[selected_page] = dirfilename
       self.parent.parent.main_frame.dirp_firstfile[selected_page] = None
       self.parent.parent.offline_file_directory[selected_page] = "file"
       self.parent.parent.defaultGlobalValues[selected_page] = initcontext
       self.parent.parent.directoryMap[selected_page] = None
       self.parent.parent.hold_offline[selected_page] = onoff_flag
       self.parent.parent.main_frame.projectName[selected_page] = self.project_dataset.get()

    def fill_in_data_information_directory( self, dirp, readFiles, onoff_line = "online" ):
       from esgcet.publish import multiDirectoryIterator
       from esgcet.config import getHandler, getHandlerByName
       if onoff_line == "online":
          self.parent.parent.filefilt = ".*\\" + self.parent.parent.extension[0][1:] + "$"

          lastargs = [dirp]
          multiIter = multiDirectoryIterator(lastargs, filefilt=self.parent.parent.filefilt)
          firstFile, size = multiIter.next()
          handler = getHandler(firstFile, self.Session, validate=True)
          if handler is None:
              raise ESGPublishError("No project found in file %s, specify with --project."%firstFile)
          projectName = handler.name
   
          self.parent.parent.multiIter = multiIter
          self.parent.parent.firstFile = firstFile

          initcontext = {}

          # Copy the defaultGlobalValues into initcontext
          setdefaultGlobalValues = {}
          for x in self.defaultGlobalValues.keys():
              if self.defaultGlobalValues[ x ].find("Default Global Setting") == -1:
                 setdefaultGlobalValues[ x ] = self.defaultGlobalValues[ x ]
          initcontext.update( setdefaultGlobalValues ) # Update the initcontext

          properties = {}
          props = properties.copy()
          props.update(initcontext)
          
          if not readFiles:
            holdDirectoryMap = handler.generateDirectoryMap(lastargs, self.parent.parent.filefilt, initContext=props)
          else:  
            holdDirectoryMap = handler.generateDirectoryMapFromFiles(lastargs, self.parent.parent.filefilt, initContext=props)
          
          self.parent.parent.datasetNames = [(item,-1) for item in holdDirectoryMap.keys()]
          self.parent.parent.datasetNames.sort()
          tab_name= "Collection %i" % self.parent.parent.top_ct
          page_type = "collection"
          tcolor='lightgreen'
          onoff_flag = False
       else:
          holdDirectoryMap = None
          firstFile = None
          page_type = "offline"
          tab_name= "Offline %i" % self.parent.parent.top_ct
          self.parent.parent.datasetNames = [self.parent.parent.offline_datasetName]
          tcolor='orange'
          onoff_flag = True

       self.parent.parent.ntk.new_page( self.parent.parent, tab_name, tab_color = tcolor,page_type = page_type )

       # Set the iteration values for each page
       selected_page = self.parent.parent.main_frame.selected_top_page
       self.parent.parent.main_frame.dmap[selected_page] = None
       self.parent.parent.main_frame.extraFields[selected_page] = None
       self.parent.parent.main_frame.datasetMapfile[selected_page] = None
       self.parent.parent.main_frame.dirp_firstfile[selected_page] = firstFile
       self.parent.parent.offline_file_directory[selected_page] = "directory"
       self.parent.parent.directoryMap[selected_page] = holdDirectoryMap
       self.parent.parent.hold_offline[selected_page] = onoff_flag
       self.parent.parent.main_frame.projectName[selected_page] = self.project_dataset.get()

    #-----------------------------------------------------------------
    # event to load in the selected project fields
    #-----------------------------------------------------------------
    def evt_reset_project(self, parent, event):
        extraction_controls.load_configuration( self.parent.parent )

    def evt_popup_fields_window(self, parent, projectName ):
        if self.evt_fields_flg: return
        self.evt_fields_flg = True

        #---------------------------------------------------------------------------------
        # Create the Fields dialog window
        #---------------------------------------------------------------------------------
        self.fields = Pmw.Dialog(
            parent,
            buttons = ('OK', 'Cancel'),
            defaultbutton = 'OK',
            title = 'Set Additional Mandatory Fields',
            command = pub_controls.Command(self.close_fields_dialog, parent)
            )


        self.fields.withdraw()
        self.fields.transient( parent )

        frame = Pmw.ScrolledFrame( self.fields.interior(),
                usehullsize = 1,
                horizflex = 'expand',
                )

        # Add additional mandatory fields to allow the user to set default settings
        handler = getHandlerByName(projectName, None, self.Session)
        list_fields = getQueryFields( handler )
        for x in list_fields:
            if handler.isMandatory( x ):
               if x.lower() != "project":
                  field_options = handler.getFieldOptions(x)
                  if field_options is not None:
                     if x in self.defaultGlobalValues.keys():
                        set_to = self.defaultGlobalValues[x]
                     else:
                        set_to = x+" (Default Global Setting)"
                     field_options.insert(0, x+" (Default Global Setting)")
                     self.dataset_fields[x] = show_field( parent, frame.interior(), x.capitalize(), field_options , set_to, 1, 1 )
  
        Pmw.alignlabels( self.dataset_fields.values() )

        frame.pack(side='top', expand=1, fill='both')

        #---------------------------------------------------------------------------------
        # Position dialog popup
        #---------------------------------------------------------------------------------
        import string
        parent_geom = parent.geometry()
        geom = string.split(parent_geom, '+')
        d1 = string.atoi( geom[1] )
        d2 = string.atoi( geom[2] )
        self.fields.geometry( "500x200+%d+%d" % (d1, d2) )
        self.fields.show()

    #---------------------------------------------------------------------------------
    # Close the mandatory fields dialog window
    #---------------------------------------------------------------------------------
    def close_fields_dialog(self, parent, result):
        self.evt_fields_flg = False

        if (result is None or result == 'Cancel'):
            self.fields.destroy()
        else:
            for x in self.parent.parent.pub_buttonexpansion.dataset_widgets.dataset_fields.keys():
              v = self.parent.parent.pub_buttonexpansion.dataset_widgets.dataset_fields[x].get()
              self.defaultGlobalValues[ x ] = v
            self.fields.destroy()


    #-----------------------------------------------------------------
    # event functions to toggle working from online or offline mode
    #-----------------------------------------------------------------
    def evt_work_on_or_off_line( self, tag ):
        # Reset the button colors
        self.cw_dir.configure( background=self.save_dir_btn_color, foreground='black' )
        self.cw_file.configure( background=self.save_file_btn_color, foreground='black' )
        self.cw_reg.configure( background=self.save_reg_btn_color, foreground='black' )

        if tag == "Off-line": 
           self.parent.parent.offline = True

           #self.group_file_filter.pack_forget()
           #self.group_list.pack_forget()
           #self.lw_dir.pack_forget()

           # Clear out the Dataset form and put the white canvas back
           #self.parent.parent.pub_editorviewer.dataset_sframe.pack_forget()
           #self.parent.parent.canvas.pack(expand=1, fill='both')

           # Get the projects and display them to the user
           #projectOption = self.parent.parent.config.get('initialize', 'project_options')
           #projectSpecs = splitRecord(projectOption)
           #self.parent.parent.projectName = projectSpecs[0][0]
           #projects = []
           #for i in range(len(projectSpecs)):
           #    projects.append( projectSpecs[i][0] )
           #projects.sort()
        if tag == "On-line":
           self.parent.parent.offline = False

           self.lw_dir.pack(side='top', before=self.lw_file, expand = 1, fill = 'both', padx=10, pady=10)

           # Clear out the Dataset form and put the white canvas back
           #self.parent.parent.pub_editorviewer.dataset_sframe.pack_forget()
           #self.parent.parent.canvas.pack(expand=1, fill='both')

           self.parent.parent.projectName = None

           #self.group_file_filter.pack(side='top', before=self.group_list_generation, fill='x', pady=3)
           #self.group_list.pack(side='top', after=self.group_list_generation, fill='x')

    #-----------------------------------------------------------------
    # event functions to popup the directory selection window
    # --project cmip5 --read-files
    #-----------------------------------------------------------------
    def evt_popup_directory_window( self ):
       # Reset the button colors
       self.cw_dir.configure( background=self.save_dir_btn_color, foreground='black' )
       self.cw_file.configure( background=self.save_file_btn_color, foreground='black' )
       #self.cw_reg.configure( background=self.save_reg_btn_color, foreground='black' )

       # Start the busy routine to indicate to the users something is happening
       self.parent.parent.busyCursor = 'watch'
       self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' ), self.parent.parent.pane2.pane( 'EditPaneBottom' ), self.parent.parent.pane2.pane( 'EditPaneStatus' ), self.parent.parent.pane.pane( 'ControlPane' )]
       pub_busy.busyStart( self.parent.parent )

       try:
       # if true, then the dataset is not directly readable and on tertiary storage
          if self.parent.parent.offline == True:
             onoff_line = "offline"
             dirfilename = None
	  # Create the dialog to prompt for the entry input
	     self.dialog = Pmw.Dialog(self.parent.control_frame2,
	       title = 'Working off-line',
	       buttons = ('OK', 'Cancel'),
	       defaultbutton = 'OK',
	       command = pub_controls.Command( self.evt_work_off_line_directory, ),
               )

             self.entry1 = Pmw.EntryField(self.dialog.interior(),
		   labelpos = 'w',
		   label_text = 'Directory:',
                entry_width =  75,
                entry_background = 'aliceblue',
                entry_foreground = 'black',
		   )
             self.entry1.pack(side='top', fill='x', expand=1, padx=10, pady=5)
             self.entry2 = Pmw.EntryField(self.dialog.interior(),
		   labelpos = 'w',
		   label_text = 'Dataset Name:',
                entry_width =  75,
                entry_background = 'aliceblue',
                entry_foreground = 'black',
		   )
             self.entry2.pack(side='top', fill='x', expand=1, padx=10, pady=5)

             Pmw.alignlabels((self.entry1, self.entry2))

             parent_geom = self.parent.parent.geometry()
             geom = string.split(parent_geom, '+')
             d1 = string.atoi( geom[1] )
             d2 = string.atoi( geom[2] )
             p1=string.atoi(geom[0].split('x')[0])*0.3
             p2=string.atoi(geom[0].split('x')[1])*0.3
             self.dialog.activate(geometry= "+%d+%d" % (p1+d1, p2+d2) )
             if self.parent.parent.offline_directories != "Cancel":
             # Load up the data information from data extraction
                self.fill_in_data_information_directory( dirfilename, True, onoff_line = onoff_line )
          else:
             onoff_line = "online"
             if self.generating_file_list_flg == 1: return
             dialog_icon = tkFileDialog.Directory(master=self.parent.control_frame2,
                         title = 'Directory and File Selection')
             dirfilename=dialog_icon.show(initialdir=os.getcwd())
             if dirfilename in [(), '']:
                pub_busy.busyEnd( self.parent.parent )
                return

             self.stop_listing_flg = 0

             self.parent.parent.extension = []
             self.parent.parent.extension.append( (self.data_filter._entryfield.get().split()[-1]) )

          # Load up the data information from data extraction
             self.fill_in_data_information_directory( dirfilename, True, onoff_line = onoff_line )

       # Change the color of the selected button
          bcolorbg = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.25 )
          bcolorfg = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.85 )
          self.cw_dir.configure( background=bcolorbg, foreground=bcolorfg )

#
       except:
            pub_busy.busyEnd( self.parent.parent )  # catch here in order to turn off the busy cursor ganz
            raise
       finally:
           pub_busy.busyEnd( self.parent.parent )
#
#       pub_busy.busyEnd( self.parent.parent )

       # Disable the "Data Publication" button
       self.parent.parent.pub_buttonexpansion.ControlButton3.configure( state = 'disabled' )

    #-----------------------------------------------------------------
    # event functions to popup the file selection window
    #-----------------------------------------------------------------
    def evt_popup_file_window( self ):
       # Reset the button colors
       self.cw_dir.configure( background=self.save_dir_btn_color, foreground='black' )
       self.cw_file.configure( background=self.save_file_btn_color, foreground='black' )
       self.cw_reg.configure( background=self.save_reg_btn_color, foreground='black' )

       if self.generating_file_list_flg == 1: return
       dialog_icon = tkFileDialog.Open(master=self.parent.control_frame2,
                      filetypes=pub_controls.filetypes, title = 'File Open Selection')
       dirfilename=dialog_icon.show(initialdir=os.getcwd())
       if dirfilename in [(), '']: return

       # Determine if working online or off-line
       if self.parent.parent.offline == True:
          onoff_line = "offline"
       else:
          onoff_line = "online"

       # Start the busy routine to indicate to the users something is happening
       self.parent.parent.busyCursor = 'watch'
       self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' ), self.parent.parent.pane2.pane( 'EditPaneBottom' ), self.parent.parent.pane2.pane( 'EditPaneStatus' ), self.parent.parent.pane.pane( 'ControlPane' )]
       pub_busy.busyStart( self.parent.parent )
       try:
       # Change the color of the selected button
          bcolorbg = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.25 )
          bcolorfg = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.85 )
          self.cw_file.configure( background=bcolorbg, foreground=bcolorfg )

       # Load up the data information from data extraction. This must be done outside the start of the Thread.
          self.fill_in_data_information_file( dirfilename, onoff_line = onoff_line )
 
       except:
            pub_busy.busyEnd( self.parent.parent )  # catch here in order to turn off the busy cursor ganz
            raise
       finally:
           pub_busy.busyEnd( self.parent.parent )      
#       pub_busy.busyEnd( self.parent.parent )

       # Disable the "Data Publication" button
       self.parent.parent.pub_buttonexpansion.ControlButton3.configure( state = 'disabled' )

    #-----------------------------------------------------------------
    # event function associated with working off-line
    #-----------------------------------------------------------------
    def evt_work_off_line_directory( self, event ):
       if event == "OK":
          self.parent.parent.offline_directories = [ self.entry1.get( ).strip() ]
          self.parent.parent.offline_datasetName = self.entry2.get( ).strip()
          if (len(self.entry1.get( ).strip()) == 0) or (len(self.entry2.get( ).strip()) == 0):
             self.parent.parent.offline_directories = "Cancel"
             self.parent.parent.offline_datasetName = "Cancel"
       elif event == "Cancel":
          self.parent.parent.offline_directories = "Cancel"
          self.parent.parent.offline_datasetName = "Cancel"

       self.dialog.destroy()

    #-----------------------------------------------------------------
    # event functions associated with the "Select Variable" panel
    #-----------------------------------------------------------------
    def evt_change_color( self, event ):
      keycolor = Pmw.Color.changebrightness(self.parent, 'red', 0.85)
      self.directory_combo.configure( entry_background = keycolor )

    #----------------------------------------------------------------------------------------
    # event for directory entry only, search for a tab entry
    #----------------------------------------------------------------------------------------
    def evt_tab( self, event ):
      s=string.split( self.directory_combo.get(), '/' )[-1]
      s2=string.split( self.directory_combo.get(), '/' )
      d = ''
      for x in os.listdir( './' ):
         if os.path.isfile( x ):
           pass
         else:
            if string.find( x, s ) == 0:
               if len(d):
                  if len(d) > len(x):
                     d = x
               else:
                  d = x
      if d == '': d = s2[-1]
      r = ''
      for x in s2[1:-1]: r = r + '/' + x
      r = r + '/' + d
      self.directory_combo.delete( 0, 'end' )
      self.directory_combo.setentry( r )
      #
      self.evt_enter_directory( None )
      #
      # Override the behavior of the Tab for this widget.
      # Just do the above and stop.
      return "break"

    #----------------------------------------------------------------------------------------
    # event for directory entry only, search for back space entry
    #----------------------------------------------------------------------------------------
    def evt_backspace( self, event ):
      keycolor = Pmw.Color.changebrightness(self.parent, 'red', 0.85)
      self.directory_combo.configure( entry_background = keycolor )
      t = self.directory_combo.get()
      s=string.split( t, '/' )[-1]
      if s == '':
         self.evt_enter_directory( None )

    #----------------------------------------------------------------------------------------
    # Event if text entered into the directory entry  window
    #----------------------------------------------------------------------------------------
    def evt_enter_directory( self, event ):
      # change backgound color to white
      self.directory_combo.configure( entry_background = 'white' )

    #----------------------------------------------------------------------------------------
    # Event to set the stop_listing flag
    #----------------------------------------------------------------------------------------
    def stop_listing( self ):
      self.stop_listing_flg = 1

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
