import json
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import zmq

from input_dialog import InputDialogMulti
from connection import getIp

common_config = {
    'bg' : '#e6e6e6',
    'borderwidth' : 2
}

class Build:
    def __init__(self, master):
        self.frm_connect = tk.Frame(master, **common_config)
        self.build_assistants_opt(self.frm_connect)
        self.frm_connect.pack(fill=tk.X, expand=True)

        self.frm_config = tk.Frame(master, **common_config)
        self.build_load_configuration(self.frm_config)
        self.frm_config.pack(fill=tk.X, expand=True)

        self.frm_log = tk.Frame(master, **common_config)
        self.build_log(self.frm_log)
        self.frm_log.pack(fill=tk.X, expand=True)

        self.frm_control = tk.Frame(master, **common_config)
        self.build_control(self.frm_control)
        self.frm_control.pack(fill=tk.X, expand=True)

    def build_assistants_opt(self, master):
        self.lbl_main_ip = tk.Label(master, text="Qual o ip?", **common_config)
        self.lbl_main_ip.grid(row=1, column=0, sticky=tk.E, padx=2)

        self.str_main_ip = tk.StringVar()
        self.ent_main_ip = tk.Entry(master)
        self.ent_main_ip.config(width=16, justify=tk.CENTER)
        self.ent_main_ip.config(textvariable=self.strMain_ip)
        self.ent_main_ip.grid(row=1, column=1, sticky=tk.W, padx=2)
        self.str_main_ip.set("127.0.0.1")

        self.lbl_mainPort = tk.Label(master, text="Qual a porta?", **common_config)
#       self.lbl_assistants.config()
        self.lbl_mainPort.grid(row=1, column=2, sticky=tk.E, padx=2)

        self.str_mainPort = tk.StringVar()
        self.ent_mainPort = tk.Entry(master)
        self.ent_mainPort.config(width=5, justify=tk.CENTER)
        self.ent_mainPort.config(textvariable=self.strMainPort)
        self.ent_mainPort.grid(row=1, column=3, sticky=tk.W, padx=2)
        self.str_mainPort.set("7000")

        self.btn_assitants = tk.Button(master, text="Conectar", **common_config)
        self.btn_assitants.grid(row=1, column=4, sticky=tk.W, padx=2)

    def build_loadConfiguration(self, master):
        self.btn_loadConf = tk.Button(master, text="Configuração...", **common_config)
        self.btn_loadConf.pack(anchor=tk.W)

        self.txt_config = tk.Text(master)
        self.txt_config.config(height=10, yscrollcommand=True)
        self.txt_config.pack(side=tk.BOTTOM)

    def build_log(self, master):
        self.lbl_log = tk.Label(master, text="log: ", **common_config)
        self.lbl_log.pack(anchor=tk.W)

        self.txt_log = tk.Text(master)
        self.txt_log.config(height=10, yscrollcommand=True, bg='#000000', fg='#fff')
        self.txt_log.pack()

    def build_control(self, master):
        #start button
        self.btn_start = tk.Button(master, text="Start", width=8, **common_config)
        self.btn_start.grid(row=0, column=1, sticky=tk.E, padx=2, pady=2)
        #stop button
        self.btn_stop = tk.Button(master, text="Stop", width=8, **common_config)
        self.btn_stop.grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)
        #restart button
        self.btn_restart = tk.Button(master, text="Restart", width=8, **common_config)
        self.btn_restart.grid(row=0, column=3, sticky=tk.E, padx=2, pady=2)
        #exit button
        self.btn_exit = tk.Button(master, text="Exit", width=8, **common_config)
        self.btn_exit.grid(row=0, column=4, sticky=tk.E, padx=2, pady=2)


class Actions(Build):
    def __init__(self, master):
        super().__init__(master)

    def connect(self, event):
#       info = Input_dialogMulti(self.master, event, "Qual o ip?", "Qual a porta?")
#       self.master.wait_window(info.top)
        contexto = zmq.Context()
        socket_envio = contexto.socket(zmq.PUSH)
        socket_resposta = contexto.socket(zmq.PULL)
        ip, porta = self.str_main_ip.get(), self.strMainPort.get()
        socket_resposta.bind("tcp://" + getIp() + ":" + porta)
        print("Tentando conexão com {}:{}".format(ip, porta))
        socket_envio.connect("tcp://" + ip + ":" + porta)
        print("Conexão estabelecida, enviando mensagem ")
        socket_envio.send("olá sou o " + getIp())
        print("Aguardando resposta...")
        tentativas = 0
        while tentativas < 1000:
            msg = None
            try:
                msg = socket_resposta.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                tentativas += 1
            if msg != None:
                self.write_log("recebi " + msg + '\n')
                break
            time.sleep(0.01)
        del socket_resposta
        del socket_envio
        return

    def set_centralized(self, event):
        self.centralized = True

    def set_distributed(self, event):
        self.centralized = False

    def load_configuration(self):
        filename = tkdialog.askopenfilename()

    def write_log(self, texto):
        self.txt_log.insert(tk.END, texto)
        self.master.update_idletasks()

    def quit(self):
        self.master.destroy()


class Events(Actions):
    def __init__(self, master):
        super().__init__(master)
        self.btn_assitants.bind("<Button-1>", self.clickConnect)
        self.btn_assitants.bind("<Return>", self.clickConnect)
        self.btn_assitants.bind("<space>", self.clickConnect)
        self.btn_loadConf.config(command=self.loadConfiguration)
        self.btn_exit.bind("<Button-1>", self.clickExit)
        self.btn_exit.bind("<space>", self.clickExit)
        self.btn_exit.bind("<Return>", self.clickExit)

    def click_connect(self, event):
        self.connect(event)

    def click_centralized(self, event):
        self.lbl_assistants.config(state=tk.DISABLED)
        self.ent_numAssistants.config(state=tk.DISABLED)
        self.btn_assitants.config(state=tk.DISABLED)
        self.set_centralized(event)

    def click_distributed(self, event):
        self.lbl_assistants.config(state=tk.NORMAL)
        self.ent_numAssistants.config(state=tk.NORMAL)
        self.btn_assitants.config(state=tk.NORMAL)
        self.set_distributed(event)

    def click_exit(self, event):
        self.quit()


class ZephyrusAuxiliary(Events):
    def __init__(self):
        self.master = tk.Tk()
        self.master.title("Zephyrus Auxiliary")
        self.master.resizable(False, False)
        super().__init__(self.master)
        self.txt_log.insert(tk.END, "*" * 24)
        self.txt_log.insert(tk.END, " ZEPHYRUS - version 0.1 - 2012 ")
        self.txt_log.insert(tk.END, "*" * 24 + '\n')

        tk.mainloop()
