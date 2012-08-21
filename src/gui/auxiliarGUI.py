#-*-coding:utf-8-*-
import json
import time
import Tkinter as tk
import tkFileDialog as tkdialog
import tkMessageBox as tkmessage

import zmq

from inputDialog import InputDialogMulti
from connection import getIp


class Build(object):
	def __init__(self, master):
		self.frmConnect = tk.Frame(master, borderwidth=2, relief=tk.GROOVE)
		self.buildAssistantsOpt(self.frmConnect)
		self.frmConnect.pack(fill=tk.X, expand=True)
		
		self.frmConfig = tk.Frame(master, borderwidth=2, relief=tk.GROOVE)
		self.buildLoadConfiguration(self.frmConfig)
		self.frmConfig.pack(fill=tk.X, expand=True)
		
		self.frmLog = tk.Frame(master, borderwidth=2, relief=tk.GROOVE)
		self.buildLog(self.frmLog)
		self.frmLog.pack(fill=tk.X, expand=True)
		
		self.frmControl = tk.Frame(master, borderwidth=2, relief=tk.GROOVE)
		self.buildControl(self.frmControl)
		self.frmControl.pack(fill=tk.X, expand=True)
				
	def buildAssistantsOpt(self, master):
		self.lblMainIp = tk.Label(master, text="Qual o ip?")
#		self.lblAssistants.config()
		self.lblMainIp.grid(row=1, column=0, sticky=tk.E, padx=2)
		
		self.strMainIp = tk.StringVar()
		self.entMainIp = tk.Entry(master)		
		self.entMainIp.config(width=16, justify=tk.CENTER) 
		self.entMainIp.config(textvariable=self.strMainIp)
		self.entMainIp.grid(row=1, column=1, sticky=tk.W, padx=2)	
		self.strMainIp.set("127.0.0.1")	

		self.lblMainPort = tk.Label(master, text="Qual a porta?")
#		self.lblAssistants.config()
		self.lblMainPort.grid(row=1, column=2, sticky=tk.E, padx=2)
		
		self.strMainPort = tk.StringVar()
		self.entMainPort = tk.Entry(master)
		self.entMainPort.config(width=5, justify=tk.CENTER) 
		self.entMainPort.config(textvariable=self.strMainPort)
		self.entMainPort.grid(row=1, column=3, sticky=tk.W, padx=2)	
		self.strMainPort.set("7000")

		self.btnAssitants = tk.Button(master, text="Conectar")
#		self.btnAssitants.config()
		self.btnAssitants.grid(row=1, column=4, sticky=tk.W, padx=2)
				
	def buildLoadConfiguration(self, master):
		self.btnLoadConf = tk.Button(master, text="Carregar Configuração...")
#		self.btnLoadConf.grid(row=0, column=0, sticky=tk.E)
		self.btnLoadConf.pack(anchor=tk.W)
		
		self.txtConfig = tk.Text(master)
		self.txtConfig.config(height=10, yscrollcommand=True)
		self.txtConfig.pack(side=tk.BOTTOM)
		
	def buildLog(self, master):
		self.lblLog = tk.Label(master, text="log: ")
		self.lblLog.pack(anchor=tk.W)
#		self.lblLog.config(state=tk.DISABLED)

		self.txtLog = tk.Text(master)
		self.txtLog.config(height=10, yscrollcommand=True, bg='#000000', fg='#fff')
		self.txtLog.pack()
		
	def buildControl(self, master):
		self.btnStart = tk.Button(master, text="Start")
#		self.btnStart.config(state=tk.DISABLED)
		self.btnStart.grid(row=0, column=1, sticky=tk.E, padx=2, pady=2)
		
		self.btnStop = tk.Button(master, text="Stop")
#		self.btnStop.config(state=tk.DISABLED)
		self.btnStop.grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)
		
		self.btnRestart = tk.Button(master, text="Restart")
#		self.btnRestart.config(state=tk.DISABLED)
		self.btnRestart.grid(row=0, column=3, sticky=tk.E, padx=2, pady=2)
		
		self.btnExit = tk.Button(master, text="Exit")
