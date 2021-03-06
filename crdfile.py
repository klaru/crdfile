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
from tkinter import *
from tkinter.scrolledtext import *

global filename, value_new, value_len_new

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

    # after the window has been destroyed, we can't access the entry widget,
    # tbut we _can_ access the associated variable
    value = var.get()
    return value   
 
def create_file(filename):
    f = open(filename, 'rb')        
    card_bytes = f.read()  
    CARD_BYTES_NEW = bytearray(len(card_bytes))
    try:
        quantity = int.from_bytes(card_bytes[3:5], sys.byteorder)    
        CARD_BYTES_NEW[0:3] = b'MGC'                                                                        # NEW
        CARD_BYTES_NEW[3:5] = quantity.to_bytes(2, sys.byteorder)                                    # NEW
        index_start = 5
        index_entry_len = 52
        index_len = quantity * index_entry_len
        value_start = index_start + index_len + 1
        index = card_bytes[0:value_start]
        
        for i in range(0, quantity):
            index_pos = index_start + i * index_entry_len
            index_entry = index[index_pos:index_pos + index_entry_len]    
            # Null bytes, reserved for future.
            CARD_BYTES_NEW[index_pos:index_pos+6] = b'\x00\x00\x00\x00\x00\x00'                             # NEW
            # Absolute position of card data in file (32 bits) 
            card_pos = int.from_bytes(index_entry[6:10], sys.byteorder)           
            CARD_BYTES_NEW[index_pos+6:index_pos+10] = card_pos.to_bytes(4, sys.byteorder)                  # NEW   
            CARD_BYTES_NEW[index_pos+10:index_pos+11] = b'\x00'                                             # NEW                
            index_text = index_entry[11:51]                               # Index line text, null terminated
            index_text = index_text[0:41]
            index_text = index_text.decode(encoding='latin1')
            CARD_BYTES_NEW[index_pos+11:index_pos+51] =  bytes(index_text[0:41], encoding='latin1')         # NEW
            CARD_BYTES_NEW[index_pos+51:index_pos+52] = b'\x00'                                             # NEW , Null byte, indicates end of entry   
            CARD_BYTES_NEW[card_pos:card_pos+2] = b'\x00\x00'                                               # NEW, lob
            value_len = int.from_bytes(card_bytes[card_pos+2:card_pos+4], sys.byteorder)                    
            CARD_BYTES_NEW[card_pos+2:card_pos+4] = value_len.to_bytes(2, sys.byteorder)                    # NEW)
            value = card_bytes[card_pos+4:card_pos+4 + value_len + 1]
            value = value.decode(encoding='latin1')
            CARD_BYTES_NEW[card_pos+4:card_pos+4 + value_len + 1] = bytes(value[0:value_len + 1], encoding='latin1')         # NEW
    finally:
        f.close()          
        return CARD_BYTES_NEW    

        
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
        f = open(filename, 'rb')
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
            index = card_bytes[0:value_start]
        
            for i in range(0, self.quantity):
                index_entry = index[index_start + i * index_entry_len:index_start + (i+1) * index_entry_len]
                # Null bytes, reserved for future.
                assert index_entry[0:6] == b'\x00\x00\x00\x00\x00\x00'
                # Absolute position of card data in file (32 bits)
                card_pos = int.from_bytes(index_entry[6:10], sys.byteorder)  
                assert index_entry[10:11] == b'\x00'
                index_text = index_entry[11:51]                                  # Index line text, null terminated
                index_text = index_text[0:index_text.find(b'\00')]
                index_text = index_text.decode(encoding='latin1')
                assert index_entry[51:52] == b'\x00'                                      # Null byte, indicates end of entry   
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
    
    def save_file(self):
        tempfile = filename + '_tmp'
        ftemp = open(tempfile, 'wb')
        CARD_BYTES_NEW = create_file(filename)       
        ftemp.write(CARD_BYTES_NEW) 
        ftemp.close()
        os.replace(tempfile, filename)
        
    def save_as(self):
        tempfile = gui_input(300, 'Enter file name: ')
        ftemp = open(tempfile, 'wb')
        CARD_BYTES_NEW = create_file(filename)       
        ftemp.write(CARD_BYTES_NEW)
        ftemp.close()             
         
    def add_card(self):

        def get_text():
            value_new = text.get("1.0","end-1c")    
            value_len_new = len(value_new)
            CARD_BYTES_NEW[card_pos_new+2:card_pos_new+4] = value_len_new.to_bytes(2, sys.byteorder)
            CARD_BYTES_NEW[card_pos_new+4:card_pos_new+4 + value_len_new + 1] = bytes(value_new[0:value_len_new + 1], encoding='latin1') 
            ftemp.write(CARD_BYTES_NEW) 
            ftemp.close()     
            os.rename(tempfile, filename)            
            window.destroy()
            
        tempfile = filename + '_tmp'
        bakfile = filename + '_bak'
        ftemp = open(tempfile, 'wb')
        f = open(filename, 'rb')
        card_bytes = f.read()  
        index_entry_len = 52
        CARD_BYTES_NEW = bytearray(len(card_bytes) + index_entry_len)
        try:
            quantity = int.from_bytes(card_bytes[3:5], sys.byteorder)    
            number_of_cards = quantity + 1
            CARD_BYTES_NEW[0:3] = b'MGC'                                                                        # NEW
            CARD_BYTES_NEW[3:5] = number_of_cards.to_bytes(2, sys.byteorder)                                    # NEW
            index_start = 5
            index_len = quantity * index_entry_len
            value_start = index_start + index_len + 1
            index = card_bytes[0:value_start]
        
            for i in range(0, quantity):
                index_pos = index_start + i * index_entry_len
                index_entry = index[index_pos:index_pos + index_entry_len]    
                # Null bytes, reserved for future.
                CARD_BYTES_NEW[index_pos:index_pos+6] = b'\x00\x00\x00\x00\x00\x00'                             # NEW
                # Absolute position of card data in file (32 bits) 
                card_pos = int.from_bytes(index_entry[6:10], sys.byteorder)
                card_pos_new = card_pos  + index_entry_len
                CARD_BYTES_NEW[index_pos+6:index_pos+10] = card_pos_new.to_bytes(4, sys.byteorder)              # NEW   
                CARD_BYTES_NEW[index_pos+10:index_pos+11] = b'\x00'                                             # NEW                
                index_text = index_entry[11:51]                               # Index line text, null terminated
                index_text = index_text[0:41]
                index_text = index_text.decode(encoding='latin1')
                CARD_BYTES_NEW[index_pos+11:index_pos+51] =  bytes(index_text[0:41], encoding='latin1')         # NEW
                CARD_BYTES_NEW[index_pos+51:index_pos+52] = b'\x00'                                             # NEW , Null byte, indicates end of entry             
                CARD_BYTES_NEW[card_pos_new:card_pos_new+2] = b'\x00\x00'                                       # NEW, lob
                value_len = int.from_bytes(card_bytes[card_pos+2:card_pos+4], sys.byteorder)
                CARD_BYTES_NEW[card_pos_new+2:card_pos_new+4] = value_len.to_bytes(2, sys.byteorder)            # NEW
                value = card_bytes[card_pos+4:card_pos+4 + value_len + 1]
                value = value.decode(encoding='latin1')
                CARD_BYTES_NEW[card_pos_new+4:card_pos_new+4 + value_len + 1] = bytes(value[0:value_len + 1],encoding='latin1') # NEW    
            index_pos = index_pos + index_entry_len
            # Null bytes, reserved for future.
            CARD_BYTES_NEW[index_pos:index_pos+6] = b'\x00\x00\x00\x00\x00\x00'                                 # NEW
            # Absolute position of card data in file (32 bits) 
            card_pos_new = card_pos_new + value_len + 4
            CARD_BYTES_NEW[index_pos+6:index_pos+10] = card_pos_new.to_bytes(4, sys.byteorder)                  # NEW   
            CARD_BYTES_NEW[index_pos+10:index_pos+11] = b'\x00'                                                 # NEW    
            new_index_bytes = bytearray(40)            
            new_index_text = gui_input(600, 'Enter card name: ')
            new_index_bytes[0:len(new_index_text)] = bytes(new_index_text[0:len(new_index_text)], encoding='latin1')
            CARD_BYTES_NEW[index_pos+11:index_pos+51] =  new_index_bytes[0:41]                                  # NEW
            CARD_BYTES_NEW[index_pos+51:index_pos+52] = b'\x00'                                                 # NEW , Null byte, indicates end of entry   
            CARD_BYTES_NEW[card_pos_new:card_pos_new+2] = b'\x00\x00'                                           # NEW, lob              
            scrolledtext.insert(INSERT, new_index_text)   
            window = Toplevel()
            window.title(new_index_text)  
            text = Text(window, bg = 'beige')
            button = Button(window, text='Add card text', command=get_text)              
            text.pack()  
            button.pack()            
        finally:
            f.close()
            os.replace(filename, bakfile)                                
        
    def delete_card(self):
        print('Delete Card is not implemented yet')      
        
    def getvalue(self, index_text):
        text = self.entries[index_text] + '\n'
        return text
        
    def keytoText(self):
        text = ''
        for index_text in (self.entries):
            text += index_text + '\n'
        return text
        
    def show_card(self):
        window = Toplevel()
        index_text = scrolledtext.get(SEL_FIRST, SEL_LAST)    
        window.title(index_text)
        text = Text(window, bg = 'khaki')
        text.insert(INSERT, crd.getvalue(index_text)) 
        text.pack()    
    
