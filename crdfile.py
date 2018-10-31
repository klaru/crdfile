#! python3
# -*- coding: utf-8 -*-

#  based on crdextractor.py from Sébastien Béchet 2014 
#  and cardreader.py from Christian Ziemski 2015

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
        card_bytes = f.read() 
    
        try:
            self.signature = card_bytes[0:3]
            if self.signature != b'MGC':
                print('No other file types except MGC are supported')
            self.quantity = int.from_bytes(card_bytes[3:5], sys.byteorder)
            index_start = 5
            index_entry_len = 52
            index_len = self.quantity * index_entry_len
            value_start = index_start + index_len + 1
            index = card_bytes[index_start:value_start]
        
            for i in range(self.quantity):
                index_entry = index[i * index_entry_len:(i+1) * index_entry_len]
                # Null bytes, reserved for future.
                assert index_entry[0:6] == b'\x00\x00\x00\x00\x00\x00'
                # Absolute position of card data in file (32 bits)
                card_pos = int.from_bytes(index_entry[6:10], sys.byteorder)  
                index_text = index_entry[11:51]                                  # Index line text, null terminated
                index_text = index_text[0:index_text.find(b'\00')]
                index_text = index_text.decode(encoding='latin1')
                assert index_entry[51] == 0                                      # Null byte, indicates end of entry  
                self.entries[index_text] = card_pos    
                lob = int.from_bytes(card_bytes[card_pos:card_pos+2], sys.byteorder)
                if lob != 0:
                    print('Graphic support not implemented')                
                else:
                    value_len = int.from_bytes(card_bytes[card_pos+2:card_pos+4], sys.byteorder)
                    value = card_bytes[card_pos+4:card_pos+4 + value_len + 1]
                    value = value.decode(encoding='latin1')
                    value = value.replace('\r\n', '\n')
                    self.entries[index_text] = value
        finally:
            f.close()
    
    def getvalue(self, key):
        entries = OrderedDict(self.entries.items())
        text = entries[key] + '\n'
        return text
        
    def keytoText(self):
        entries = OrderedDict(self.entries.items())
        text = ''
        for key, value in entries.items():
            text += key + '\n'
        return text
        
    def show_card(self):
        window = Toplevel()
        key = scrolledtext.get(SEL_FIRST, SEL_LAST)    
        window.title(key)
        text = Text(window, bg = 'khaki')
        text.insert(INSERT, crd.getvalue(key)) 
        text.pack()    
    
    def save_file(self):
        print('Save File is not implemented yet')    
        
    def add_card(self):
        print('Add Card is not implemented yet')    

    def delete_card(self):
        print('Delete Card is not implemented yet')            

if __name__ == '__main__':
    tout = {}
    if len(sys.argv) < 2:
        print('Usage : ', sys.argv[0], ' filename.crd')
    else:
        winkey = Tk()
        winkey.title(sys.argv[1])  
        crd = Crd()
        button1 = Button(winkey, text = 'Select', command = crd.show_card, bg = 'cyan')
        button2 = Button(winkey, text = 'Save File', command = crd.save_file)
        button3 = Button(winkey, text = 'Quit', command = winkey.destroy, bg= 'red')
        button4 = Button(winkey, text = 'Delete Card', command = crd.delete_card)    
        button5 = Button(winkey, text = 'Add Card', command = crd.add_card)        
        button1.pack(anchor='nw', side='left')
        button2.pack(anchor='nw', side='left')
        button3.pack(anchor='ne', side='right')
        button4.pack(anchor='ne', side='right')
        button5.pack(anchor='ne')
        
        scrolledtext = ScrolledText(winkey, width = 40, height = 45, bg = 'beige')         
        
        crd.open(sys.argv[1])
        tout.update(crd.entries)
        scrolledtext.insert(INSERT, crd.keytoText())
        scrolledtext.pack()        

        winkey.mainloop()