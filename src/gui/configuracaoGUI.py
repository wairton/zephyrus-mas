#-*-coding:utf-8-*-
#This work is under LGPL license, see the LICENSE.LGPL file for further details.

import json
import os
import Tkinter as tk
import tkFileDialog as tkdialog
import tkMessageBox as tkmessage

import zmq

#from inputDialog import InputDialog
from connection import getIp
from foo import prepareConfiguration

common_config = {
	'bg' : '#e6e6e6'
}

class Build(object):
	def __init__(self, master):
		self.frmDirectory = tk.Frame(master, borderwidth=2, **common_config)
		self.buildDirectoryConfig(self.frmDirectory)
		self.frmDirectory.pack(fill=tk.X, expand=True)

		self.frmPort = tk.Frame(master, borderwidth=2, **common_config)
		self.buildPortConfig(self.frmPort)
		self.frmPort.pack(fill=tk.X, expand=True)

		self.frmAgents = tk.Frame(master, borderwidth=2, **common_config)
#		self.buildModes(self.frmMode)
		self.buildAgentsConfig(self.frmAgents)
		self.frmAgents.pack(fill=tk.X, expand=True)

#		self.frmMode1 = tk.Frame(master, borderwidth=2, relief=tk.GROOVE)
		self.frmMode1 = tk.Frame(master, borderwidth=2, **common_config)
#		self.buildModes(self.frmMode)
		self.buildAssistantsOpt2(self.frmMode1)
		self.frmMode1.pack(fill=tk.X, expand=True)
		
#		self.frmLog = tk.Frame(master, borderwidth=2, relief=tk.GROOVE)
#		self.buildLog(self.frmLog)
#		self.frmLog.pack(fill=tk.X, expand=True)
		
#		self.frmControl = tk.Frame(master, borderwidth=2, relief=tk.GROOVE)
		self.frmControl = tk.Frame(master, borderwidth=2, **common_config)
		self.buildControl(self.frmControl)
		self.frmControl.pack(fill=tk.X, expand=True)
		
	
	def buildDirectoryConfig(self, master):
		self.lblBaseDirectory = tk.Label(master, text="diretório base: ", **common_config)
		self.lblBaseDirectory.grid(row=0, column=0, sticky=tk.E, padx=2)
		
		self.strBaseDirectory = tk.StringVar()
		self.entBaseDirectory = tk.Entry(master)
		self.entBaseDirectory.config(width=50, justify=tk.CENTER) 
		self.entBaseDirectory.config(textvariable=self.strBaseDirectory)
		self.entBaseDirectory.grid(row=0, column=1, sticky=tk.W, padx=2)	
		self.strBaseDirectory.set('/'.join(os.getcwd().split('/')[:-1] + ['examples']))
		
		self.btnBaseDirectory = tk.Button(master, text="...", **common_config)
		self.btnBaseDirectory.grid(row=0, column=2, padx=2)
		
	def buildPortConfig(self, master):
		self.lblPorts = tk.Label(master, text="portas->", **common_config)
		self.lblPorts.grid(row=0, column=0, sticky=tk.E, padx=2)

		tk.Label(master, text="       ", **common_config).grid(row=0, column=1, sticky=tk.E, padx=2)
		
		self.lblAgentsPorts = tk.Label(master, text="agentes:", **common_config)
		self.lblAgentsPorts.grid(row=0, column=2, sticky=tk.E, padx=2)
		
		self.strAgentsPorts = tk.StringVar()
		self.entAgentsPorts = tk.Entry(master)
		self.entAgentsPorts.config(width=5, justify=tk.CENTER) 
		self.entAgentsPorts.config(textvariable=self.strAgentsPorts)
		self.entAgentsPorts.grid(row=0, column=3, sticky=tk.W, padx=2)	
		
		tk.Label(master, text="monitor:", **common_config).grid(row=0, column=4, sticky=tk.E, padx=2)
		
		self.strMonitorPort = tk.StringVar()
		self.entMonitorPort = tk.Entry(master)
		self.entMonitorPort.config(width=5, justify=tk.CENTER) 
		self.entMonitorPort.config(textvariable=self.strMonitorPort)
		self.entMonitorPort.grid(row=0, column=5, sticky=tk.W, padx=2)
		self.strMonitorPort.set("")
		
		tk.Label(master, text="estratégia:", **common_config).grid(row=0, column=6, sticky=tk.E, padx=2)
		
		self.strStrategyPort = tk.StringVar()
		self.entStrategyPort = tk.Entry(master)		
		self.entStrategyPort.config(width=5, justify=tk.CENTER) 
		self.entStrategyPort.config(textvariable=self.strStrategyPort)
		self.entStrategyPort.grid(row=0, column=7, sticky=tk.W, padx=2)	
		self.strStrategyPort.set("")

	def buildAgentsConfig(self, master):
		self.btnAddAgent = tk.Button(master, text="Adicionar Agente", **common_config)
		self.btnAddAgent.grid(row=0, column=0)
		self.btnRemAgent = tk.Button(master, text="Remover Agente", **common_config)
		self.btnRemAgent.grid(row=0, column=1)
		self.nAgents = 0
		self.agents = {}
		for i in ['lbl', 'ent', 'str']:
			self.agents[i] = []
