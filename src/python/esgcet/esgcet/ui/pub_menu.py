#!/usr/bin/env python
#
# The Publisher Menu Bar -  pub_menu module
#
###############################################################################
#                                                                             #
# Module:       pub_menu module                                               #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Publisher main menu bar.                                      #
#                                                                             #
#                                                                             #
###############################################################################
#
from Tkinter import *
import Tkinter, Pmw, tkFont
import os, string
import gui_support
import pub_controls
import logging
import pub_busy
import pub_expand_deletion_control_gui
from help_ScrolledText import Help
from help_HTML import helpHTML
from help_File_HTML import LocalHelpHTML
from esgcet.messaging import warning
from esgcet.publish import deleteDatasetList, DELETE, UNPUBLISH, publishDatasetList
from pkg_resources import resource_filename
from esgcet.publish.utility import generateDatasetVersionId
from esgcet.config import *


on_icon  = resource_filename('esgcet.ui', 'on.gif')
off_icon = resource_filename('esgcet.ui', 'off.gif')
validate_st_names = True

def getConfigFile(configFile=None):
          
    
        # First check the environment variable ESGINI
        configFile = os.environ.get('ESGINI')
        if configFile is not None:
            if not os.path.exists(configFile):
                raise ESGPublishError("Cannot find configuration file (specified in $ESGINI): %s"%configFile)
            else:
                return configFile               
        else:
            
            # Then look in $HOME/.esgcet/esg.ini
            home = os.environ.get('HOME')
            if home is not None:
                configFile = os.path.join(home, '.esgcet', 'esg.ini')
            if configFile is not None and os.path.exists(configFile):
                return configFile

            # If not found, look in the Python installation directory
            
        if (configFile == None):
              msg = 'The esg.ini file cannot be found in $HOME/.esgcet'
              msg = msg + '\nPlease copy it there and retry command.'
              showwarning('Warning',msg)
              raise(msg)
        #return configFile
 
#----------------------------------------------------------------------------------------
# Function to change the color of a widget
#----------------------------------------------------------------------------------------
def evt_change_color( widget, parent, event ):
   keycolor = Pmw.Color.changebrightness(parent, 'red', 0.85)
   (widget).configure( entry_background = keycolor )

#----------------------------------------------------------------------------------------
# Read esg.ini file and pull out the log filename
#----------------------------------------------------------------------------------------
def return_log_file_name( parent ):
#   fp = open(parent.init_file, 'r') 
   from tkMessageBox import showinfo, showwarning, showerror
   configFile = getConfigFile()
   found = False
   fp = open(configFile, 'r')
   for x in fp.xreadlines():
      if x.find("# log_filename") != -1: 
          found = True
          break
   fp.close()
 
   config = loadConfig(None)
   section =  'extract'
   log_filename = config.get(section, 'log_filename', default=None)
   if (log_filename != None): 
       print log_filename
       return log_filename
 
   if (found == False):    
       msg = 'The esg.ini file does not specify a log file. '
       msg = msg + '\nPlease add one, e.g. # log_filename,  and retry command.'
       showwarning('Warning',msg)
       raise(msg)
     
   return x
    
