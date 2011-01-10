#!/usr/bin/env python
#
# The Publisher Button Quality Controls -  pub_expand_quality_control_gui module
#
###############################################################################
#                                                                             #
# Module:       pub_expand_quality_control_gui module                         #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Publisher button quality control expansion that is found on   #
#               the left side of GUI. When a button is selected, it expand to #
#               show additional quality controls.                             #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFileDialog, tkFont
import os, string
import pub_editorviewer
import pub_controls
import pub_busy
import thread
import logging
import traceback

from pub_controls import font_weight
from esgcet.messaging import debug, info, warning, error, critical, exception
from esgcet.publish import parseDatasetVersionId, generateDatasetVersionId
from pkg_resources import resource_filename

on_icon  = resource_filename('esgcet.ui', 'on.gif')
off_icon = resource_filename('esgcet.ui', 'off.gif')


class quality_control_widgets:
    """
    Generate the quality control widgets seen on the left when "Quality Control" is selected.
    """
    def __init__(self, parent):
      self.parent = parent
      self.Session = self.parent.parent.Session

      # Set the arrow icons
      self.on  = Tkinter.PhotoImage(file=on_icon)
      self.off = Tkinter.PhotoImage(file=off_icon)

      #----------------------------------------------------------------------------------------
      # Begin the creation of the button controls
      #----------------------------------------------------------------------------------------
      glFont=tkFont.Font(self.parent.parent, family = pub_controls.button_group_font_type, size=pub_controls.button_group_font_size, weight=font_weight)
      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type,  size=pub_controls.label_button_font_size, weight=font_weight)

      #self.button_controls = Pmw.Group(self.parent.control_frame3,
      #                  tag_text = 'Button Controls',
      #                  tag_font = glFont,
      #                  tagindent = 25)

      # Create and pack the LabeledWidgets to "Select All" datasets
#      lw_start1 = Pmw.LabeledWidget(self.parent.control_frame3,
#                    labelpos = 'w',
#                    label_font = bnFont,
#                    label_text = 'Dataset: ')
#      lw_start1.component('hull').configure(relief='sunken', borderwidth=2)
#      lw_start1.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
#      cw_start = Tkinter.Button(lw_start1.interior(),
#                    text='Select All',
#                    font = bnFont,
#                    background = "aliceblue",
#                    command = pub_controls.Command( self.evt_dataset_select_all ))
#      cw_start.pack(padx=10, pady=10, expand='yes', fill='both')

      # Create and pack the LabeledWidgets to "Unselect All" datasets
