#!/usr/bin/env python
#
# The PCMDI Data Browser Busy Cursor -  pub_busy module
#
#################################################################################
#                                                                               #
# Module:       pub_busy module                                                 #
#                                                                               #
# Copyright:    "See file Legal.htm for copyright information."                 #
#                                                                               #
# Authors:      PCMDI Software Team                                             #
#               Lawrence Livermore National Laboratory:                         #
#                                                                               #
# Description:  Indicate to the user that the Publisher GUI is busy with an     #
#               operation.                                                      #
#                                                                               #
#################################################################################

#--------------------------------------------------------------------------------
# Start the busy cursor prompt                                                   
#--------------------------------------------------------------------------------
def busyStart(parent):
   try:
      busyEnd(self, parent) # If an error occurred, then end previous busy
   except:
      pass
   newcursor = parent.busyCursor
   newPreBusyCursors = {}
   for component in parent.busyWidgets:
       newPreBusyCursors[component] = component['cursor']
       component.configure(cursor=newcursor)
       component.update_idletasks()
   parent.preBusyCursors = (newPreBusyCursors, None)

#--------------------------------------------------------------------------------
# End the busy cursor prompt.                                                    
#--------------------------------------------------------------------------------
def busyEnd(parent):
   try:
      if not parent.preBusyCursors:
          return
   except:
      return
   oldPreBusyCursors = parent.preBusyCursors[0]
   parent.preBusyCursors = parent.preBusyCursors[1]
   for component in parent.busyWidgets:
       try:
           component.configure(cursor=oldPreBusyCursors[component])
       except KeyError:
           pass
       component.update_idletasks()
