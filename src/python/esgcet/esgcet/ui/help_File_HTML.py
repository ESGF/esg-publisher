# To change this template, choose Tools | Templates
# and open the template in the editor.


import os
import webbrowser

class LocalHelpHTML:
 def __init__(self, parent):

    result = os.path.abspath(".")

    path = 'file://'
    path += result
 #   path += '//help.html'
    path += '//PublisherGUI-1.html'
 #   print path
    webbrowser.open_new(path)