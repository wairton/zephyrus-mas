#-*-coding:utf-8-*-
#This work is under LGPL license, see the LICENSE.LGPL file for further details.

import json
import time
import Tkinter as tk
import tkFileDialog as tkdialog
import tkMessageBox as tkmessage

import zmq

#from inputDialog import InputDialog
from connection import getIp
#from core.Roteiro import Roteiro
#from core.Tes

common_config = {
    'bg' : '#e6e6e6',
    'borderwidth' : 2
}

class Build(object):
    def __init__(self, master):
        self.frmMode = tk.Frame(master, **common_config)
        self.buildModes(self.frmMode)
        self.buildAssistantsOpt(self.frmMode)
        self.frmMode.pack(fill=tk.X, expand=True)

        self.frmConfig = tk.Frame(master, **common_config)
        self.buildLoadConfiguration(self.frmConfig)
        self.frmConfig.pack(fill=tk.X, expand=True)

        self.frmLog = tk.Frame(master, **common_config)
        self.buildLog(self.frmLog)
        self.frmLog.pack(fill=tk.X, expand=True)

        self.frmControl = tk.Frame(master, **common_config)
        self.buildControl(self.frmControl)
        self.frmControl.pack(fill=tk.X, expand=True)

    def buildModes(self, master):
        self.modeOpt = tk.IntVar()

        self.optCentralized = tk.Radiobutton(master, **common_config)
        self.optCentralized.config(text="centralizado", variable=self.modeOpt, value=1)
#       self.optCentralized.grid(row=0, column=0, sticky=tk.E, padx=2)
        self.optCentralized.grid(row=0, column=0, padx=2)

        self.optDistributed = tk.Radiobutton(master, **common_config)
        self.optDistributed.config(text="distribuído", variable=self.modeOpt, value=2)
#       self.optDistributed.grid(row=0, column=1, sticky=tk.E, padx=2)
        self.optDistributed.grid(row=0, column=4)

        self.modeOpt.set(1)

    def buildAssistantsOpt(self, master):
        self.lblAssistants = tk.Label(master, text="número de auxiliares: ", **common_config)
        self.lblAssistants.config(state=tk.DISABLED)
        self.lblAssistants.grid(row=1, column=0, sticky=tk.E, padx=2)

        self.numAssistants = tk.StringVar()
        self.entNumAssistants = tk.Entry(master, **common_config)
        self.entNumAssistants.config(state=tk.DISABLED, width=5, justify=tk.CENTER)
        self.entNumAssistants.config(textvariable=self.numAssistants)
        self.entNumAssistants.grid(row=1, column=1, sticky=tk.W, padx=2)
        self.numAssistants.set("0")

        self.lblConnectPort = tk.Label(master, text="porta de espera: ", **common_config)
        self.lblConnectPort.config(state=tk.DISABLED)
        self.lblConnectPort.grid(row=1, column=2, sticky=tk.W, padx=2)

        self.connectPort = tk.StringVar()
        self.entConnectPort = tk.Entry(master)
        self.entConnectPort.config(state=tk.DISABLED, width=5, justify=tk.CENTER)
        self.entConnectPort.config(textvariable=self.connectPort)
        self.entConnectPort.grid(row=1, column=3, sticky=tk.W, padx=2)
        self.connectPort.set("7000")

        self.btnAssitants = tk.Button(master, text="Conectar", **common_config)
        self.btnAssitants.config(state=tk.DISABLED)
        self.btnAssitants.grid(row=1, column=4, sticky=tk.E, padx=25)

    def buildLoadConfiguration(self, master):
        self.btnLoadConf = tk.Button(master, text="Configuração...", width=10, **common_config)
        self.btnLoadConf.grid(row=0, column=0)
        self.btnLoadScript = tk.Button(master, text="Roteiro...", width=10, **common_config)
        self.btnLoadScript.grid(row=0, column=1)

    def buildLog(self, master):
        self.lblLog = tk.Label(master, text="log: ", **common_config)
        self.lblLog.pack(anchor=tk.W)

        self.scrLog = tk.Scrollbar(master)
        self.txtLog = tk.Text(master)
        self.txtLog.config(height=20, yscrollcommand=True, bg='#000000', fg='#fff')
        self.txtLog.pack(side=tk.LEFT)
        self.scrLog.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrLog.config(command=self.txtLog.yview)

    def buildControl(self, master):
        #start button
        self.btnStart = tk.Button(master, text="Start", width=8, **common_config)
        self.btnStart.grid(row=0, column=1, sticky=tk.E, padx=2, pady=2)
        #stop button
        self.btnStop = tk.Button(master, text="Stop", width=8, **common_config)
        self.btnStop.grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)
        #restart button
        self.btnRestart = tk.Button(master, text="Restart", width=8, **common_config)
        self.btnRestart.grid(row=0, column=3, sticky=tk.E, padx=2, pady=2)
        #exit button
        self.btnExit = tk.Button(master, text="Exit", width=8, **common_config)
        self.btnExit.grid(row=0, column=4, sticky=tk.E, padx=2, pady=2)


class Actions(Build):
    def __init__(self, master):
        super(Actions, self).__init__(master)

    def connect(self, event):
#       self.txtLog.insert(tk.END, "connect")
        if (int(self.numAssistants.get()) <= 0):
            tkmessage.showwarning("Atenção", "Informe a quantidade de assistentes.")
            return False