#		self.addAgent(master)
	
	def addAgent(self, master):
		lbl = tk.Label(master, text="executar agente (" + str(self.nAgents + 1) + "):", **common_config)
		self.agents['lbl'].append(lbl)
		self.agents['lbl'][-1].grid(row=self.nAgents + 1, column=0, sticky=tk.E, padx=2)
		
		self.agents['str'].append(tk.StringVar())
		self.agents['ent'].append(tk.Entry(master))
		self.agents['ent'][-1].config(width=50, justify=tk.CENTER) 
		self.agents['ent'][-1].config(textvariable=self.agents['str'][-1])
		self.agents['ent'][-1].grid(row=self.nAgents + 1, column=1, sticky=tk.W, padx=2)
		self.agents['str'][-1].set("<MANUAL>")
		
		self.nAgents += 1
#		print 'agents: ', self.agents, self.nAgents
		
	def remAgent(self, master):
#		print self.nAgents
		if self.nAgents < 1:
			return False
		self.agents['lbl'][-1].grid_forget()
		self.agents['lbl'].pop()
#		self.agents['lbl'][-1].grid(row=self.actualLine, column=0, sticky=tk.E, padx=2)
#		self.agents['str'][-1].grid_forget()
		self.agents['str'].pop()
		self.agents['ent'][-1].grid_forget()
		self.agents['ent'].pop()		
		
		self.nAgents -= 1	

	def buildAssistantsOpt2(self, master):
		self.lblLaunchEnviron = tk.Label(master, text="executar ambiente: ", **common_config)
		self.lblLaunchEnviron.grid(row=0, column=0, sticky=tk.E, padx=2)
		self.strLaunchEnviron = tk.StringVar()
		self.entLaunchEnviron = tk.Entry(master)		
		self.entLaunchEnviron.config(width=50, justify=tk.CENTER) 
		self.entLaunchEnviron.config(textvariable=self.strLaunchEnviron)
		self.entLaunchEnviron.grid(row=0, column=1, sticky=tk.W, padx=2)	
		self.strLaunchEnviron.set("<MANUAL>")

		self.lblLaunchTester = tk.Label(master, text="executar testador: ", **common_config)
		self.lblLaunchTester.grid(row=1, column=0, sticky=tk.E, padx=2)
		self.strLaunchTester = tk.StringVar()
		self.entLaunchTester = tk.Entry(master)
		self.entLaunchTester.config(width=50, justify=tk.CENTER) 
		self.entLaunchTester.config(textvariable=self.strLaunchTester)
		self.entLaunchTester.grid(row=1, column=1, sticky=tk.W, padx=2)
		self.strLaunchTester.set("<MANUAL>")

		self.lblLaunchMonitor = tk.Label(master, text="executar monitor: ", **common_config)
		self.lblLaunchMonitor.grid(row=2, column=0, sticky=tk.E, padx=2)
		self.strLaunchMonitor = tk.StringVar()
		self.entLaunchMonitor = tk.Entry(master)
		self.entLaunchMonitor.config(width=50, justify=tk.CENTER) 
		self.entLaunchMonitor.config(textvariable=self.strLaunchMonitor)
		self.entLaunchMonitor.grid(row=2, column=1, sticky=tk.W, padx=2)	
		self.strLaunchMonitor.set("<MANUAL>")

		self.lblLaunchStrategy = tk.Label(master, text="executar estratégia: ", **common_config)
		self.lblLaunchStrategy.grid(row=3, column=0, sticky=tk.E, padx=2)
		self.strLaunchStrategy = tk.StringVar()
		self.entLaunchStrategy = tk.Entry(master)
		self.entLaunchStrategy.config(width=50, justify=tk.CENTER) 
		self.entLaunchStrategy.config(textvariable=self.strLaunchStrategy)
		self.entLaunchStrategy.grid(row=3, column=1, sticky=tk.W, padx=2)	
		self.strLaunchStrategy.set("<MANUAL>")


	def buildLoadConfiguration(self, master):
		self.btnLoadConf = tk.Button(master, text="Carregar Configuração...", **common_config)