if __name__ == '__main__':
    tout = {}
    if len(sys.argv) < 2:
        print('Usage : ', sys.argv[0], ' filename.crd')
    else:
        winkey = Tk()
        filename = sys.argv[1]
        winkey.title(filename)  
        crd = Crd()
        button1 = Button(winkey, text = 'Select', command = crd.show_card, bg = 'cyan')
        button2 = Button(winkey, text = 'Save File', command = crd.save_file)
        button3 = Button(winkey, text = 'Save As', command = crd.save_as)       
        button4 = Button(winkey, text = 'Quit', command = winkey.destroy, bg= 'red')
        button5 = Button(winkey, text = 'Delete Card', command = crd.delete_card)    
        button6 = Button(winkey, text = 'Add Card', command = crd.add_card)        
        button1.pack(anchor='nw', side='left')
        button2.pack(anchor='nw', side='left')
        button3.pack(anchor='nw', side='left')
        button4.pack(anchor='ne', side='right')
        button5.pack(anchor='ne', side='right')
        button6.pack(anchor='ne')
        
        scrolledtext = ScrolledText(winkey, width = 40, height = 45, bg = 'beige')         
        
        crd.open(filename)
        tout.update(crd.entries)
        scrolledtext.insert(INSERT, crd.keytoText())
        scrolledtext.pack()        

        winkey.mainloop()