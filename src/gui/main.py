import json
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

import zmq

from connection import getIp

common_config = {
    'bg' : '#e6e6e6',
    'borderwidth' : 2
}

common_config = {
    'borderwidth' : 1
}


class Build:
    def __init__(self, master):
        self.frm_mode = tk.Frame(master, **common_config)
        self.build_menu(master)
        self.build_modes(self.frm_mode)
        self.frm_mode.pack(fill=tk.X, expand=True)

        self.frm_config = tk.Frame(master, **common_config)
        #self.build_load_configuration(self.frm_config)
        self.frm_config.pack(fill=tk.X, expand=True)

        self.frm_log = tk.Frame(master, **common_config)
        self.build_log(self.frm_log)
        self.frm_log.pack(fill=tk.X, expand=True)

        self.frm_control = tk.Frame(master, **common_config)
        self.build_control(self.frm_control)
        self.frm_control.pack(fill=tk.X, expand=True)

    def build_menu(self, master):
        self.menubar = tk.Menu(master)
        master.config(menu=self.menubar)

    def build_modes(self, master):
        self.mode_opt = tk.IntVar()

        self.opt_centralized = tk.Radiobutton(master, **common_config)
        self.opt_centralized.config(text="centralizado", variable=self.mode_opt, value=1)
#       self.opt_centralized.grid(row=0, column=0, sticky=tk.E, padx=2)
        self.opt_centralized.grid(row=0, column=0, sticky=tk.W)

        self.opt_distributed = tk.Radiobutton(master, **common_config)
        self.opt_distributed.config(text="distribuído", variable=self.mode_opt, value=2)
#       self.opt_distributed.grid(row=0, column=1, sticky=tk.E, padx=2)
        self.opt_distributed.grid(row=0, column=1, sticky=tk.W)

        self.mode_opt.set(1)

        self.lbl_assistants = tk.Label(master, text="auxiliares: ", **common_config)
        self.lbl_assistants.config(state=tk.DISABLED)
        self.lbl_assistants.grid(row=0, column=2, sticky=tk.E)

        self.num_assistants = tk.StringVar()
        self.ent_num_assistants = tk.Entry(master, **common_config)
        self.ent_num_assistants.config(state=tk.DISABLED, width=5, justify=tk.CENTER)
        self.ent_num_assistants.config(textvariable=self.num_assistants)
        self.ent_num_assistants.grid(row=0, column=3, sticky=tk.W, padx=2)
        self.num_assistants.set("0")

        self.lbl_connect_port = tk.Label(master, text="porta: ", **common_config)
        self.lbl_connect_port.config(state=tk.DISABLED)
        self.lbl_connect_port.grid(row=0, column=4, sticky=tk.W, padx=2)

        self.connect_port = tk.StringVar()
        self.ent_connect_port = tk.Entry(master)
        self.ent_connect_port.config(state=tk.DISABLED, width=5, justify=tk.CENTER)
        self.ent_connect_port.config(textvariable=self.connect_port)
        self.ent_connect_port.grid(row=0, column=5, sticky=tk.W, padx=2)
        self.connect_port.set("7000")

        self.btn_assitants = tk.Button(master, text="Conectar", **common_config)
        self.btn_assitants.config(state=tk.DISABLED)
        self.btn_assitants.grid(row=0, column=6, sticky=tk.E)

    def build_load_configuration(self, master):
        self.btn_load_conf = tk.Button(master, text="Configuração...", width=10, **common_config)
        self.btn_load_conf.grid(row=0, column=0)
        self.btn_load_script = tk.Button(master, text="Roteiro...", width=10, **common_config)
        self.btn_load_script.grid(row=0, column=1)

    def build_log(self, master):
        self.lbl_log = tk.Label(master, text="log: ", **common_config)
        self.lbl_log.pack(anchor=tk.W)

        self.scr_log = tk.Scrollbar(master)
        self.txt_log = tk.Text(master)
        self.txt_log.config(height=10, yscrollcommand=True, bg='#000000', fg='#fff')
        self.txt_log.pack(side=tk.LEFT)
        self.scr_log.pack(side=tk.RIGHT, fill=tk.Y)
        self.scr_log.config(command=self.txt_log.yview)

    def build_control(self, master):
        #start button
        self.btn_start = tk.Button(master, text="Start", width=8, **common_config)
        #self.btn_start.pack(side=tk.BOTTOM)
        self.btn_start.grid(row=0, column=1, sticky=tk.E, padx=2, pady=2)
        #stop button
        self.btn_stop = tk.Button(master, text="Stop", width=8, **common_config)
        #self.btn_stop.pack(side=tk.LEFT)
        self.btn_stop.grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)
        #restart button
        self.btn_restart = tk.Button(master, text="Restart", width=8, **common_config)
        self.btn_restart.grid(row=0, column=3, sticky=tk.E, padx=2, pady=2)
        #exit button
        self.btn_exit = tk.Button(master, text="Exit", width=8, **common_config)
        self.btn_exit.grid(row=0, column=4, sticky=tk.E, padx=2, pady=2)