#		self.btnLoadConf.grid(row=0, column=0, sticky=tk.E)
		self.btnLoadConf.grid(row=0, column=0)

		self.btnLoadScript = tk.Button(master, text="Carregar Roteiro...", **common_config)
#		self.btnLoadScript.grid(row=0, column=1,sticky=tk.E)
		self.btnLoadScript.grid(row=0, column=1)
		
		self.txtConfig = tk.Text(master)
		self.txtConfig.config(height=10, yscrollcommand=True, **common_config)
		self.txtConfig.grid(row=1, columnspan=2)
		
	def buildLog(self, master):
		self.lblLog = tk.Label(master, text="log: ", **common_config)
		self.lblLog.pack(anchor=tk.W)
#		self.lblLog.config(state=tk.DISABLED)

		self.txtLog = tk.Text(master)
		self.txtLog.config(height=10, yscrollcommand=True, bg='#000000', fg='#fff')
		self.txtLog.pack()
		
	def buildControl(self, master):
		self.btnNew = tk.Button(master, text="Novo", **common_config)
#		self.btnStart.config(state=tk.DISABLED)
		self.btnNew.grid(row=0, column=1, sticky=tk.E, padx=2, pady=2)
		
		self.btnOpen = tk.Button(master, text="Abrir", **common_config)
#		self.btnStop.config(state=tk.DISABLED)
		self.btnOpen.grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)
		
		self.btnSave = tk.Button(master, text="Salvar", **common_config)
#		self.btnRestart.config(state=tk.DISABLED)
		self.btnSave.grid(row=0, column=3, sticky=tk.E, padx=2, pady=2)
		
		self.btnExit = tk.Button(master, text="Sair", **common_config)
#		self.btnExit.config(state=tk.DISABLED)
		self.btnExit.grid(row=0, column=4, sticky=tk.E, padx=2, pady=2)	
		
	def cleanFields(self):
		self.strBaseDirectory.set('/'.join(os.getcwd().split('/')[:-1] + ['examples']))
		self.strStrategyPort.set("")
		self.strMonitorPort.set("")
		self.strAgentsPorts.set("")
		for stringVar in self.agents['str']:
			stringVar.set("<MANUAL>")
		while self.nAgents > 1:
			self.remAgent(None)
		self.strLaunchEnviron.set("<MANUAL>")
		self.strLaunchTester.set("<MANUAL>")
		self.strLaunchMonitor.set("<MANUAL>")
		self.strLaunchStrategy.set("<MANUAL>")
		
		
