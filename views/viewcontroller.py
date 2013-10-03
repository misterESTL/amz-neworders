# Created on May 31, 2013
# @author: Tom Eaton
#
# This is the Tk frontend for new orders from key accounts.  Orders are 
# converted from incoming format into Everest Advanced Edition 5.0 compatible
# CSV header and data files.

import os
import Tkinter as tk
import tkFileDialog

class Application(tk.Frame):
    '''The Tk GUI interface for converting new orders to Everest formatted \
    CSV files.'''

    def __init__(self, title, description, ftypes, master=None):
        """ Create the base window for the application. """
        self.title = title
        self.description = description
        self.ftypes = ftypes

        tk.Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.master.minsize(500, 290)
        self.master.maxsize(500, 290)
        self.master.title(self.title)


    def createWidgets(self):
        """ Generate widgets """
        # Input file widgets
        self.inLabel = tk.Label(self, text='New Order File:')
        self.inLabel.grid(row=0, column=0)
        self.inEntry = tk.Entry(self, width=70)
        self.inEntry.grid(row=2, column=0, rowspan=2)
        self.inEntry.insert(0, '')

        self.inBrowse = tk.Button(self, text='...', width=3, 
                                  command=self.inFileBrowse)
        self.inBrowse.grid(row=2, column=1)

        # Output file widgets
        self.outLabel = tk.Label(self, text='Output File Path:')
        self.outLabel.grid(row=4, column=0)
        self.outEntry = tk.Entry(self, width=70)
        self.outEntry.grid(row=5, column=0, rowspan=2)
        self.outEntry.insert(0, 'C:\\Documents and Settings\\tom\\Desktop')

        self.outBrowse = tk.Button(self, text='...', width=3, 
                                   command=self.outPathBrowse)
        self.outBrowse.grid(row=5, column=1)

        self.convertButton = tk.Button(self, text='Convert', width=30, 
                                       command=self.checkInput)
        self.convertButton.grid(row=7, column=0, rowspan=2, padx=5, pady=2)

        # Output text box
        self.outText = tk.Text(self, height=10, width=60)
        self.outText.grid(row=9, column=0, columnspan=2, padx=5, pady=5)
        self.writeText(self.description)


    def inFileBrowse(self):
        """ Use the askopenfilename tk dialog to get input file. """
        self.inFile = tkFileDialog.askopenfilename(filetypes=self.ftypes)
        if self.inFile:
            self.inFile = self.inFile.replace('/', '\\')
            self.inEntry.delete(0, tk.END)
            self.inEntry.insert(0, self.inFile)


    def outPathBrowse(self):
        """ Use the askdirectory tk dialog to get output path. """
        self.outPath = tkFileDialog.askdirectory()
        if self.outPath:
            self.outPath = self.outPath.replace('/', '\\')
            self.outEntry.delete(0, tk.END)
            self.outEntry.insert(0, self.outPath)


    def writeText(self, str):
        """ Write to the text widget. """
        # Rewrite to support *args
        self.outText.configure(state='normal')
        self.outText.insert('end', str + '\n')
        self.outText.configure(state='disabled')


    def clearText(self):
        """ Clear the text widget. """
        self.outText.configure(state='normal')
        self.outText.delete(1.0, tk.END)
        self.outText.configure(state='disabled')


    def checkInput(self):
        """ Check for valid input file and output path. """
        if os.path.isdir(self.outEntry.get()) & \
                         os.path.isfile(self.inEntry.get()):
            self.clearText()
            paths = [self.inEntry.get(), self.outEntry.get()]
            self.convert(paths)

        elif os.path.isdir(self.outEntry.get()):
            self.clearText()
            self.writeText('Error: Invalid file!')
        elif os.path.isfile(self.inEntry.get()):
            self.clearText()
            self.writeText('Error: Invalid directory!')
        else:
            self.clearText()
            self.writeText('Error: Invalid file and directory!')

            
    def convert(self, paths):
        """ Initiate conversion. """
        self.clearText()
        self.writeText('Starting Conversion.')
        self.writeText('--------------------')

        procOrder = model.ConvertOrder(paths)

        self.writeText(procOrder.statusText)
        self.writeText('--------------------')
        self.writeText('Complete.')
        

app = Application(model.title, model.description, model.filetypes)
app.mainloop()
