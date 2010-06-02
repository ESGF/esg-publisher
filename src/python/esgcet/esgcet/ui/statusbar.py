#!/usr/bin/env python
#
# The ESG-CET Publisher Graphical User Interface  - statusbar module
#
###############################################################################
#                                                                             #
# Module:       tk_publisher module                                           #
#                                                                             #
# Copyright:    "See file Legal.htm for copyright information."               #
#                                                                             #
# Authors:      PCMDI Software Team                                           #
#               Lawrence Livermore National Laboratory:                       #
#                                                                             #
# Description:  Display the Publisher's Graphical User Interface status bar.  #
#                                                                             #
###############################################################################
#

import Pmw, Tkinter, tkFont
import pub_controls

class Statusbar(Pmw.MegaWidget):
    """ Megawidget containing a scale and an indicator.
    """
    def __init__(self, parent = None, **kw):

        optiondefs = (
            ('color','red',None),
            ('bg','white',None),
            ('value',25.,None),
            ('margins',(5,5,2,2),None),
            ('xcounter',50,None),
            ('ycounter',90,None),
            ('textcounter','%5.2f %%',None),
            ('oncounter',True,None),
            )
        self.defineoptions(kw, optiondefs)

        #-------------------------------------------------------------------------
        # Initialise base class (after defining options)
        #-------------------------------------------------------------------------
        Pmw.MegaWidget.__init__(self, parent)

        txtFont = tkFont.Font(parent, family = pub_controls.tab_font_type, size=pub_controls.tab_font_size)

        # Create the components.
        interior = self.interior()

        self.label = self.createcomponent('label',
                                          (),None,
                                          Tkinter.Label,
                                          (interior,),
                                          text="Status",
                                          font= txtFont,
                                     )
        self.label.pack(side='left')
        self.canvas = self.createcomponent('canvas',
                                      (),None,
                                      Tkinter.Canvas,
                                      (interior,),
                                      )
        self.canvas.pack(side='left')
        self.canvas.configure(relief='sunken', borderwidth=2)

        self.initialiseoptions()
        self.bar = self.canvas.create_rectangle(0,0,0,0)
        self.text = self.canvas.create_text(0,0,font= txtFont)
        self.update()

    #-------------------------------------------------------------------------
    # Show the value in the middle of the status bar region
    #-------------------------------------------------------------------------
    def show(self,value):
         self['value']=value
         self.update()
         self.update_idletasks()

    #-------------------------------------------------------------------------
    # Update the status bar so that the user can see the status of the process
    #-------------------------------------------------------------------------
    def update(self,**kw):

        bg=self['bg']
        self.interior().configure(bg=bg)
        self.label.configure(bg=bg)
        self.canvas.configure(bg=bg)

        ig = self.interior().winfo_geometry()
        lg = self.label.winfo_geometry()
        while ig == 'None' or lg == 'None':
           ig = self.interior().winfo_geometry()
           lg = self.label.winfo_geometry()
        ig=ig.split('x')
        lg=lg.split('x')

        iw = float(ig[0])
        ih = float(ig[1].split('+')[0])

        lw = float(lg[0])
        lh = float(lg[1].split('+')[0])

        cw = iw-lw
        ch = ih

        self.canvas['width']=str(cw)
        self.canvas['height']=str(ch)

        w1 = cw*self['margins'][0]/100.
        w2 = cw*self['margins'][1]/100.
        h1 = cw*self['margins'][2]/100.
        h2 = cw*self['margins'][3]/100.

        self.canvas.coords(self.bar,w1,h1,w1+(cw-w2-w1)*self['value']/100.,ch-h2)
        self.canvas.itemconfig(self.bar,fill=self['color'])
        self.canvas.coords(self.text,self['xcounter']/100.*cw,(1.-self['ycounter']/100.)*ch)
        if self['oncounter']:
            try:
                txt = self['textcounter']%self['value']
            except:
                txt = self['textcounter']
        else:
            txt=''
        self.canvas.itemconfig(self.text,text=txt)

