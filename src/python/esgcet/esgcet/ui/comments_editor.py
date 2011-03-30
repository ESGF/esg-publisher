#!/usr/bin/env python
import os
import tempfile
import Tkinter, Pmw, tkFileDialog, tkFont

title = 'Editor DIALOG'
class EDITOR:
    def __init__(self, parent):
      self.parent = parent
    
    def edit(self):
# Create a temp file
        editor = os.environ.get('EDITOR')
        if editor is None:
            #editor = "gedit"
            # ======== Select a file for opening:
            print "Please set your favorite editor in the EDITOR environmental variable for future use." 
            try:
                dialog_icon = tkFileDialog.Open(master=self.parent.control_frame2,title = 'Editor Selection')
                editor=dialog_icon.show(initialdir="/")   #os.getcwd())
            except:
                print excpt
  
  # finally if all else fails....
            if editor == None:
                editor = "/usr/local/bin/emacs"
                
        tmp = tempfile.mktemp()

# Edit a temp file

        command = '%s %s'%(editor, tmp)
        errno = os.system(command)
        if errno!=0:
            print 'Invalid command:', command

# Read temp file contents
        if not os.path.exists(tmp):
            print 'No comment file created, editor %s , please reset EDITOR env variable to a valid graphical editor' % editor
            lines = []
        else:
            f = open(tmp, "r")
            
            lines = f.readlines()
            #print 'comments recorded %s ', lines
            f.close()
          
    # Remove temp file
            os.remove(tmp)
        return lines
######################################################################