#----------------------------------------------------------------------------------------
# Read esg.ini file and pull out the log level for each configuration
#----------------------------------------------------------------------------------------
def return_log_settings_from_ini_file( parent ):
   shared_opt_flg = False
   db_init_flg = False
   proj_spec_flg = False
   md_extract_flg = False
   shared_opt_invoke='Warning'
   db_init_invoke = 'Warning'
   proj_spec_invoke='Warning'
   md_extract_invoke='Warning'

   from functools import partial as pto
   from Tkinter import Tk, Button, X
   from tkMessageBox import showinfo, showwarning, showerror
   import os.path
    
 
   try:   
       configFile = getConfigFile()
   except :
       print "Error getting config file ", sys.exc_info()
       
     
   
   if (configFile == None):
       return
   try:
      #fp = open(parent.init_file, 'r')
      fp = open(configFile, 'r')
      for x in fp.xreadlines():
         if x.find("# Shared options") != -1: 
          shared_opt_flg = True
          db_init_flg = False
          proj_spec_flg = False
          md_extract_flg = False
         if x.find("# Database initialization") != -1:
          shared_opt_flg = False
          db_init_flg = True
          proj_spec_flg = False
          md_extract_flg = False
         if x.find("# Project-specific configuration") != -1:
          shared_opt_flg = False
          db_init_flg = False
          proj_spec_flg = True
          md_extract_flg = False
         if x.find("# Metadata extraction") != -1:
          shared_opt_flg = False
          db_init_flg = False
          proj_spec_flg = False
          md_extract_flg = True
         if ( (x.find("log_level") != -1) and shared_opt_flg ):
           shared_opt_flg = False
           shared_opt_invoke =  x[(x.find("=")+1):].strip().capitalize()
         if ( (x.find("log_level") != -1) and db_init_flg ):
           db_init_flg = False
           db_init_invoke =  x[(x.find("=")+1):].strip().capitalize()
         if ( (x.find("log_level") != -1) and proj_spec_flg ):
           proj_spec_flg = False
           proj_spec_invoke =  x[(x.find("=")+1):].strip().capitalize()
         if ( (x.find("log_level") != -1) and md_extract_flg ):
           md_extract_flg = False
           md_extract_invoke =  x[(x.find("=")+1):].strip().capitalize()
      fp.close()

   except:
       pass
   
   #print "Preferences for logging: "
   """
   if shared_opt_flg == True:
       print "shared_opt_flg log level is ON "
   if db_init_flg == True:
       print "db_init_flg log level is ON "
   if proj_spec_flg == True:
       print "proj_spec_flg log level is ON "      
   if md_extract_flg == True:
       print "md_extract_flg log level is ON "  
   
   print "shared_opt_invoke log level is set to  ", shared_opt_invoke
   print "db_init_invoke log level is set to  ", db_init_invoke
   print "proj_spec_invoke log level is set to  ", proj_spec_invoke
   print "md_extract_invoke log level is set to  ", md_extract_invoke
   """
  
   
   return shared_opt_invoke, db_init_invoke, proj_spec_invoke, md_extract_invoke

#----------------------------------------------------------------------------------------
# Begin the creation of the publisher menu and its menu items
#----------------------------------------------------------------------------------------
class create_publisher_menu:
   def __init__( self, top_parent, parent ):
      # create the main toplevel menu
      self.main_menu = Pmw.MenuBar(top_parent,
                hull_relief = 'raised',
                hull_borderwidth = 2,
                balloon = parent.balloon
                )
      self.main_menu.pack(side='top', fill='x')

      parent.protocol("WM_DELETE_WINDOW", pub_controls.Command(exit_publisher, parent))

      tear_it = 1

      #-------------------------------------------
      # menu 1 -- 'Publisher'
      #-------------------------------------------
      self.preferences = create_file_menu( self.main_menu, parent, tear_it )

      #-------------------------------------------
      # menu 2 -- 'Dataset'
      #-------------------------------------------
      self.Dataset = create_dataset_menu( self.main_menu, parent, tear_it )

      #-------------------------------------------
      # menu 3 -- 'login'
      #-------------------------------------------
      #self.login_menu = create_login_menu( self.main_menu, parent, 0)

      #-------------------------------------------
      # menu 4 -- 'Help'
      #-------------------------------------------
      create_help_menu( self.main_menu, parent, tear_it)