#		self.btnExit.config(state=tk.DISABLED)
		self.btnExit.grid(row=0, column=4, sticky=tk.E, padx=2, pady=2)		
		
		
class Actions(Build):
	def __init__(self, master):
		super(Actions, self).__init__(master)
		
	def connect(self, event):
#		info = InputDialogMulti(self.master, event, "Qual o ip?", "Qual a porta?")
#		self.master.wait_window(info.top)
		contexto = zmq.Context()
		socketEnvio = contexto.socket(zmq.PUSH)
		socketResposta = contexto.socket(zmq.PULL)
		ip, porta = self.strMainIp.get(), self.strMainPort.get()
		socketResposta.bind("tcp://" + getIp() + ":" + porta)
		print "Tentando conexão com {}:{}".format(ip, porta)
		socketEnvio.connect("tcp://" + ip + ":" + porta)
		print "Conexão estabelecida, enviando mensagem "
		socketEnvio.send("olá sou o " + getIp())
		print "Aguardando resposta..."
		tentativas = 0
		while tentativas < 1000: 
			msg = None
			try:
				msg = socketResposta.recv(zmq.NOBLOCK)
			except zmq.ZMQError:
				tentativas += 1
			if msg != None:
				print 'msg'
				self.writeLog("recebi " + msg + '\n')
				break
			time.sleep(0.01)
		print 'quitei'
		del socketResposta
		del socketEnvio
		print 'mesmo'
		return 
			
	def setCentralized(self, event):
		self.centralized = True
				
	def setDistributed(self, event):
		self.centralized = False
		
	def loadConfiguration(self):
		filename = tkdialog.askopenfilename()
		
		print filename
		
	def writeLog(self, texto):	
		self.txtLog.insert(tk.END, texto)
		self.master.update_idletasks()		
		
	def quit(self):
		self.master.destroy()
	

class Events(Actions):
	def __init__(self, master):
		super(Events, self).__init__( master)
#		self.optCentralized.bind("<Button-1>", self.clickCentralized)
#		self.optCentralized.bind("<Return>", self.clickCentralized)
#		self.optCentralized.bind("<space>", self.clickCentralized)
#		self.optDistributed.bind("<Return>", self.clickDistributed)
#		self.optDistributed.bind("<Button-1>", self.clickDistributed)
#		self.optDistributed.bind("<space>", self.clickDistributed)
		self.btnAssitants.bind("<Button-1>", self.clickConnect)
		self.btnAssitants.bind("<Return>", self.clickConnect)
		self.btnAssitants.bind("<space>", self.clickConnect)
		self.btnLoadConf.config(command=self.loadConfiguration)
		self.btnExit.bind("<Button-1>", self.clickExit)
		self.btnExit.bind("<space>", self.clickExit)
		self.btnExit.bind("<Return>", self.clickExit)
		
	def clickConnect(self, event):
		self.connect(event)
				
	def clickCentralized(self, event):
		self.lblAssistants.config(state=tk.DISABLED)
		self.entNumAssistants.config(state=tk.DISABLED)
		self.btnAssitants.config(state=tk.DISABLED)
#		self.btnAssitants.lower(self.frmMode)
		self.setCentralized(event)
				
	def clickDistributed(self, event):
		self.lblAssistants.config(state=tk.NORMAL)
		self.entNumAssistants.config(state=tk.NORMAL)
		self.btnAssitants.config(state=tk.NORMAL)
#		self.btnAssitants.lift(self.frmMode)
		self.setDistributed(event)		

	def clickExit(self, event):
		self.quit()
		

class ZephyrusAuxiliary(Events):
	def __init__(self):
		self.master = tk.Tk()
		self.master.title("Zephyrus Auxiliary")
		self.master.resizable(False, False)
		super(ZephyrusAuxiliary, self).__init__(self.master)
		self.txtLog.insert(tk.END, "*" * 24)		
		self.txtLog.insert(tk.END, " ZEPHYRUS - version 0.1 - 2012 ")
		self.txtLog.insert(tk.END, "*" * 24 + '\n')
		
		tk.mainloop()
		
