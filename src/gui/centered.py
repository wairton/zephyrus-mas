import tkinter as tk

def startgame():
    pass

mw = tk.Tk()
mw.title('The Game')

back=tk.Frame(master=mw, width=500, height=500, bg='black')
# back.pack_propagate(0)
back.pack(fill=tk.BOTH, expand=1) #Adapts the size to the window

#Here I had the label

go = tk.Button(master=back, text='Start Game', command=startgame, bg='#111', fg='red')
go.pack()
close = tk.Button(master=back, text='Quit', command=mw.destroy, bg='#111', fg='red')
close.pack()
info = tk.Label(master=back, text='Made by me!', bg='red', fg='black')
info.pack()

back.grid(row=1, column=1)
mw.grid_rowconfigure(0, weight=1)
mw.grid_rowconfigure(2, weight=1)
mw.grid_columnconfigure(0, weight=1)
mw.grid_columnconfigure(2, weight=1)

mw.mainloop()