#-----------------------------------------------------
# Save GUI settings
#-----------------------------------------------------
def save_GUI_state( parent ):
    import datetime

    n=datetime.datetime.now().timetuple()
    time = 'timestamp = '+str(n[1])+"-"+str(n[2])+"-"+str(n[0])+"_"+str(n[3])+":"+str(n[4])+":"+str(n[5])

    # Get the users $HOME directory
    try:
       fn = '%s' % os.environ['HOME']
    except:
       return # could not find the user's home directory to save GUI settings

    #
    # Create .esgcet directory if it does not exist
    fn += "/.esgcet"
    print " fn = ", fn
    if os.access(fn, os.X_OK) == 0:
      try:
         os.mkdir( fn )
      except:
         return # Do not have write permission for home directory. Must have write permissions
         sys.exit()

    file_name = fn + '/esgpublish_gui_settings.py'
    print "file name = ", file_name
    fp = open(file_name, 'w')

    fp.write("# " + time+"\n\n")
    fp.write("class get:\n")
    fp.write("#                                                    \n")
    fp.write("#####################################################\n")
    fp.write("# GUI Geometry Settings                             #\n")
    fp.write("#####################################################\n")
    fp.write("#                                                    \n")
    geometry = parent.geometry()
    geometry = string.split(geometry, 'x')
    fp.write("   gui_width = %s                                  # GUI Width\n" % geometry[0])
    geometry = string.split(geometry[1], '+')
    fp.write("   gui_height = %s                                 # GUI Height\n" % geometry[0])
    fp.write("   gui_x_position = %s                             # GUI X Position\n" % geometry[1])
    fp.write("   gui_y_position = %s                             # GUI Y Position\n" % geometry[2])

    fp.write("#####################################################\n")
    fp.write("# Pane Settings                                     #\n")
    fp.write("#####################################################\n")
    fp.write("#                                                    \n")
    fp.write("   ControlPane_size = %d                         # Select variable size pane position\n" % parent.pane._size['ControlPane'] )
    fp.write("   EditPaneTop_size = %d                         # Select variable size pane2 position\n" % parent.pane2._size['EditPaneTop'] )
    fp.write("   EditPaneBottom_size = %d                         # Select variable size pane2 position\n" % parent.pane2._size['EditPaneBottom'] )
    fp.write("   EditPaneStatus_size = %d                         # Select variable size pane2 position\n" % parent.pane2._size['EditPaneStatus'] )

#    fp.write("   ControlPane_min = %d                         # Select variable min pane position\n" % parent.pane._min['ControlPane'] )
#    fp.write("   ControlPane_max = %d                         # Select variable max pane position\n" % parent.pane._max['ControlPane'] )
#    fp.write("   EditPaneTop_min = %d                         # Select variable min pane2 position\n" % parent.pane2._min['EditPaneTop'] )
#    fp.write("   EditPaneTop_max = %d                         # Select variable max pane2 position\n" % parent.pane2._max['EditPaneTop'] )
#    fp.write("   EditPaneBottom_min  = %d                         # Select variable min pane2 position\n" % parent.pane2._min['EditPaneBottom'] )
#    fp.write("   EditPaneBottom_max  = %d                         # Select variable max pane2 position\n" % parent.pane2._max['EditPaneBottom'] )
#    fp.write("   EditPaneStatus_min  = %d                         # Select variable min pane2 position\n" % parent.pane2._min['EditPaneStatus'] )
#    fp.write("   EditPaneStatus_max  = %d                         # Select variable max pane2 position\n" % parent.pane2._max['EditPaneStatus'] )


    fp.flush()
    fp.close()


#----------------------------------------------------------------------------------------
# Event for "Exiting" the Publisher GUI
#----------------------------------------------------------------------------------------
class exit_publisher:
   """
   Event to 'end' or 'exist' the Publisher GUI.
   """
   def __init__(self, parent ):
      save_GUI_state( parent )
      parent.destroy() # sys.exit( 0 ) is an alternative way to exit