#      lw_start2 = Pmw.LabeledWidget(self.parent.control_frame3,
#                    labelpos = 'w',
#                    label_font = bnFont,
#                    label_text = 'Dataset: ')
#      lw_start2.component('hull').configure(relief='sunken', borderwidth=2)
#      lw_start2.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
#      cw_start = Tkinter.Button(lw_start2.interior(),
#                    text='Unselect All',
#                    font = bnFont,
#                    background = "aliceblue",
#                    command = pub_controls.Command( self.evt_dataset_unselect_all ))
#      cw_start.pack(padx=10, pady=10, expand='yes', fill='both')

      # Create and pack the LabeledWidgets to "Publish" datasets
      self.generating_file_list_flg = 0
      lw_start3 = Pmw.LabeledWidget(self.parent.control_frame3,
                    labelpos = 'w',
                    label_font = bnFont,
                    label_text = 'Release data: ')
      lw_start3.component('hull').configure(relief='sunken', borderwidth=2)
      lw_start3.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      cw_start = Tkinter.Button(lw_start3.interior(),
                    text='Publish',
                    font = bnFont,
                    background = "lightblue",
                    command = pub_controls.Command( self.start_harvest, parent ))
      cw_start.pack(padx=10, pady=10, expand='yes', fill='both')

 #     Pmw.alignlabels( (lw_start1, lw_start2, lw_start3) )

      # Create and pack the LabeledWidgets to THREDDS catalog the data
      self.generating_file_list_flg = 0
      lw_catalog = Pmw.LabeledWidget(self.parent.control_frame3,
                    labelpos = 'w',
                    label_text = 'Generate:      ')
      lw_catalog.component('hull').configure(relief='sunken', borderwidth=2)
      cw_catalog = Tkinter.Button(lw_catalog.interior(),
                    text='THREDDS',
                    command = pub_controls.Command( self.catalog_thredds, parent ))
      cw_catalog.pack(padx=10, pady=10, expand='yes', fill='both')

      #self.button_controls.pack(side='top', fill='x', pady=3)
      #----------------------------------------------------------------------------------------
      # End the creation of the button controls
      #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    # Event button to start the extraction process
    #----------------------------------------------------------------------------------------
    def evt_dataset_select_all( self ):
       self.parent.parent.menu.Dataset.evt_select_all_dataset( self.parent.parent )

    def evt_dataset_unselect_all( self ):
       self.parent.parent.menu.Dataset.evt_unselect_all_dataset( self.parent.parent )

    def start_harvest( self, parent ):
        from esgcet.publish import publishDatasetList
        from esgcet.model import Dataset, PUBLISH_FAILED_EVENT, ERROR_LEVEL

        dcolor1 = Pmw.Color.changebrightness(self.parent.parent, 'aliceblue', 0.8 )

        # Make sure the publisher is logged in
       # if not self.parent.parent.password_flg:
       #    self.parent.parent.menu.login_menu.evt_login( self.parent.parent )

        # Start the busy routine to indicate to the users something is happening
        self.parent.parent.busyCursor = 'watch'
        self.parent.parent.busyWidgets = [self.parent.parent.pane2.pane( 'EditPaneTop' ), self.parent.parent.pane2.pane( 'EditPaneBottom' ), self.parent.parent.pane2.pane( 'EditPaneStatus' ), self.parent.parent.pane.pane( 'ControlPane' )]
        pub_busy.busyStart( self.parent.parent )
 
        # Generate the list of datasets to be published
        datasetNames=[]
        GUI_line = {}
        tab_name = self.parent.parent.top_notebook.getcurselection()
        selected_page = self.parent.parent.main_frame.selected_top_page

        if (selected_page is None):
           warning("Must generate a list of datasets to scan before publishing can occur.")
           pub_busy.busyEnd( self.parent.parent )
           return

        for x in self.parent.parent.main_frame.top_page_id[selected_page]:

            if self.parent.parent.main_frame.top_page_id[selected_page][x].cget('bg') != 'salmon' and self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('bg') != 'salmon':
                dset_name = self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('text')
                dsetTuple = parseDatasetVersionId(dset_name)
                datasetNames.append(dsetTuple)
                GUI_line[ dset_name ] = x
            else:
                if self.parent.parent.main_frame.top_page_id2[selected_page][x].cget('bg') == 'salmon':
                   self.parent.parent.main_frame.top_page_id[selected_page][x].configure(relief = 'raised', background = 'salmon', image = self.off)

        # Publish collection of datasets
        testProgress = (self.parent.parent.statusbar.show, 0, 100)
        status_dict = publishDatasetList(datasetNames, self.Session, progressCallback=testProgress)

        # Show the published status
        for x in status_dict.keys():
             status = status_dict[ x ]
             dsetName, versionNo = x
             dsetVersionName = generateDatasetVersionId(x)
             guiLine = GUI_line[dsetVersionName]
            
             self.parent.parent.main_frame.status_label[selected_page][guiLine].configure(text=pub_controls.return_status_text( status) )
             dset = Dataset.lookup(dsetName, self.Session)
             if dset.has_warnings(self.Session):
                 warningLevel = dset.get_max_warning_level(self.Session)
                 if warningLevel>=ERROR_LEVEL:
                     buttonColor = "pink"
                     buttonText = "Error"
                 else:
                     buttonColor = "yellow"
                     buttonText = "Warning"
                 self.parent.parent.main_frame.ok_err[selected_page][guiLine].configure(
                     text = buttonText,
                     bg = buttonColor,
                     relief = 'raised',
                     command = pub_controls.Command( self.parent.parent.pub_buttonexpansion.extraction_widgets.error_extraction_button, dset ) )
             else:
                 self.parent.parent.main_frame.ok_err[selected_page][guiLine].configure(
                     text = 'Ok',
                     bg = dcolor1,
                     highlightcolor = dcolor1,
                     relief = 'sunken',
                     )

        pub_busy.busyEnd( self.parent.parent )

    #----------------------------------------------------------------------------------------
    # Event button to generate THREDDS configuration file
    #----------------------------------------------------------------------------------------
    def catalog_thredds( self, parent ):
        from esgcet.publish import generateThredds
        from tkMessageBox import showerror

        dialog_icon = tkFileDialog.SaveAs(master=self.parent.control_frame2,
                         filetypes=[("THREDDS", "*.thredds", "THREDDS XML"), ("XML", "*.xml", "THREDDS XML")], title = 'File Open Selection')
        dirfilename=dialog_icon.show(initialdir=os.getcwd())
        if len(dirfilename)==0:
            return
        dir = dirfilename[:dirfilename.rfind('/')]
        filename = dirfilename[dirfilename.rfind('/')+1:]
        name = filename[:filename.rfind('.')].strip()
       
        # Check for directory and filename error
        if dirfilename in [(), '']:
           showerror("ESGPublishError", "There was an error in the selected directory and specified filename." )
           return
        if name in [(), '']:
           showerror("ESGPublishError", "There was an error in the specified filename." )
           return
        if os.access(dir, os.W_OK) != True:
           showerror("ESGPublishError", "You do not have write permission for the selected directory." )
           return

        # Generate a THREDDS configuration file
        threddsOutputPath = dirfilename
        threddsOutput = open(threddsOutputPath, "w")
        try:
            selected_page = self.parent.parent.main_frame.selected_top_page
            datasetName = self.parent.parent.datasetName
            generateThredds(datasetName, self.parent.parent.Session, threddsOutput, self.parent.parent.handlerDictionary[datasetName])
        except Exception, inst:
             error(traceback.format_exc())
             showerror("ESGPublishError", inst )
        threddsOutput.close()

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