class Actions(Build):
    def __init__(self, master):
        super(Actions, self).__init__(master)

    def connect(self, event):
#       self.txt_log.insert(tk.END, "connect")
        if (int(self.num_assistants.get()) <= 0):
            messagebox.showwarning("Atenção", "Informe a quantidade de assistentes.")
            return False
#       self.txt_log.insert(tk.END, "connect")
        porta = self.connect_port.get()
        contexto = zmq.Context()
        socket_responder = []
        socket_requisicoes = contexto.socket(zmq.PULL)
        self.write_log("bind em tcp://" + get_ip() + ":" + porta + '\n')
        socket_requisicoes.bind("tcp://" + get_ip() + ":" + porta)
        self.write_log("aguardando requisições...\n")
        print('são ', self.num_assistants.get())
        tentativas = 0
        num_assistants = int(self.num_assistants.get())
        self.assistantas_ips = []
        while tentativas < 1000 and len(socket_responder) < num_assistants:
            socket_requisicoes.setsockopt(zmq.LINGER, 1)
            msg = None
            try:
                msg = socket_requisicoes.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                tentativas += 1
            if msg != None:
                tentativas = 0
                self.write_log(str(len(socket_responder)+1) + ": ")
                self.write_log("recebi " + msg + '\n')
                socket_responder.append(contexto.socket(zmq.PUSH))
                self.assistantas_ips.append(msg.split()[-1])
                socket_responder[-1].connect("tcp://" + msg.split()[-1] + ":" + porta)
                socket_responder[-1].send("e aí mano, blz? seu id é:"+ str(len(socket_responder)))
            time.sleep(0.01)
        if len(socket_responder) != num_assistants:
            self.write_log("tempo de espera limite atingido\n")
        else:
            print(self.assistantas_ips)

    def write_log(self, texto):
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, texto)
        self.master.update_idletasks()
        self.txt_log.config(state="disabled")

    def set_centralized(self, event):
#       self.txt_log.insert(tk.END, "centralizado")
        self.centralized = True

    def set_distributed(self, event):