#----------------------------------------------------------------------------------------
# Begin the creation of the file menu and its menu items
#----------------------------------------------------------------------------------------
class create_file_menu:
   """
   Create the main Publisher menu -- located in the top part of the left pane.
   """
   def __init__( self, main_menu, parent, tear_it ):
      file_name = 'Publisher'
      mnFont=tkFont.Font(parent, family = pub_controls.menu_font_type, size=pub_controls.menu_font_size, weight=pub_controls.mnfont_weight)
      
      main_menu.addmenu(file_name, 'Publisher Preferences and Options', font = mnFont, tearoff = tear_it)
      #---------------------------------------------------------------------------------
      # Create the "Preferences" menu item
      #---------------------------------------------------------------------------------
      self.evt_preferences_flg = False
      #""" ganz to remove preferences option....
      main_menu.addmenuitem(file_name, 'command', 'Set Publisher Preferences',
                         label = 'Preferences...',
                         font = mnFont,
                         command = pub_controls.Command(self.evt_preferences, parent)
                        )
      #---------------------------------------------------------------------------------
      # Create the cascade "Exit" menu and its items
      #---------------------------------------------------------------------------------
      main_menu.addmenuitem(file_name, 'separator')
      #"""
      main_menu.addmenuitem(file_name, 'command', 'Close Publisher',
                          label = "Exit Publisher",
                          font = mnFont,
                          command = pub_controls.Command(exit_publisher, parent)
                         )

   #---------------------------------------------------------------------------------
   # Create the "Preference" popup with tabs
   #---------------------------------------------------------------------------------
   def evt_preferences( self, parent ):
        if self.evt_preferences_flg: return
        self.evt_preferences_flg = True

        #---------------------------------------------------------------------------------
        # Create the Preference dialog
        #---------------------------------------------------------------------------------
        self.pref_dialog = Pmw.Dialog(
            parent,
            buttons = ('OK', 'Cancel'),
            defaultbutton = 'OK',
            title = 'Preferences',
            command = pub_controls.Command(self.close_pref_dialog, parent)
            )

        self.pref_dialog.withdraw()
        self.pref_dialog.transient( parent )

        #---------------------------------------------------------------------------------
	# Create and pack the NoteBook
        #---------------------------------------------------------------------------------
        notebook = Pmw.NoteBook( self.pref_dialog.interior() )
        notebook.pack(fill = 'both', expand = 1, padx = 10, pady = 10)

        #---------------------------------------------------------------------------------
        # Add the "Appearance" page to the notebook
        #---------------------------------------------------------------------------------
        # ganz disable General tab, this info is not useful, at this time. 3/29/11
        #page = notebook.add('General')
        #self.general_settings = set_general( page, parent )
        #notebook.tab('General').focus_set()

        page = notebook.add('Log Level')
        # ganz added this code 1/20/11
        try:
            self.log_settings = set_log_preferences( page, parent )
        
        
          
        except:
          print "set_log_preferences call failed...", sys.exc_info()
          return

        notebook.setnaturalsize()

        #---------------------------------------------------------------------------------
        # Position dialog popup
        #---------------------------------------------------------------------------------
        import string
        parent_geom = parent.geometry()
        geom = string.split(parent_geom, '+')
        d1 = string.atoi( geom[1] )
        d2 = string.atoi( geom[2] )
        self.pref_dialog.geometry( "650x440+%d+%d" % (d1, d2) )
        self.pref_dialog.show() 

   #---------------------------------------------------------------------------------
   # Remove the Preference dialog
   #---------------------------------------------------------------------------------
   def close_pref_dialog(self, parent, result):
        self.evt_preferences_flg = False

        if (result is None or result == 'Cancel'):
            self.pref_dialog.destroy()
        else:
            parent.echoSql = parent.menu.preferences.log_settings.echo_sql.getvalue().strip().replace(' ', '')
            newlog = parent.menu.preferences.log_settings.log_dirname_str.getvalue().strip().replace(' ', '')
            if newlog != '':
               parent.log_dirname = newlog
            parent.aggregateDimension = self.general_settings.aggr_dim.getvalue() 
            parent.engine.echo = eval( parent.echoSql )
            parent.validateStandardName=self.general_settings.validate_std_name.getvalue()
            self.pref_dialog.destroy()

