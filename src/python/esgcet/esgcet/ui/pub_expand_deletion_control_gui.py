#!/usr/bin/env python
#
# The Publisher Button Deletion Controls -  pub_expand_deletion_control_gui module
#
###############################################################################
#                                                                             #
# Module:       pub_expand_deletion_control_gui module                        #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Publisher button deletion control expansion that is found on  #
#               the left side of GUI. When a button is selected, it expand to #
#               show additional dataset deletion controls.                    #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFileDialog, tkFont
import os, string
import pub_editorviewer
import pub_controls
import thread
import logging
import traceback

from pub_controls import font_weight
from esgcet.messaging import debug, info, warning, error, critical, exception

class deletion_widgets:
    """
    Generate the deletion control widgets seen on the left when "Dataset Deletion" is selected.
    """
    def __init__(self, parent):
      self.parent = parent
      self.Session = self.parent.parent.Session

      #----------------------------------------------------------------------------------------
      # Begin the creation of the button controls
      #----------------------------------------------------------------------------------------
      glFont=tkFont.Font(self.parent.parent, family = pub_controls.button_group_font_type, size=pub_controls.button_group_font_size, weight=font_weight)

      # Create and pack the LabeledWidgets to "Select All" datasets
#      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type,  size=pub_controls.label_button_font_size, weight=font_weight)

      # Create and pack the LabeledWidgets to "Select All" datasets
#      lw_start1 = Pmw.LabeledWidget(self.parent.control_frame5,
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
#      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type,  size=pub_controls.label_button_font_size, weight=font_weight)

#      lw_start2 = Pmw.LabeledWidget(self.parent.control_frame5,
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

      # Create and pack the LabeledWidgets to "Remove" selected datasets
      bnFont=tkFont.Font(self.parent.parent, family = pub_controls.label_button_font_type,  size=pub_controls.label_button_font_size, weight=font_weight)

      lw_start3 = Pmw.LabeledWidget(self.parent.control_frame5,
                    labelpos = 'w',
                    label_font = bnFont,
                    label_text = 'Dataset deletion: ')
      lw_start3.component('hull').configure(relief='sunken', borderwidth=2)
      lw_start3.pack(side='top', expand = 1, fill = 'both', padx=10, pady=10)
      cw_start = Tkinter.Button(lw_start3.interior(),
                    text='Remove',
                    font = bnFont,
                    background = "lightblue",
                    command = pub_controls.Command( self.evt_remove_selected_dataset ))
      cw_start.pack(padx=10, pady=10, expand='yes', fill='both')

#      Pmw.alignlabels( (lw_start1, lw_start2, lw_start3) )
#      Pmw.alignlabels( (lw_start3) )

      #----------------------------------------------------------------------------------------
      # End the creation of the button controls
      #----------------------------------------------------------------------------------------

    #----------------------------------------------------------------------------------------
    # Button events to Select, Unselect, and Remove datasets
    #----------------------------------------------------------------------------------------
    def evt_dataset_select_all( self ):
       self.parent.parent.menu.Dataset.evt_select_all_dataset( self.parent.parent )

    def evt_dataset_unselect_all( self ):
       self.parent.parent.menu.Dataset.evt_unselect_all_dataset( self.parent.parent )

    def evt_remove_selected_dataset( self ):
       self.parent.parent.menu.Dataset.evt_remove_dataset( self.parent.parent )


#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