#       self.txtLog.insert(tk.END, "connect")
        porta = self.connectPort.get()
        contexto = zmq.Context()
        socketResponder = []
        socketRequisicoes = contexto.socket(zmq.PULL)
        self.writeLog("bind em tcp://" + getIp() + ":" + porta + '\n')
        socketRequisicoes.bind("tcp://" + getIp() + ":" + porta)
        self.writeLog("aguardando requisições...\n")
        print 'são ', self.numAssistants.get()
        tentativas = 0
        numAssistants = int(self.numAssistants.get())
        self.assistantasIps = []
        while tentativas < 1000 and len(socketResponder) < numAssistants:
            socketRequisicoes.setsockopt(zmq.LINGER, 1)
            msg = None
            try:
                msg = socketRequisicoes.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                tentativas += 1
            if msg != None:
                tentativas = 0
                self.writeLog(str(len(socketResponder)+1) + ": ")
                self.writeLog("recebi " + msg + '\n')
                socketResponder.append(contexto.socket(zmq.PUSH))
                self.assistantasIps.append(msg.split()[-1])
                socketResponder[-1].connect("tcp://" + msg.split()[-1] + ":" + porta)
                socketResponder[-1].send("e aí mano, blz? seu id é:"+ str(len(socketResponder)))
            time.sleep(0.01)
        if len(socketResponder) != numAssistants:
            self.writeLog("tempo de espera limite atingido\n")
        else:
            print self.assistantasIps


    def writeLog(self, texto):
        self.txtLog.config(state="normal")
        self.txtLog.insert(tk.END, texto)
        self.master.update_idletasks()
        self.txtLog.config(state="disabled")

    def setCentralized(self, event):
#       self.txtLog.insert(tk.END, "centralizado")
        self.centralized = True

    def setDistributed(self, event):
#       self.txtLog.insert(tk.END, "distribuido")
        self.centralized = False

    def loadScript(self):
        filename = tkdialog.askopenfilename()
        if filename != '':
            self.writeLog('carregando roteiro: ' + filename + '\n')
            script = json.load(open(filename))
        else:
            pass

    def loadConfiguration(self):
        filename = tkdialog.askopenfilename()
        if filename != '':
            self.writeLog('carregando configuração: ' + filename + '\n')
            try:
                config = json.load(open(filename))
                #testar se o arquivo é válido:
                valid = ['agents', 'ambient', 'monitor', 'strategy']
                keys = config.keys()
                for item in valid:
                    if item not in config.keys():
                        self.writeLog('arquivo de configuração inválido\n')
                        return
            except:
                self.writeLog('erro ao carregar arquivo de configuração\n')
                return
            self.writeLog("agente(s):\n")
            for agente in config['agents']:
                self.writeLog(' ' * 8 + agente + '\n')
            self.writeLog('Ambiente: ' + config['ambient'] + '\n')
            self.writeLog('Monitor: ' + config["monitor"] + '\n')
            self.writeLog(u'Estratégia: ' + config['strategy'] + '\n')
        else:
            pass

    def quit(self):
        self.master.destroy()


class Events(Actions):
    def __init__(self, master):
        super(Events, self).__init__( master)
        self.optCentralized.bind("<Button-1>", self.clickCentralized)
        self.optCentralized.bind("<Return>", self.clickCentralized)
        self.optCentralized.bind("<space>", self.clickCentralized)

        self.optDistributed.bind("<Button-1>", self.clickDistributed)
        self.optDistributed.bind("<Return>", self.clickDistributed)
        self.optDistributed.bind("<space>", self.clickDistributed)

        self.btnAssitants.bind("<Button-1>", self.clickConnect)
        self.btnAssitants.bind("<Return>", self.clickConnect)
        self.btnAssitants.bind("<space>", self.clickConnect)

        self.btnLoadConf.config(command=self.loadConfiguration)
        self.btnLoadScript.config(command=self.loadScript)

        self.btnExit.bind("<Button-1>", self.clickExit)
        self.btnExit.bind("<space>", self.clickExit)
        self.btnExit.bind("<Return>", self.clickExit)

    def clickConnect(self, event):
        self.connect(event)

    def clickCentralized(self, event):
        self.lblAssistants.config(state=tk.DISABLED)
        self.entNumAssistants.config(state=tk.DISABLED)
        self.lblConnectPort.config(state=tk.DISABLED)
        self.entConnectPort.config(state=tk.DISABLED)
        self.btnAssitants.config(state=tk.DISABLED)
#       self.btnAssitants.lower(self.frmMode)
        self.setCentralized(event)

    def clickDistributed(self, event):
        self.lblAssistants.config(state=tk.NORMAL)
        self.entNumAssistants.config(state=tk.NORMAL)
        self.lblConnectPort.config(state=tk.NORMAL)
        self.entConnectPort.config(state=tk.NORMAL)
        self.btnAssitants.config(state=tk.NORMAL)
#       self.btnAssitants.lift(self.frmMode)
        self.setDistributed(event)

    def clickExit(self, event):
        self.quit()


class Zephyrus(Events):
    def __init__(self):
        self.master = tk.Tk()
        self.master.title("Zephyrus")
        self.master.resizable(False, False)
        super(Zephyrus, self).__init__(self.master)
        #TODO: mover essa mensagem
        self.txtLog.insert(tk.END, "*" * 24)
        self.txtLog.insert(tk.END, " ZEPHYRUS - version 0.1 - 2012 ")
        self.txtLog.insert(tk.END, "*" * 24 + '\n')
        self.txtLog.config(state="disabled")

        tk.mainloop()


#if __name__ == '__main__':
#   Zephyrus()