class set_general:
   """
   Set up the General Preference tab page. Allows the user to set the initialization file, 
   aggregation dimension, and validate standard names.
   """
   
   
   def __init__( self, page, parent ):

        frame = Tkinter.Frame( page )

        #---------------------------------------------------------------------------------
	# Create and pack the EntryFields to show the initialization file
        #---------------------------------------------------------------------------------
        configFile = getConfigFile()
	self.init_file = Pmw.EntryField(frame,
		labelpos = 'w',
		label_text = 'Initialization File: ',
                entry_background = "aliceblue",
                entry_width =  60,
                value = configFile,
                )
        self.init_file.pack(side = 'top', expand = 1, fill = 'x', pady = 5 )
        self.init_file.component('entry').bind('<KeyPress>', pub_controls.Command(evt_change_color, self.init_file, parent ))

        #---------------------------------------------------------------------------------
	# Create and pack the EntryFields to show the aggregate dimension
        #---------------------------------------------------------------------------------
	self.aggr_dim = Pmw.EntryField(frame,
		labelpos = 'w',
		label_text = 'Aggregate Dimension: ',
                entry_background = "aliceblue",
                entry_width =  60,
                value = parent.aggregateDimension,
                )
        self.aggr_dim.pack(side = 'top', expand = 1, fill = 'x', pady = 5 )
        self.aggr_dim.component('entry').bind('<KeyPress>', pub_controls.Command(evt_change_color, self.aggr_dim, parent ))

        frame.pack(side='top', fill='x')

        sep1 = Tkinter.Frame ( page, relief = 'raised', height = 4, borderwidth = 2, background='purple')
        sep1.pack( side='top', fill = 'x' )

        #--------------------------------------------------------------------------------------
        # Create and pack a RadioSelect widget, with radiobuttons for "Validate Standard Name"
        #--------------------------------------------------------------------------------------
        self.validate_std_name = Pmw.RadioSelect(page,
                buttontype = 'radiobutton',
                orient = 'horizontal',
                labelpos = 'w',
                label_text = 'Validate Standard Names: ',
        )
        self.validate_std_name.pack(side = 'top', fill='x', padx = 10, pady = 10)

        #---------------------------------------------------------------------------------
        # Add buttons to the Echo SQL Commands RadioSelect
        #---------------------------------------------------------------------------------
        for text in ('True', 'False'):
            self.validate_std_name.add(text)
        self.validate_std_name.setvalue(str(parent.validateStandardName))

        entries = ( self.init_file, self.aggr_dim, self.validate_std_name )
        Pmw.alignlabels(entries)
        

class set_log_preferences:
   """
   Set up the Log Preference tab page -- shows the "Output" log filename and toggle to indicate whether or not to show Echo SQL Commands.
   """
   
   def __init__( self, page, parent ):

        shared_opt_invoke, db_init_invoke, proj_spec_invoke, md_extract_invoke = return_log_settings_from_ini_file( parent )
        #---------------------------------------------------------------------------------
	# Create and pack a log filename widget, with checkbutton
        #---------------------------------------------------------------------------------
        frame = Tkinter.Frame( page )
        self.log_dirname_btn=Tkinter.Button( frame,
            text = 'Output Log Filename',
            background = 'aliceblue',
            command = pub_controls.Command(self.evt_log_dirname, parent)
            )
        self.log_dirname_btn.pack(side = 'left', expand = 1, fill = 'x', padx = 5, pady = 5 )

        #---------------------------------------------------------------------------------
	# Create and pack the EntryFields to show the log directory and filename
        #---------------------------------------------------------------------------------
	self.log_dirname_str = Pmw.EntryField(frame,
                entry_state='disabled',
                entry_disabledbackground = "pink",
                entry_disabledforeground = "black",
                entry_width =  160,
                )
        self.log_dirname_str.pack(side = 'left', expand = 1, fill = 'x', padx = 5, pady = 5 )
        
        fn = return_log_file_name( parent ).strip()
        if fn[0] != "#":
           fn = fn[fn.find("=")+1:].strip()
           if fn!='':
              parent.log_dirname = fn
              self.log_dirname_str.setvalue(fn)

        frame.pack(side='top', fill='x')

        sep1 = Tkinter.Frame ( page, relief = 'raised', height = 4, borderwidth = 2, background='purple')
        sep1.pack( side='top', fill = 'x' )

        #---------------------------------------------------------------------------------
        # Create and pack a RadioSelect widget, with radiobuttons for "Echo SQL Commands"
        #---------------------------------------------------------------------------------
        self.echo_sql = Pmw.RadioSelect(page,
                buttontype = 'radiobutton',
                orient = 'horizontal',
                labelpos = 'w',
                label_text = 'Echo SQL Commands: ',
        )
        self.echo_sql.pack(side = 'top', fill='x', padx = 10, pady = 10)

        #---------------------------------------------------------------------------------
        # Add buttons to the Echo SQL Commands RadioSelect
        #---------------------------------------------------------------------------------
        for text in ('True', 'False'):
            self.echo_sql.add(text)
        self.echo_sql.setvalue(str(parent.echoSql))
       
        entries = ( self.echo_sql, self.log_dirname_btn  )
        Pmw.alignlabels(entries)

   def evt_log_dirname( self, parent ):
       import os
       import tkFileDialog

       dialog_icon = tkFileDialog.SaveAs(master=self.log_dirname_btn,
                         filetypes=[("Text files", "*.txt", "TEXT")], title = 'Save Log Output In...')
       dirfilename=dialog_icon.show(initialdir=os.getcwd())
       if (dirfilename != None):
           self.log_dirname_str.setvalue( dirfilename )
       else:
           self.log_dirname_str.setvalue( parent.log_dirname )