class Actions(Build):
	def __init__(self, master):
		super(Actions, self).__init__(master)
	
	def newFile(self):
		self.cleanFields()
	
	def chooseBaseDirectory(self):
		self.strBaseDirectory.set(tkdialog.askdirectory())
	
	def openFile(self):
		conf = {}
		conf['defaultextension'] = '.conf'
		conf['filetypes'] = [('arquivos de configuração', '.conf')]
		filename = tkdialog.askopenfilename(**conf)
		self.cleanFields()
		if filename != '':
			configuration = json.load(open(filename))
			self.strBaseDirectory.set(configuration['baseDir'])
			self.strAgentsPorts.set(configuration['agentsPort']) 
			self.strMonitorPort.set(configuration['monitorPort']) 
			self.strStrategyPort.set(configuration['strategyPort'])
			for i in range(len(configuration['agents'])-1): 
				self.addAgent(self.frmAgents)
			for i, agente in enumerate(configuration['agents']):
				self.agents['str'][i].set(configuration['agents'][i])
			self.strLaunchEnviron.set(configuration['environ'])
			self.strLaunchTester.set(configuration['tester'])
			self.strLaunchMonitor.set(configuration['monitor']) 
			self.strLaunchStrategy.set(configuration['strategy'])
		else:
			pass
	
	def fillConfiguration(self):
		configuration = {}
		configuration['baseIp'] = getIp()
		configuration['baseDir'] = self.strBaseDirectory.get()
		configuration['agentsPort'] = self.strAgentsPorts.get()
		configuration['monitorPort'] = self.strMonitorPort.get()
		configuration['strategyPort'] = self.strStrategyPort.get()
		configuration['agents'] = []
		for stringVar in self.agents['str']:
			configuration['agents'].append(stringVar.get())
		configuration['environ'] = self.strLaunchEnviron.get()
		configuration['tester'] = self.strLaunchTester.get()
		configuration['monitor'] = self.strLaunchMonitor.get()
		configuration['strategy'] = self.strLaunchStrategy.get()
        #FIXME: incompleto!
		#prepareConfiguration(configuration)
		return configuration
	
	def saveFile(self):
		opt = {}
		opt['defaultextension'] = '.conf'
		opt['filetypes'] = [('arquivos de configuração', '.conf')]
		filename = tkdialog.asksaveasfilename(**opt)
		configuration = self.fillConfiguration()
		if filename != '':
			f = open(filename,'w')
			json.dump(configuration, f, sort_keys=True, indent=4)
			f.close()
		else:
			pass
		
	def quit(self):
		self.master.destroy()
	

class Events(Actions):
	def __init__(self, master):
		super(Events, self).__init__( master)
		
		self.btnAddAgent.bind("<Button-1>", self.clickAddAgent)
		self.btnAddAgent.bind("<space>", self.clickAddAgent)
		self.btnAddAgent.bind("<Return>", self.clickAddAgent)
		self.addAgent(self.frmAgents)
		
		self.btnBaseDirectory.bind("<Button-1>", self.clickChooseDirectory)
		self.btnBaseDirectory.bind("<space>", self.clickChooseDirectory)
		self.btnBaseDirectory.bind("<Return>", self.clickChooseDirectory)

		self.btnRemAgent.bind("<Button-1>", self.clickRemAgent)
		self.btnRemAgent.bind("<space>", self.clickRemAgent)
		self.btnRemAgent.bind("<Return>", self.clickRemAgent)
		
		self.btnNew.bind("<Button-1>", self.clickNewFile)
		self.btnNew.bind("<space>", self.clickNewFile)
		self.btnNew.bind("<Return>", self.clickNewFile)		

		self.btnOpen.bind("<Button-1>", self.clickOpenFile)
		self.btnOpen.bind("<space>", self.clickOpenFile)
		self.btnOpen.bind("<Return>", self.clickOpenFile)	

		self.btnSave.bind("<Button-1>", self.clickSaveFile)
		self.btnSave.bind("<space>", self.clickSaveFile)
		self.btnSave.bind("<Return>", self.clickSaveFile)
		
		self.btnExit.bind("<Button-1>", self.clickExit)
		self.btnExit.bind("<space>", self.clickExit)
		self.btnExit.bind("<Return>", self.clickExit)
		
		
	def clickChooseDirectory(self, event):
		self.chooseBaseDirectory()
		
	def clickNewFile(self, event):
		self.newFile()

	def clickRemAgent(self, event):
		self.remAgent(self.frmAgents)
		
	def clickAddAgent(self, event):
		self.addAgent(self.frmAgents)
		
	def clickOpenFile(self, event):
		self.openFile()
	
	def clickSaveFile(self, event):
		self.saveFile()
	
	def clickExit(self, event):
		self.quit()
		

class ZephyrusConfiguration(Events):
	def __init__(self):
		self.master = tk.Tk()
		self.master.title("Zephyrus")
		self.master.resizable(False, False)
		self.master.config(**common_config)
		self.master.configure(bg='white')
		super(ZephyrusConfiguration, self).__init__(self.master)
		tk.mainloop()

