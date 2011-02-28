#!/usr/bin/env python
#
# The Publisher Button Expansion Controls -  pub_buttonexpansion module
#
###############################################################################
#                                                                             #
# Module:       pub_buttonexpansion module                                    #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore NationalLaboratory:                        #
#                                                                             #
# Description:  Publisher button expansion that is found on the left side of  #
#               GUI. When a button is selected, it expand to show additional  #
#               controls.                                                     #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFileDialog
import os, string
import pub_editorviewer
import pub_controls
import pub_busy
import thread

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

      #----------------------------------------------------------------------------------------
      # Begin the creation of the file type selection
      #----------------------------------------------------------------------------------------
      self.group_file_filter = Pmw.Group(self.parent.control_frame1,
                        tag_text = 'Filter File Search',
                        tag_font = ('Times', 18, 'bold'),
                        tagindent = 25)

      self.data_filter = Pmw.ComboBox( self.group_file_filter.interior(),
                             scrolledlist_items = pub_controls.datatypes,
                             entryfield_value = pub_controls.datatypes[0],
                         #    label_text = 'Filter File Search:',
                         #    labelpos = 'w',
                             entry_state = 'readonly',
                             entry_font = ('Times', 16, 'bold'),
                             entry_background='white', entry_foreground='black',
                             #selectioncommand=pub_controls.Command(self.evt_data_filter)
                             )
      #self.parent.balloon.bind(self.data_filter, "Return specific files.")
      #self.parent.balloon.bind( self.data_filter._arrowBtn, 'Files types.' )

      self.data_filter.pack(side = 'top', fill='x', pady = 5)
      self.group_file_filter.pack(side='top', fill='x', pady=3)
      #----------------------------------------------------------------------------------------
      # End the creation of the file type selection
      #----------------------------------------------------------------------------------------

      #----------------------------------------------------------------------------------------
      # Begin the creation of the directory, file, and combo directoy box
      #----------------------------------------------------------------------------------------
      #self.parent.control_frame2 = Tkinter.Frame(self.parent.control_frame1, width=5,height=5, background='aliceblue')
      self.group_list_generation = Pmw.Group(self.parent.control_frame1,
                        tag_text = 'Generate List',
                        tag_font = ('Times', 18, 'bold'),
                        tagindent = 25)
      self.parent.control_frame2 = self.group_list_generation.interior()

      self.directory_icon = Tkinter.PhotoImage(file=file2_gif)
      self.file_icon = Tkinter.PhotoImage(file=folder2_gif)
      self.stop_icon = Tkinter.PhotoImage(file=stop_gif)

      # Create the directory button icon
      lw = Pmw.LabeledWidget(self.parent.control_frame2,
	               labelpos = 'w',
	               label_text = "Generate list from directory: ",
                       label_font = ('Times', 16, 'bold'),
                       hull_relief='raised',
                       hull_borderwidth=2,
                       )
      lw.pack(fill = 'x', padx=1, pady=3)

      self.generating_file_list_flg = 0
      self.directory_button = Tkinter.Button(lw.interior(),
                       image = self.directory_icon,
                       bg = 'lightblue',
                       command = pub_controls.Command(self.evt_popup_directory_window)
                       )
      self.directory_button.image = self.directory_icon # save the image from garbage collection
      #self.parent.balloon.bind(self.directory_button, "Popup directory selection window.")
      self.directory_button.pack(side = 'left', fill = 'x')

      # Create the file button icon
      lw = Pmw.LabeledWidget(self.parent.control_frame2,
	               labelpos = 'w',
	               label_text = "Generate list from file:         ",
                       label_font = ('Times', 16, 'bold'),
                       hull_relief='raised',
                       hull_borderwidth=2,
                       )
      lw.pack(fill = 'x', padx=1, pady=3)
      self.file_button = Tkinter.Button(lw.interior(),
                       image = self.file_icon,
                       bg = 'lightblue',
                       command = pub_controls.Command(self.evt_popup_file_window)
                       )
      self.file_button.image = self.file_icon # save the image from garbage collection
      #self.parent.balloon.bind(self.file_button, "Popup text file selection window.")
      self.file_button.pack(side = 'left', fill = 'x')

      # Set up directory combo box
      d,f = _scn_a_dir( self.parent )
      self.directory_combo = Pmw.ComboBox( self.parent.control_frame2,
                             scrolledlist_items = d,
                             entryfield_value = os.getcwd(),
                             entry_font = ('Times', 16, 'bold'),
                             entry_background='white', entry_foreground='black',
                             selectioncommand=pub_controls.Command(self.evt_enter_directory)
                             )
      #self.directory_combo.configure( menubutton_text=gui_control.dbdchlst[0] )
      #self.parent.balloon.bind(self.directory_combo, "Enter directory and/or text file.")
      #self.parent.balloon.bind( self.directory_combo._arrowBtn, 'View and select directories to generate dataset list.' )

      self.directory_combo.component('entry').bind( "<Key>", pub_controls.Command(self.evt_change_color) )
      self.directory_combo.component('entry').bind( "<Return>", pub_controls.Command(self.evt_enter_directory) )
      self.directory_combo.component('entry').bind('<Tab>', pub_controls.Command(self.evt_tab) )
      self.directory_combo.component('entry').bind( "<BackSpace>", pub_controls.Command(self.evt_backspace) )

      #self.directory_combo.pack(side = 'left', expand = 1, fill='x')

      # Create the stop button icon
      lw = Pmw.LabeledWidget(self.parent.control_frame2,
	               labelpos = 'w',
	               label_text = "Stop list generation:             ",
                       label_font = ('Times', 16, 'bold'),
                       hull_relief='raised',
                       hull_borderwidth=2,
                       )
      lw.pack(fill = 'x', padx=1, pady=3)
      self.stop_listing_flg = 0
      self.stop_button = Tkinter.Button(lw.interior(),
                       image = self.stop_icon,
                       bg = 'lightblue',
                       command = pub_controls.Command(self.stop_listing)
                       )
      self.stop_button.image = self.stop_icon # save the image from garbage collection
      #self.parent.balloon.bind( self.stop_button, "Stop the generation of the dataset list.")
      self.stop_button.pack(side = 'left', fill = 'x')

      self.parent.control_frame2.pack(side="top", fill = 'x', pady=5)
      self.group_list_generation.pack(side='top', fill='x', pady=3)
      #----------------------------------------------------------------------------------------
      # End the creation of the directory, file, and combo directoy box
      #----------------------------------------------------------------------------------------

      #----------------------------------------------------------------------------------------
      # Begin the regular expression widget
      #----------------------------------------------------------------------------------------
      self.group_list = Pmw.Group(self.parent.control_frame1,
                        tag_text = 'Regular Expressions',
                        tag_font = ('Times', 18, 'bold'),
                        tagindent = 25)
      self.group_list.pack(side='top', fill='x')

      self.scl1 = Pmw.ScrolledText( self.group_list.interior(),
                                 text_background='aliceblue',
                                 text_foreground='black',
                                 text_wrap = 'none',
                                 usehullsize = 1,
                                 hull_width = 100,
                                 hull_height = 100)
                                 #horizscrollbar_width=50,
                                 #vertscrollbar_width=50 )
      #self.scl1.grid(row=0, column=0 )
      self.scl1.pack(side='top', expand=1, fill='both')

      # Create and pack a vertical RadioSelect widget, with checkbuttons.
      self.checkbuttons = Pmw.RadioSelect(self.group_list.interior(),
                buttontype = 'checkbutton',
                orient = 'horizontal',
                labelpos = 'w',
        #       command = self.checkbuttoncallback,
                hull_borderwidth = 2,
                hull_relief = 'ridge',
      )
      self.checkbuttons.pack(side = 'top', expand = 1, padx = 10, pady = 10)

      # Add some buttons to the checkbutton RadioSelect.
      for text in ('Ignore Case', 'Multi-Line', 'Verbose'):
                  self.checkbuttons.add(text)
      #self.checkbuttons.invoke('Ignore Case')
      #self.checkbuttons.invoke('Find All')
      #----------------------------------------------------------------------------------------
      # End the regular expression widget
      #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    # From a directory path name, generate the dynamic list of files and their
    # sizes in the directory tree.
    #----------------------------------------------------------------------------------------
    def myfun3( self, dirp, lock ):
       import fnmatch, time

       index_count = 0
       lock.acquire()

       for root, dirs, files in os.walk(dirp):
          for filename in files:
              if fnmatch.fnmatch(filename, self.extension[0]):
                  sfilename = os.path.join(root, filename)
                  filesize = os.path.getsize(sfilename)
                  self.parent.parent.file_line.append(pub_editorviewer.create_publisher_editor_viewer_row(self.parent.parent, index = index_count, size = filesize, status_flg = 1, filename = sfilename))
                  index_count+=1

                  time.sleep(0.1)    # Must wait for the row to be generated before moving on.

              if self.stop_listing_flg == 1 and index_count > 0:
                 pub_busy.busyEnd( self.parent.parent )
                 self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
                 self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')
                 self.parent.parent.file_counter = index_count
                 time.sleep(0.1)    # Must wait for the row to be generated before moving on.
                 self.parent.parent.log_window.appendtext("File list creation stopped. %s files in list.\n" % index_count)
                 self.generating_file_list_flg = 0
                 thread.exit()
       lock.release()

       self.parent.parent.file_counter = index_count

       pub_busy.busyEnd( self.parent.parent )

       if index_count > 0:
          self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
          self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')

       self.parent.parent.log_window.appendtext("Finished creating the file list. %s files in list.\n" % index_count)
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
       for dirfile in f:
           sfilename = dirfile[:-1]
           filesize = os.path.getsize(sfilename)
           self.parent.parent.file_line.append(pub_editorviewer.create_publisher_editor_viewer_row(self.parent.parent, index = index_count, size = filesize, status_flg = 0, filename = sfilename))
           index_count+=1

           time.sleep(0.1)    # Must wait for the row to be generated before moving on.

           if self.stop_listing_flg == 1:
              pub_busy.busyEnd( self.parent.parent )
              self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
              self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')
              self.parent.parent.file_counter = index_count
              time.sleep(0.1)    # Must wait for the row to be generated before moving on.
              self.parent.parent.log_window.appendtext("File list creation stopped. %s files in list.\n" % index_count)
              self.generating_file_list_flg = 0
              thread.exit()

       f.close()

       lock.release()

       self.parent.parent.file_counter = index_count

       pub_busy.busyEnd( self.parent.parent )
       self.parent.parent.pub_editorviewer.sf.configure(hscrollmode = 'dynamic')
       self.parent.parent.pub_editorviewer.sf.configure(vscrollmode = 'dynamic')

       self.parent.parent.log_window.appendtext("Finished creating the file list. %s files in list.\n" % index_count)
       self.generating_file_list_flg = 0

    #-----------------------------------------------------------------
    # event functions to popup the directory selection window
    #-----------------------------------------------------------------
    def evt_popup_directory_window( self ):
       if self.generating_file_list_flg == 1: return
       dialog_icon = tkFileDialog.Directory(master=self.parent.control_frame2,
                         title = 'Directory and File Selection')
       dirfilename=dialog_icon.show(initialdir=os.getcwd())
       if dirfilename in [(), '']: return

       self.stop_listing_flg = 0

       self.extension = []
       self.parent.extension.append( (self.data_filter._entryfield.get().split()[-1]) )

       # Set up the thread to do asynchronous I/O
       self.stop_listing_flg = 0

       self.parent.parent.busyCursor = 'watch'
       self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' )]
       # note this busy cursor is reset in the method myfun3
       pub_busy.busyStart(self.parent.parent)

       # Remove the old list
       if self.parent.parent.file_counter > 0:
          self.parent.parent.pub_editorviewer.sf.destroy()
          self.parent.parent.pub_editorviewer = pub_editorviewer.create_publisher_editor_viewer( self.parent.parent )

       self.parent.parent.log_window.appendtext("Creating the file list...\n")
       self.generating_file_list_flg = 1
       lock=thread.allocate_lock()
       thread.start_new_thread( self.myfun3, (dirfilename,lock) )

    #-----------------------------------------------------------------
    # event functions to popup the file selection window
    #-----------------------------------------------------------------
    def evt_popup_file_window( self ):
       if self.generating_file_list_flg == 1: return
       dialog_icon = tkFileDialog.Open(master=self.parent.control_frame2,
                         filetypes=pub_controls.filetypes, title = 'File Open Selection')
       dirfilename=dialog_icon.show(initialdir=os.getcwd())
       if dirfilename in [(), '']: return

       # Set up the thread to do asynchronous I/O
       self.stop_listing_flg = 0

       self.parent.parent.busyCursor = 'watch'
       self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' )]
       
       # Note: this busy cursor is reset in open_text_file
       pub_busy.busyStart(self.parent.parent)

       # Remove the old list
       if self.parent.parent.file_counter > 0:
          self.parent.parent.pub_editorviewer.sf.destroy()
          self.parent.parent.pub_editorviewer = pub_editorviewer.create_publisher_editor_viewer( self.parent.parent )

       self.parent.parent.log_window.appendtext("Creating the file list...\n")
       self.generating_file_list_flg = 1
       lock=thread.allocate_lock()
       thread.start_new_thread( self.open_text_file, (dirfilename,lock) )

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
