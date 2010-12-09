#!/usr/bin/env python
#
# The Publisher controls and miscellaneous functions -  pub_control module
#
###############################################################################
#                                                                             #
# Module:       pub_control module                                            #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Publisher GUI controls and miscellaneous functons.            #
#                                                                             #
###############################################################################

import Tkinter
import os, sys, string, types
import pub_busy

#------------------------------------------------------------------------
# Redirect the destination of sys.stderr to the "Error" tab window
#------------------------------------------------------------------------
class standard_err:
    """
    Show all warning, error, debug, critical, and exception messages in the 'Error' tab window located in the bottom right.
    """
    def __init__( self, master ):
        self.parent = master

    def write(self,s):
        self.parent.bottom_notebook.selectpage('Error')
        self.parent.log_error_window.appendtext( s )
        self.parent.log_error_window.yview("moveto", 1)
        self.parent.log_error_window.configure(vscrollmode ='dynamic')

        # Remove the busy mouse
        pub_busy.busyEnd( self.parent.parent )

    def flush(self):
        err = open('/dev/null', 'a+', 0)
        os.dup2(err.fileno(), 2)

#------------------------------------------------------------------------
# Redirect the destination of sys.stdout to the "Output" tab window
#------------------------------------------------------------------------
class standard_out:
    """
    Show all information messages in the 'Output' tab window located in the bottom right.
    """
    def __init__( self, master ):
        self.parent = master

    def write(self,s):
        self.parent.bottom_notebook.selectpage('Output')
        self.parent.log_output_window.appendtext( s )
        self.parent.log_output_window.yview("moveto", 1)
        self.parent.log_output_window.configure(vscrollmode ='dynamic')

    def flush(self):
        out = open('/dev/null', 'a+', 0)
        os.dup2(out.fileno(), 2)

#---------------------------------------------------------------------------------
# Event handling function that will allow the passing of arguments
#---------------------------------------------------------------------------------
class Command:
    """
    Event handling function that will allow the passing of arguments.
    """
    def __init__(self, func, *args, **kw):
      self.func = func
      self.args = args
      self.kw = kw

    def __call__(self, *args, **kw):
      args = self.args + args
      kw.update(self.kw)
      return apply(self.func, args, kw)

#--------------------------------------------------------------------------------
# This is just an ordinary button with special image to remove the page.
# This button is used exclusively to remove pages from the top notebook.
#--------------------------------------------------------------------------------
class MyButton(Tkinter.Button):
    """
    A Tkinter button with the special image to remove tab pages.
    """
    def __init__(self, master=None, cnf={}, **kw):
        from pkg_resources import resource_filename
        remove_gif = resource_filename('esgcet.ui', 'remove.gif')
        photo1 = Tkinter.PhotoImage(file=remove_gif)
        self.__toggle = 0
        #kw['background'] = 'green'
        #kw['activebackground'] = 'red'
        kw['image'] = photo1
        apply(Tkinter.Button.__init__, (self, master, cnf), kw)
        self.image = photo1 # save the image from garbage collection
        
#---------------------------------------------------------------------
# Controls for the GUI fonts: Font.family (Courier, Helvetica, Ariel,
#                             Cambria, Calibri)
#---------------------------------------------------------------------
menu_font_type = 'Helvetica'
menu_font_size = -16

button_font_type = 'Helvetica'
button_font_size = -16

collection_font_type = 'Helvetica'
collection_font_size= -13

button_group_font_type = 'Helvetica'
button_group_font_size = -16

combobox_font_type = 'Helvetica'
combobox_font_size = -14

label_button_font_type = 'Helvetica'
label_button_font_size = -14

text_font_type = 'Helvetica'
text_font_size = -14

tab_font_type = 'Helvetica'
tab_font_size = -14

splash_font_size = -14
font_weight = "normal"
bnfont_weight = "normal"
mnfont_weight = "normal"
#font_weight = "normal"

#---------------------------------------------------------------------
# Controls for the GUI colors
#---------------------------------------------------------------------
query_tab_color = "yellow"

#---------------------------------------------------------------------------------
# List of filetypes to search for in the "File Select" popup dialog window
#---------------------------------------------------------------------------------
filetypes = [
        ("Python and text files", "*.py *.pyw *.txt", "TEXT"),
        ("All text files", "*", "TEXT"),
        ("All files", "*"),
        ]

#---------------------------------------------------------------------------------
# List of filetypes to search for in the "File Select" popup dialog window
#---------------------------------------------------------------------------------
datatypes = [
         ("Search for netCDF files", "*.nc"),
         ("Search for GrADS files", "*.ctl"),
         ("Search for CDMS files", "*.cdms"),
         ("Search for DRS files", "*.dic"),
         ("Search for PP files", "*.pp"),
         ("Search for HDF files", "*.hdf"),
         ("Search for XML files", "*.xml"),
         ("Search for XML files", "*.cdml"),
         ("Search for PSQL files", "*.cdms"),
         ("All files", "*")
         ]

def return_status_text( status ):
    from esgcet.model import eventShortName

    result = eventShortName.get(status, 'Error')
    return result

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
