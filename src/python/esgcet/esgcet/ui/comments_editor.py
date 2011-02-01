#!/usr/bin/env python
import os
import tempfile

title = 'Editor DIALOG'
class EDITOR:
   
    def edit(self):
# Create a temp file
        editor = os.environ.get('EDITOR')
        if editor is None:
            #editor = "gedit"
            editor = "/usr/local/bin/emacs"
            #print 'No editor defined.'
            #sys.exit(0)
        tmp = tempfile.mktemp()
        print 'Editing', tmp

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

# testing, can remove later
if __name__ == '__main__':

    myeditor = EDITOR()
    lines = myeditor.edit()

    for x in lines:
       print x
 