#       self.txt_log.insert(tk.END, "distribuido")
        self.centralized = False

    def load_script(self):
        filename = filedialog.askopenfilename()
        if filename != '':
            self.write_log('carregando roteiro: ' + filename + '\n')
            script = json.load(open(filename))
        else:
            pass

    def load_configuration(self):
        filename = filedialog.askopenfilename()
        if filename != '':
            self.write_log('carregando configuração: ' + filename + '\n')
            try:
                config = json.load(open(filename))
                #testar se o arquivo é válido:
                valid = ['agents', 'ambient', 'monitor', 'strategy']
                keys = config.keys()
                for item in valid:
                    if item not in config.keys():
                        self.write_log('arquivo de configuração inválido\n')
                        return
            except:
                self.write_log('erro ao carregar arquivo de configuração\n')
                return
            self.write_log("agente(s):\n")
            for agente in config['agents']:
                self.write_log(' ' * 8 + agente + '\n')
            self.write_log('Ambiente: ' + config['ambient'] + '\n')
            self.write_log('Monitor: ' + config["monitor"] + '\n')
            self.write_log(u'Estratégia: ' + config['strategy'] + '\n')
        else:
            pass

    def quit(self):
        self.master.destroy()

    def start(self):
        print("run baby run!")

    def stop(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()


class Events(Actions):
    def __init__(self, master):
        super(Events, self).__init__( master)
        self.opt_centralized.bind("<Button-1>", self.click_centralized)
        self.opt_centralized.bind("<Return>", self.click_centralized)
        self.opt_centralized.bind("<space>", self.click_centralized)

        self.opt_distributed.bind("<Button-1>", self.click_distributed)
        self.opt_distributed.bind("<Return>", self.click_distributed)
        self.opt_distributed.bind("<space>", self.click_distributed)

        self.btn_assitants.bind("<Button-1>", self.click_connect)
        self.btn_assitants.bind("<Return>", self.click_connect)
        self.btn_assitants.bind("<space>", self.click_connect)


        filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Configuração...", command=self.load_configuration)
        filemenu.add_command(label="Roteiro...", command=self.load_script)
        self.menubar.add_cascade(label="Carregar", menu=filemenu)
        #self.btn_load_conf.config(command=self.load_configuration)
        #self.btn_load_script.config(command=self.loadScript)

        self.btn_exit.bind("<Button-1>", self.click_exit)
        self.btn_exit.bind("<space>", self.click_exit)
        self.btn_exit.bind("<Return>", self.click_exit)

        self.btn_start.bind("<Button-1>", self.click_start)
        self.btn_start.bind("<Return>", self.click_start)

        self.btn_stop.bind("<Button-1>", self.click_stop)
        self.btn_stop.bind("<Return>", self.click_stop)

        self.btn_restart.bind("<Button-1>", self.click_restart)
        self.btn_restart.bind("<Return>", self.click_restart)

    def click_connect(self, event):
        self.connect(event)

    def click_start(self, event):
        self.start()

    def click_stop(self, event):
        self.stop()

    def click_restart(self, event):
        self.restart()

    def click_centralized(self, event):
        self.lbl_assistants.config(state=tk.DISABLED)
        self.ent_num_assistants.config(state=tk.DISABLED)
        self.lbl_connect_port.config(state=tk.DISABLED)
        self.ent_connect_port.config(state=tk.DISABLED)
        self.btn_assitants.config(state=tk.DISABLED)
#       self.btn_assitants.lower(self.frm_mode)
        self.set_centralized(event)

    def click_distributed(self, event):
        self.lbl_assistants.config(state=tk.NORMAL)
        self.ent_num_assistants.config(state=tk.NORMAL)
        self.lbl_connect_port.config(state=tk.NORMAL)
        self.ent_connect_port.config(state=tk.NORMAL)
        self.btn_assitants.config(state=tk.NORMAL)
#       self.btn_assitants.lift(self.frm_mode)
        self.set_distributed(event)

    def click_exit(self, event):
        self.quit()


class Zephyrus(Events):
    def __init__(self):
        self.master = tk.Tk()
        self.master.title("Zephyrus")
        self.master.resizable(False, False)
        super(Zephyrus, self).__init__(self.master)
        #TODO: mover essa mensagem
        self.txt_log.insert(tk.END, "*" * 24)
        self.txt_log.insert(tk.END, " ZEPHYRUS - version 0.1.1 - 2013 ")
        self.txt_log.insert(tk.END, "*" * 24 + '\n')
        self.txt_log.config(state="disabled")

        tk.mainloop()


if __name__ == '__main__':
   Zephyrus()