#----------------------------------------------------------------------------------------
# Begin the creation of the dataset menu and its menu items
#----------------------------------------------------------------------------------------
class create_dataset_menu:
   """
   Create the dataset menu and its menu items.
   """
   
   #DeleteLocalDB =  None
   #DeleteGateway =  None
   #DeleteThredds =  None

   
   def __init__( self, main_menu, parent, tear_it ):
      self.Session = parent.Session

      # Set the arrow icons
      self.on  = Tkinter.PhotoImage(file=on_icon)
      self.off = Tkinter.PhotoImage(file=off_icon)
      
      dataset_name = 'Dataset'
      mnFont=tkFont.Font(parent, family = pub_controls.menu_font_type, size=pub_controls.menu_font_size, weight=pub_controls.mnfont_weight)
      main_menu.addmenu(dataset_name, 'Publisher Dataset', side='left', font = mnFont, tearoff = tear_it)

      #-----------------------------------------------------------------------------------
      # Create the "Select All" menu item
      #-----------------------------------------------------------------------------------
      self.remove_dataset = main_menu.addmenuitem(dataset_name, 'command', 'Select All',
                         label = 'Select All',
                         font = mnFont,
                         command = pub_controls.Command(self.evt_select_all_dataset, parent)
                        )

      #-----------------------------------------------------------------------------------
      # Create the "Unselect All" menu item
      #-----------------------------------------------------------------------------------
      self.remove_dataset = main_menu.addmenuitem(dataset_name, 'command', 'Unselect All',
                         label = 'Unselect All',
                         font = mnFont,
                         command = pub_controls.Command(self.evt_unselect_all_dataset, parent)
                        )

#      main_menu.addmenuitem(dataset_name, 'separator')

      #-----------------------------------------------------------------------------------
      # Create the "Remove" menu item
      #-----------------------------------------------------------------------------------
