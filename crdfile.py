#! python3
# -*- coding: utf-8 -*-

#  based on crdextractor from Sébastien Béchet 2014

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License Version 3 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

import sys, os
from collections import OrderedDict
from tkinter import *
from tkinter.scrolledtext import *

def gui_input(width, prompt):

    root = Toplevel()
    w = width # width for the Tk root
    h = 65 # height for the Tk root

    # get screen width and height
    ws = root.winfo_screenwidth() # width of the screen
    hs = root.winfo_screenheight() # height of the screen

    # calculate x and y coordinates for the Tk root window
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)

    # set the dimensions of the screen 
    # and where it is placed
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))


    # this will contain the entered string, and will
    # still exist after the window is destroyed
    var = StringVar()

    # create the GUI
    label = Label(root, text=prompt)
    entry = Entry(root, textvariable=var)
    label.pack(side="left", padx=(20, 0), pady=20)
    entry.pack(side="right", fill="x", padx=(0, 20), pady=20, expand=True)
    entry.focus_force()

    # Let the user press the return key to destroy the gui 
    entry.bind("<Return>", lambda event: root.destroy())

    # this will block until the window is destroyed
    root.wait_window()

    # after the window has been destroyed, we can't access
    # the entry widget, but we _can_ access the associated
    # variable
    value = var.get()
    return value           
    
# Only MGC at this time
class Crd(object):
    filename = ""
    signature = "MGC"
    quantity = 0
    entries = {}

    def __init__(self):
        self.filename = ""
        self.signature = "MGC"
        self.quantity = 0
        self.entries = {}

    def open(self, filename):
        self.filename = filename
        f = open(filename, "rb")
        try:
            self.signature = f.read(3)
            if self.signature != b'MGC':
                return False
            self.quantity = int.from_bytes(f.read(2), byteorder='little')
            for i in range(self.quantity):
                f.seek(6,1)
                pos = int.from_bytes(f.read(4), byteorder='little')
                f.seek(1,1)
                text = f.read(40)
                text = text.decode('cp1252')
                text = text.split('\0',1)[0]
                self.entries[text] = pos
                f.seek(1,1)
            for key, seek in self.entries.items():
                f.seek(seek,0)
                lob = int.from_bytes(f.read(2), byteorder='little')
                if lob == 0:
                    lot = int.from_bytes(f.read(2), byteorder='little')
                    value = f.read(lot)
                    value = value.decode('cp1252')
                    value = value.replace('\r\n', '\n')
                    self.entries[key] = value
                else:
                    print('erreur lob=', lob,' pour un seek=',seek)
        finally:
            f.close()
    
    def getvalue(self, key):
        entries2 = OrderedDict(self.entries.items())
        text = entries2[key] + '\n'
        return text
        
    def keytoText(self):
        entries2 = OrderedDict(self.entries.items())
        text = ''
        for key, value in entries2.items():
            text += key + '\n'
        return text
        
    def show_card(self):
        window = Toplevel()
        key = scrolledtext.get(SEL_FIRST, SEL_LAST)    
        window.title(key)
        text = Text(window, bg = 'khaki')
        text.insert(INSERT, crd.getvalue(key)) 
        text.pack()           

if __name__ == '__main__':
    tout = {}
    if len(sys.argv) < 2:
        print('Usage : ', sys.argv[0], ' filename.crd')
    else:
        winkey = Tk()
        winkey.title(sys.argv[1])  
        scrolledtext = ScrolledText(winkey, width = 40, height = 45, bg = 'beige')         
        
        nb = len(sys.argv) - 1
        for i in range(nb):
            crd = Crd()
            crd.open(sys.argv[i + 1])
            tout.update(crd.entries)
        crd = Crd()
        crd.entries = tout
        scrolledtext.insert(INSERT, crd.keytoText())
        scrolledtext.pack()
        button = Button(winkey, text = 'Select', command = crd.show_card)
        button.pack()

        winkey.mainloop()