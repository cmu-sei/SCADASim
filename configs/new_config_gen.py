# SCADA Simulator
#
# Copyright 2018 Carnegie Mellon University. All Rights Reserved.
#
# NO WARRANTY. THIS CARNEGIE MELLON UNIVERSITY AND SOFTWARE ENGINEERING INSTITUTE MATERIAL IS FURNISHED ON AN "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY KIND, EITHER EXPRESSED OR IMPLIED, AS TO ANY MATTER INCLUDING, BUT NOT LIMITED TO, WARRANTY OF FITNESS FOR PURPOSE OR MERCHANTABILITY, EXCLUSIVITY, OR RESULTS OBTAINED FROM USE OF THE MATERIAL. CARNEGIE MELLON UNIVERSITY DOES NOT MAKE ANY WARRANTY OF ANY KIND WITH RESPECT TO FREEDOM FROM PATENT, TRADEMARK, OR COPYRIGHT INFRINGEMENT.
#
# Released under a MIT (SEI)-style license, please see license.txt or contact permission@sei.cmu.edu for full terms.
#
# [DISTRIBUTION STATEMENT A] This material has been approved for public release and unlimited distribution.  Please see Copyright notice for non-US Government use and distribution.
# This Software includes and/or makes use of the following Third-Party Software subject to its own license:
# 1. Packery (https://packery.metafizzy.co/license.html) Copyright 2018 metafizzy.
# 2. Bootstrap (https://getbootstrap.com/docs/4.0/about/license/) Copyright 2011-2018  Twitter, Inc. and Bootstrap Authors.
# 3. JIT/Spacetree (https://philogb.github.io/jit/demos.html) Copyright 2013 Sencha Labs.
# 4. html5shiv (https://github.com/aFarkas/html5shiv/blob/master/MIT%20and%20GPL2%20licenses.md) Copyright 2014 Alexander Farkas.
# 5. jquery (https://jquery.org/license/) Copyright 2018 jquery foundation.
# 6. CanvasJS (https://canvasjs.com/license/) Copyright 2018 fenopix.
# 7. Respond.js (https://github.com/scottjehl/Respond/blob/master/LICENSE-MIT) Copyright 2012 Scott Jehl.
# 8. Datatables (https://datatables.net/license/) Copyright 2007 SpryMedia.
# 9. jquery-bridget (https://github.com/desandro/jquery-bridget) Copyright 2018 David DeSandro.
# 10. Draggabilly (https://draggabilly.desandro.com/) Copyright 2018 David DeSandro.
# 11. Business Casual Bootstrap Theme (https://startbootstrap.com/template-overviews/business-casual/) Copyright 2013 Blackrock Digital LLC.
# 12. Glyphicons Fonts (https://www.glyphicons.com/license/) Copyright 2010 - 2018 GLYPHICONS.
# 13. Bootstrap Toggle (http://www.bootstraptoggle.com/) Copyright 2011-2014 Min Hur, The New York Times.
# DM18-1351
#

import tkinter as tk

class ScrolledFrame(tk.Frame):

    def __init__(self, parent, vertical=True, horizontal=False):
        super().__init__(parent)

        # canvas for inner frame
        self._canvas = tk.Canvas(self)
        self._canvas.grid(row=0, column=0, sticky='news') # changed

        # create right scrollbar and connect to canvas Y
        self._vertical_bar = tk.Scrollbar(self, orient='vertical', command=self._canvas.yview)
        if vertical:
            self._vertical_bar.grid(row=0, column=1, sticky='ns')
        self._canvas.configure(yscrollcommand=self._vertical_bar.set)

        # create bottom scrollbar and connect to canvas X
        self._horizontal_bar = tk.Scrollbar(self, orient='horizontal', command=self._canvas.xview)
        if horizontal:
            self._horizontal_bar.grid(row=1, column=0, sticky='we')
        self._canvas.configure(xscrollcommand=self._horizontal_bar.set)

        # inner frame for widgets
        self.inner = tk.Frame(self._canvas)
        self._window = self._canvas.create_window((0, 0), window=self.inner, anchor='nw')

        # autoresize inner frame
        self.columnconfigure(0, weight=1) # changed
        self.rowconfigure(0, weight=1) # changed

        # resize when configure changed
        self.inner.bind('<Configure>', self.resize)
        self._canvas.bind('<Configure>', self.frame_width)

    def frame_width(self, event):
        # resize inner frame to canvas size
        canvas_width = event.width
        self._canvas.itemconfig(self._window, width = canvas_width)

    def resize(self, event=None): 
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

class PLC:

    def __init__(self, parent, num):
        self.parent = parent
        self.title = "PLC " + str(num + 1)
        self.create_widgets()

    def create_widgets(self):
        self.labelframe = tk.LabelFrame(self.parent, text=self.title)
        self.labelframe.pack(fill="both", expand=True)

        self.label = tk.Label(self.labelframe, text="properties")
        self.label.pack(expand=True, fill='both')

        self.entry = tk.Entry(self.labelframe)
        self.entry.pack()

#Creates PLC devices
def build_plc(window, num_of_plc):
    destroy_plc(window)
    for i in range(int(num_of_plc)):
        PLC(window.inner, i)

#Destroys PLC devices
def destroy_plc(window):
    children = window.inner.winfo_children() 
    for child in children:
        if str(type(child)) == "<class 'tkinter.LabelFrame'>":
            child.destroy()

def main():
    #Create main tkinter frame
    root = tk.Tk()
    root.title("Config Generator")
    #root.geometry("400x300")

    #Create new ScrolledFrame
    window = ScrolledFrame(root)
    window.pack(expand=True, fill='both')

    #User specifies number of plc devices
    label = tk.Label(window.inner, text="Number of PLC devices?")
    label.pack(expand=True, fill='both')

    num_of_plc = tk.Entry(window.inner)
    num_of_plc.pack(fill=tk.X, padx=5)

    submit_btn = tk.Button(window.inner, text="Submit", command=lambda: build_plc(window, num_of_plc.get()))
    submit_btn.pack()

    reset_btn = tk.Button(window.inner, text="Reset", command=lambda: destroy_plc(window))
    reset_btn.pack()

    #start GUI
    root.mainloop()

if __name__ == '__main__':
    main()