#      self.remove_dataset = main_menu.addmenuitem(dataset_name, 'command', 'Remove dataset',
#                         label = 'Remove',
#                         font = mnFont,
#                         command = pub_controls.Command(self.evt_remove_dataset, parent)
#                        )

   def evt_select_all_dataset(self, parent):
      # Start the busy routine to indicate to the users something is happening
      parent.busyCursor = 'watch'
      parent.busyWidgets = [parent.pane2.pane( 'EditPaneTop' ), parent.pane2.pane( 'EditPaneBottom' ), parent.pane2.pane( 'EditPaneStatus' ), parent.pane.pane( 'ControlPane' )]
      pub_busy.busyStart( parent )
      try:
         selected_page = parent.main_frame.selected_top_page
         keycolor1 = Pmw.Color.changebrightness(parent, 'aliceblue', 0.6 )
         if selected_page is not None:
            for x in parent.main_frame.top_page_id[selected_page]:
                parent.main_frame.top_page_id[selected_page][x].configure(relief = 'raised', background = keycolor1, image=self.on)

      except:
            pub_busy.busyEnd( parent )  # catch here in order to turn off the busy cursor ganz
            raise
      finally:
           pub_busy.busyEnd( parent )
      #pub_busy.busyEnd( parent )

   def evt_unselect_all_dataset(self, parent):
      # Start the busy routine to indicate to the users something is happening
      parent.busyCursor = 'watch'
      parent.busyWidgets = [parent.pane2.pane( 'EditPaneTop' ), parent.pane2.pane( 'EditPaneBottom' ), parent.pane2.pane( 'EditPaneStatus' ), parent.pane.pane( 'ControlPane' )]
      pub_busy.busyStart( parent )
      try:
         selected_page = parent.main_frame.selected_top_page
         if selected_page is not None:
            for x in parent.main_frame.top_page_id[selected_page]:
                parent.main_frame.top_page_id[selected_page][x].configure(relief = 'raised', background = 'salmon', image=self.off)
      except:
            pub_busy.busyEnd( parent )  # catch here in order to turn off the busy cursor ganz
            raise
      finally:
           pub_busy.busyEnd( parent )
      #pub_busy.busyEnd( parent )

   def warn_On_Removal(self):

       import tkMessageBox
       return tkMessageBox.askokcancel("Removing Datasets WARNING:", 
                                       "Removing the local DB could result in dataset orphans on either the gateway or thredds server. \nCancel to Quit or Ok to Proceed")


       
   def evt_remove_dataset(self, parent):
      from esgcet.publish import pollDatasetPublicationStatus

      # Start the busy routine to indicate to the users something is happening
      parent.busyCursor = 'watch'
      parent.busyWidgets = [parent.pane2.pane( 'EditPaneTop' ), parent.pane2.pane( 'EditPaneBottom' ), parent.pane2.pane( 'EditPaneStatus' ), parent.pane.pane( 'ControlPane' )]
      pub_busy.busyStart( parent )

      datasetNames = []
      GUI_line = {}
      DELETE = 1
      #UNPUBLISH = 2
      NO_OPERATION = 3
      DeleteLocalDB = pub_expand_deletion_control_gui.deletion_widgets.get_CheckBox1() #   DeleteLocalDB 
      DeleteGateway = pub_expand_deletion_control_gui.deletion_widgets.get_CheckBox2() #   DeleteGateway
      DeleteThredds = pub_expand_deletion_control_gui.deletion_widgets.get_CheckBox3() #   DeleteThredds


      selected_page = parent.main_frame.selected_top_page
      if selected_page is not None:
         tab_name = parent.top_notebook.getcurselection()
         for x in parent.main_frame.top_page_id[selected_page]:
            if parent.main_frame.top_page_id[selected_page][x].cget('bg') != 'salmon' and parent.main_frame.top_page_id2[selected_page][x].cget('bg') != 'salmon':
                dset_name = parent.main_frame.top_page_id2[selected_page][x].cget('text')
                               
                #dsetVersionName1 = self.parent.parent.main_frame.top_page_id2v[selected_page][x].cget('text')
                #query_name, dset_version = parseDatasetVersionId(dsetVersionName1)
                """ ganz I am modifying this so that if a user selects a dataset without a version then we delete all versions of that dataset"""
                try:
                    dset_version = parent.main_frame.version_label[selected_page][x].cget('text')
                except:
                    dset_version = -1
                    #print 'Delete all versions'   
                #dset_version = 1
                if (dset_version == 'N/A' or not dset_version):
                    dset_version = -1
                    # continue   # not published, yet
                # Only delete published events
                status = pollDatasetPublicationStatus(dset_name, self.Session)
                if status == 3  or DeleteGateway or DeleteThredds or DeleteLocalDB:
                   #datasetNames.append(generateDatasetVersionId((dset_name, dset_version)))   
                   datasetNames.append([dset_name, dset_version])   # ganz create name/version to delete                 
                else:
                   parent.main_frame.top_page_id[selected_page][x].configure(relief = 'raised', background = 'salmon', image = self.off)
                GUI_line[ dset_name ] = x
            else:
                if parent.main_frame.top_page_id2[selected_page][x].cget('bg') == 'salmon':
                   parent.main_frame.top_page_id[selected_page][x].configure(relief = 'raised', background = 'salmon', image = self.off)
      else:
         warning("%d: No pages generated for selection. Remove is only used to remove datasets from the Publisher." % logging.WARNING)

      # Remove dataset from the gateway, etc.
      if ((DeleteGateway==0 or DeleteThredds==0) and DeleteLocalDB==1) :
          ans = self.warn_On_Removal()
          if (ans == FALSE):
              return
      
      if DeleteGateway==1:
          gatewayOp = DELETE
      else:
          gatewayOp = NO_OPERATION
    # now decide if there is anything to do
      if (gatewayOp==1 or DeleteThredds==1 or DeleteLocalDB==1) :   
          las=False
          thredds = (DeleteThredds==1)              
          deleteDset = (DeleteLocalDB==1)
              
          testProgress = (parent.parent.statusbar.show, 0, 100)
          status_dict = deleteDatasetList(datasetNames, self.Session, gatewayOp, thredds, las, deleteDset, progressCallback=testProgress)


      # Show the published status
      try:
         for x in status_dict.keys():
            status = status_dict[ x ]
            parent.main_frame.status_label[selected_page][GUI_line[x]].configure(text=pub_controls.return_status_text( status) )
      except:
         pass

      pub_busy.busyEnd( parent )
      # ganz refresh [if there were no exceptions] dataset list after deletions 
      parent.pub_buttonexpansion.query_widgets.parent.parent.ntk.evt_refresh_list_of_datasets(selected_page )
     

