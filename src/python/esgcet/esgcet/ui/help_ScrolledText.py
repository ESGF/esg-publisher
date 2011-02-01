import os.path


title = 'Help DIALOG'

import sys
import os

import Tkinter
import Pmw


class Help:
    def __init__(self, parent):

        fixedFont = Pmw.logicalfont('Fixed')
       	self.st = Pmw.ScrolledText(parent,
		labelpos = 'n',
		label_text='Help for ESG PUBLISHER GUI',

		usehullsize = 1,
		hull_width = 1000,
		hull_height = 600,
		text_wrap='none',
		text_font = fixedFont,

		text_padx = 4,
		text_pady = 4,
	)
       # sys.path[:0] = ['.']
        
        result = os.path.abspath(".")
       # print result

        self.st.importfile(os.path.join(result,'help.txt'))
      #  self.st.importfile(os.path.join(result,'ESG_PUB_GUI_HELP.txt'))
	self.st.pack(padx = 5, pady = 5, fill = 'both', expand = 1)

        # disable ability to modify
	self.st.configure(
            text_state = 'disabled',

        )

######################################################################

# testing, can remove later
if __name__ == '__main__':
    root = Tkinter.Tk()
    Pmw.initialise(root)
    root.title(title)

    exitButton = Tkinter.Button(root, text = 'Close', command = root.destroy)
    exitButton.pack(side = 'bottom')
    widget = Help(root)
    root.mainloop()


