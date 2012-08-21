from Tkinter import *

class InputDialog(object):
	def __init__(self, master, event, mensagem):
		self.top = Toplevel(master)
		self.event = event
#		self.top.transient(master)
		
		Label(self.top, text=mensagem).pack(side=LEFT)
		self.entry = Entry(self.top)
		self.entry.pack(padx=5, pady=5, side=LEFT)
		self.value = 0

		b = Button(self.top, text="ok", command=self.ok)
		b.pack(pady=5, side=LEFT)
		
		self.entry.bind("<space>", self.ok)
		b.bind("Return>", self.ok)

	def ok(self, event=None):
		self.value = self.entry.get()
		self.event.valor = self.entry.get()
		self.top.destroy()
	
	def get(self):
		return self.value
	
	def die(self):
		print 'morri!!!'
		self.top.destroy()
		

class InputDialogMulti(object):
	def __init__(self, master, event, *mensagens):
		self.top = Toplevel(master)
		self.top.transient(master)
		
		self.entries = []
		self.values  = None
		print len(mensagens), mensagens
		for i in range(len(mensagens)):
			Label(self.top, text=mensagens[i]).grid(row=i, column=0)
			self.entries.append(Entry(self.top))
			self.entries[i].grid(padx=5, pady=5, row=i, column=1)

		b = Button(self.top, text="ok", command=self.ok)
		b.grid(pady=5, row=len(mensagens)+1, columns=1)
		self.entries[-1].bind("<space>", self.ok)
		b.bind("Return>", self.ok)

	def ok(self, event=None):
		self.value = [k.get() for k in self.entries]
		self.top.destroy()
	
	def get(self):
		return self.value	

	def die(self):
		self.top.destroy()