#----------------------------------------------------------------------------------------
# Create the Login menu and its menu items
#----------------------------------------------------------------------------------------
class create_login_menu:
   """
   Show the Login menu to publish datasets.
   """
   def __init__( self, main_menu, parent, tear_it ):
      L_name = 'Login'
      mnFont=tkFont.Font(parent, family = pub_controls.menu_font_type, size=pub_controls.menu_font_size, weight=pub_controls.mnfont_weight)
      main_menu.addmenu(L_name, 'Publisher Login', side='right', font = mnFont, tearoff = tear_it)

      # Create the "Login" menu item
      self.login = main_menu.addmenuitem(L_name, 'command', 'Open data file',
                         label = 'Login...',
                         font = mnFont,
                         command = pub_controls.Command(self.evt_login, parent)
                        )

   def evt_login(self, parent):

        # Create the username/password dialog.
        self.auth_dialog = Pmw.Dialog(
            parent,
            buttons = ('OK', 'Cancel'),
            defaultbutton = 'OK',
            title = 'Authentication Required',
            command = pub_controls.Command(self.handle_auth_prompt, parent)
            )

        self.auth_dialog.withdraw()

        self.txt_username = Pmw.EntryField(
                            self.auth_dialog.interior(),
                            labelpos = Tkinter.W,
                            label_text = 'Username:',
                            entry_background = 'aliceblue',
                            entry_foreground = 'black',
                            validate = None
                            )
        self.txt_username.pack(side=Tkinter.TOP, padx=5, pady=2)

        self.txt_password = Pmw.EntryField(
                            self.auth_dialog.interior(),
                            labelpos = Tkinter.W,
                            label_text = 'Password:',
                            entry_background = 'aliceblue',
                            entry_foreground = 'black',
                            validate = None,
                            entry_show = '*',
                            )
        self.txt_password.pack(side=Tkinter.TOP, padx=5, pady=2)

        self.auth_dialog.activate(geometry = 'centerscreenalways')

   def handle_auth_prompt(self, parent, result):
        if (result is None or result == 'Cancel'):
            self.auth_dialog.deactivate(result)
        else:
            try:
                self.username = self.txt_username.get()
                self.password = self.txt_password.get()

                self.auth_dialog.deactivate(result)

                parent.password_flg = True

            except Exception, e:
                raise


#----------------------------------------------------------------------------------------
# Create the Help menu and its menu items
#----------------------------------------------------------------------------------------
class create_help_menu:
   """
   Show the help menu -- (e.g., Show Balloons).

   """
   def evt_helpHTML(self, parent):

       widget = helpHTML(self)
     #  widget = LocalHelpHTML(self)


   def evt_help(self, parent):
       title = 'Help DIALOG'
       root = Tkinter.Tk()
       Pmw.initialise(root)
       root.title(title)

       exitButton = Tkinter.Button(root, text = 'Close', command = root.destroy)
       exitButton.pack(side = 'bottom')
       widget = Help(root)
       root.mainloop()

   def __init__( self, main_menu, parent, tear_it):
      H_name = 'Help'


      mnFont=tkFont.Font(parent, family = pub_controls.menu_font_type, size=pub_controls.menu_font_size, weight=pub_controls.mnfont_weight)
      main_menu.addmenu(H_name, 'Publisher Help', side='right', font = mnFont, tearoff = tear_it)
      gui_support.add_balloon_help(main_menu, H_name, font=mnFont)
   #   main_menu.addmenuitem(H_name, 'separator')
      self.help = main_menu.addmenuitem(H_name, 'command', 'Show Help Package',
                         label = 'Help HTML',
                         font = mnFont,
                         command = pub_controls.Command(self.evt_helpHTML, parent))
#      self.help = main_menu.addmenuitem(H_name, 'command', 'Show Help Package',
#                         label = 'Help TEXT',
#                         font = mnFont,
#                         command = pub_controls.Command(self.evt_help, parent))
 

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
