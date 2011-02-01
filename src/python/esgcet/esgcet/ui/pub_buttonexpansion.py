#!/usr/bin/env python
#
# The Publisher Buttion Expansion Controls -  pub_buttonexpansion module
#
###############################################################################
#                                                                             #
# Module:       pub_buttonexpansion module                                    #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Publisher button expansion that is found on the left side of  #
#               GUI. When a button is selected, it expands to show additional #
#               controls.                                                     #
#                                                                             #
###############################################################################
#
import Tkinter, Pmw, tkFileDialog, tkFont
import os, string
import pub_controls
import pub_expand_dataset_gui
import pub_expand_extraction_gui
import pub_expand_quality_control_gui
import pub_expand_query_gui
import pub_expand_deletion_control_gui

from pkg_resources import resource_filename
blue_right = resource_filename('esgcet.ui', 'blue_right.gif')
blue_down = resource_filename('esgcet.ui', 'blue_down.gif')

#----------------------------------------------------------------------------------------
# Begin the class creation of the publisher control expansion buttons
#----------------------------------------------------------------------------------------
class create_publisher_button_expansion:
   """
   Display the action item expansion buttons located on the left side of the Publisher GUI.
   """
   def __init__( self, root ):

      self.parent = root
      button_parent = root.pane.pane( 'ControlPane' )

      # Set the arrow icons
      self.right = Tkinter.PhotoImage(file=blue_right)
      self.down = Tkinter.PhotoImage(file=blue_down)

      #----------------------------------------------------------------------------------------
      # Create the first control button for "Specify Project and Dataset"
      #----------------------------------------------------------------------------------------
      self.control_toggle1=0
      bxtFont = tkFont.Font(button_parent, family = pub_controls.button_font_type, size=pub_controls.button_font_size, weight=pub_controls.bnfont_weight)
      self.ControlButton1 = Tkinter.Button(button_parent,
                       compound = Tkinter.LEFT,
                       justify = Tkinter.LEFT,
                       anchor = Tkinter.W,
                       image = self.right,
                       text = 'Specify Project and Dataset',
                       font = bxtFont,
                       bg = 'lightblue',
                       command = pub_controls.Command(self.view_controls1, button_parent))
      self.ControlButton1.image = self.right # save the image from garbage collection
      self.ControlButton1.pack(side = 'top', fill = 'x')
      self.parent.balloon.bind(self.ControlButton1, "Specify on-line or off-line work, project, directory or file \ncontaining dataset locations, and filter file search.")
      self.control_frame1 = Tkinter.Frame(button_parent, width=5,height=5)

      # generate the dataset widgets
      self.dataset_widgets = pub_expand_dataset_gui.dataset_widgets( self )
      #----------------------------------------------------------------------------------------
      # End the create first control button for "Specify Project and Dataset"
      #----------------------------------------------------------------------------------------

      #----------------------------------------------------------------------------------------
      # Create the second control button for "Data Extraction"
      #----------------------------------------------------------------------------------------
      self.control_toggle2=0
      self.ControlButton2 = Tkinter.Button(button_parent,
                       compound = Tkinter.LEFT,
                       justify = Tkinter.LEFT,
                       anchor = Tkinter.W,
                       image = self.right,
                       text = 'Data Extraction',
                       font = bxtFont,
                       bg = 'lightblue',
                       command = pub_controls.Command(self.view_controls2, button_parent))
      self.ControlButton2.image = self.right # save the image from garbage collection
      self.ControlButton2.pack(side = 'top', fill = 'x')
      self.parent.balloon.bind(self.ControlButton2, "Extract and scan datasets, then add file information to the database.")
      self.control_frame2 = Tkinter.Frame(button_parent, width=5,height=5)

      # generate the extraction widgets
      self.extraction_widgets = pub_expand_extraction_gui.dataset_widgets( self )
      #----------------------------------------------------------------------------------------
      # End the create second control button for "Data Extraction"
      #----------------------------------------------------------------------------------------
	    
      #----------------------------------------------------------------------------------------
      # Create the third control button for "Quality Control"
      #----------------------------------------------------------------------------------------
      self.control_toggle3=0
      self.ControlButton3 = Tkinter.Button(button_parent,
                       compound = Tkinter.LEFT,
                       justify = Tkinter.LEFT,
                       anchor = Tkinter.W,
                       image = self.right,
                       text = 'Data Publication',
                       font = bxtFont,
                       state = 'disabled',
                       bg = 'lightblue',
                       command = pub_controls.Command(self.view_controls3, button_parent))
      self.ControlButton3.image = self.right # save the image from garbage collection
      self.ControlButton3.pack(side = 'top', fill = 'x')
      self.parent.balloon.bind(self.ControlButton3, 'Publish dataset(s):\nThe "Data Publication" button is only selectable after successful\n"Data Extraction" or "Dataset Query" operations.')
      self.control_frame3 = Tkinter.Frame(button_parent, width=5,height=5)

      # generate the publication control widgets
      self.quality_control_widgets = pub_expand_quality_control_gui.quality_control_widgets( self )
      #----------------------------------------------------------------------------------------
      # End the create third control button for "Quality Control"
      #----------------------------------------------------------------------------------------
	    
      #----------------------------------------------------------------------------------------
      # Create the fourth control button for "Dataset Query"
      #----------------------------------------------------------------------------------------
      self.control_toggle4=0
      self.ControlButton4 = Tkinter.Button(button_parent,
                       compound = Tkinter.LEFT,
                       justify = Tkinter.LEFT,
                       anchor = Tkinter.W,
                       image = self.right,
                       text = 'Dataset Query',
                       font = bxtFont,
                       bg = 'lightblue',
                       command = pub_controls.Command(self.view_controls4, button_parent))
      self.ControlButton4.image = self.right # save the image from garbage collection
      self.ControlButton4.pack(side = 'top', fill = 'x')
      self.parent.balloon.bind(self.ControlButton4, "Query datasets given project information.")
      self.control_frame4 = Tkinter.Frame(button_parent, width=5,height=5)

      # generate the query control widgets
      self.query_widgets = pub_expand_query_gui.query_widgets( self )
      #----------------------------------------------------------------------------------------
      # End the create the fourth control button for "Dataset Query"
      #----------------------------------------------------------------------------------------

      #----------------------------------------------------------------------------------------
      # Create the fifth control button for "Dataset Deletion"
      #----------------------------------------------------------------------------------------
      self.control_toggle5=0
      self.ControlButton5 = Tkinter.Button(button_parent,
                       compound = Tkinter.LEFT,
                       justify = Tkinter.LEFT,
                       anchor = Tkinter.W,
                       image = self.right,
                       text = 'Dataset Deletion',
                       font = bxtFont,
                       bg = 'lightblue',
                       command = pub_controls.Command(self.view_controls5, button_parent))
      self.ControlButton5.image = self.right # save the image from garbage collection
      self.ControlButton5.pack(side = 'top', fill = 'x')
      self.parent.balloon.bind(self.ControlButton5, "Remove datasets from the system.")
      self.control_frame5 = Tkinter.Frame(button_parent, width=5,height=5)

      # generate the deletion control widgets (was query_widgets BUG?)
      self.deletion_widgets = pub_expand_deletion_control_gui.deletion_widgets( self )
      #----------------------------------------------------------------------------------------
      # End the create the fifth control button for "Dataset Deletion"
      #----------------------------------------------------------------------------------------


   #----------------------------------------------------------------------------------------
   # Expand and contract the view controls for "Specify Datasets"
   #----------------------------------------------------------------------------------------
   def view_controls1(self, parent):
      if self.control_toggle1 == 0:
         self.control_frame1.pack(side='top', after=self.ControlButton1, fill='x')
         self.control_toggle1 = 1
         self.ControlButton1.configure(image = self.down )

         self.control_frame2.pack_forget()
         self.control_toggle2 = 0
         self.ControlButton2.configure(image = self.right )
         self.control_frame3.pack_forget()
         self.control_toggle3 = 0
         self.ControlButton3.configure(image = self.right )
         self.control_frame4.pack_forget()
         self.control_toggle4 = 0
         self.ControlButton4.configure(image = self.right )
         self.control_frame5.pack_forget()
         self.control_toggle5 = 0
         self.ControlButton5.configure(image = self.right )
      else:
         self.control_frame1.pack_forget()
         self.control_toggle1 = 0
         self.ControlButton1.configure(image = self.right )

   #----------------------------------------------------------------------------------------
   # Expand and contract the view controls for "Data Extraction"
   #----------------------------------------------------------------------------------------
   def view_controls2(self, parent):
      if self.control_toggle2 == 0:
         self.control_frame2.pack(side='top', after=self.ControlButton2, fill='x')
         self.control_toggle2 = 1
         self.ControlButton2.configure(image = self.down )

         self.control_frame1.pack_forget()
         self.control_toggle1 = 0
         self.ControlButton1.configure(image = self.right )
         self.control_frame3.pack_forget()
         self.control_toggle3 = 0
         self.ControlButton3.configure(image = self.right )
         self.control_frame4.pack_forget()
         self.control_toggle4 = 0
         self.ControlButton4.configure(image = self.right )
         self.control_frame5.pack_forget()
         self.control_toggle5 = 0
         self.ControlButton5.configure(image = self.right )
      else:
         self.control_frame2.pack_forget()
         self.control_toggle2 = 0
         self.ControlButton2.configure(image = self.right )

   #----------------------------------------------------------------------------------------
   # Expand and contract the view controls for "Quality Control"
   #----------------------------------------------------------------------------------------
   def view_controls3(self, parent):
      if self.control_toggle3 == 0:
         self.control_frame3.pack(side='top', after=self.ControlButton3, fill='x')
         self.control_toggle3 = 1
         self.ControlButton3.configure(image = self.down )

         self.control_frame1.pack_forget()
         self.control_toggle1 = 0
         self.ControlButton1.configure(image = self.right )
         self.control_frame2.pack_forget()
         self.control_toggle2 = 0
         self.ControlButton2.configure(image = self.right )
         self.control_frame4.pack_forget()
         self.control_toggle4 = 0
         self.ControlButton4.configure(image = self.right )
         self.control_frame5.pack_forget()
         self.control_toggle5 = 0
         self.ControlButton5.configure(image = self.right )
      else:
         self.control_frame3.pack_forget()
         self.control_toggle3 = 0
         self.ControlButton3.configure(image = self.right )

   #----------------------------------------------------------------------------------------
   # Expand and contract the view controls for "Metadata Query, Update, and Delete"
   #----------------------------------------------------------------------------------------
   def view_controls4(self, parent):
      if self.control_toggle4 == 0:
         self.control_frame4.pack(side='top', after=self.ControlButton4, fill='x')
         self.control_toggle4 = 1
         self.ControlButton4.configure(image = self.down )

         self.control_frame1.pack_forget()
         self.control_toggle1 = 0
         self.ControlButton1.configure(image = self.right )
         self.control_frame2.pack_forget()
         self.control_toggle2 = 0
         self.ControlButton2.configure(image = self.right )
         self.control_frame3.pack_forget()
         self.control_toggle3 = 0
         self.ControlButton3.configure(image = self.right )
         self.control_frame5.pack_forget()
         self.control_toggle5 = 0
         self.ControlButton5.configure(image = self.right )
      else:
         self.control_frame4.pack_forget()
         self.control_toggle4 = 0
         self.ControlButton4.configure(image = self.right )

   #----------------------------------------------------------------------------------------
   # Expand and contract the view controls for "Metadata Query, Update, and Delete"
   #----------------------------------------------------------------------------------------
   def view_controls5(self, parent):
      if self.control_toggle5 == 0:
         self.control_frame5.pack(side='top', after=self.ControlButton5, fill='x')
         self.control_toggle5 = 1
         self.ControlButton5.configure(image = self.down )

         self.control_frame1.pack_forget()
         self.control_toggle1 = 0
         self.ControlButton1.configure(image = self.right )
         self.control_frame2.pack_forget()
         self.control_toggle2 = 0
         self.ControlButton2.configure(image = self.right )
         self.control_frame3.pack_forget()
         self.control_toggle3 = 0
         self.ControlButton3.configure(image = self.right )
         self.control_frame4.pack_forget()
         self.control_toggle4 = 0
         self.ControlButton4.configure(image = self.right )
      else:
         self.control_frame5.pack_forget()
         self.control_toggle5 = 0
         self.ControlButton5.configure(image = self.right )

#----------------------------------------------------------------------------------------
# End the class creation of the publisher control expansion buttons
#----------------------------------------------------------------------------------------

#---------------------------------------------------------------------
# End of File
#---------------------------------------------------------------------
