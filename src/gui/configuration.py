#-*-coding:utf-8-*-
#This work is under LGPL license, see the LICENSE.LGPL file for further details.

import json
import os
import tkinter as tk
from tkinter import filedialog

import zmq

from connection import getIp
from foo import prepare_configuration

common_config = {
    'bg' : '#e6e6e6'
}

class Build(object):
    num_agents = 0

    def __init__(self, master):
        self.frm_directory = tk.Frame(master, borderwidth=2, **common_config)
        self.build_directory_config(self.frm_directory)
        self.frm_directory.pack(fill=tk.X, expand=True)
        #port configuration
        self.frm_port = tk.Frame(master, borderwidth=2, **common_config)
        self.build_port_config(self.frm_port)
        self.frm_port.pack(fill=tk.X, expand=True)
        #agent buttons
        self.frm_agents_control = tk.Frame(master, borderwidth=2, **common_config)
        self.build_agents_control(self.frm_agents_control)
        self.frm_agents_control.pack(fill=tk.X, expand=True)
        #agents info
        self.frm_agents = tk.Frame(master, borderwidth=2, **common_config)
        self.build_agents_config(self.frm_agents)
        self.frm_agents.pack(fill=tk.X, expand=True)
        #other participants info
        self.frm_mode1 = tk.Frame(master, borderwidth=2, **common_config)
        self.build_assistants_opt2(self.frm_mode1)
        self.frm_mode1.pack(fill=tk.X, expand=True)
        #control buttons
        self.frm_control = tk.Frame(master, borderwidth=2, **common_config)
        self.build_control(self.frm_control)
        self.frm_control.pack(fill=tk.X, expand=True)

    def build_directory_config(self, master):
        #label
        self.lbl_base_directory = tk.Label(master, text="diretório base: ", **common_config)
        self.lbl_base_directory.grid(row=0, column=0, sticky=tk.E, padx=2)
        #entry
        self.str_base_directory = tk.StringVar()
        self.ent_base_directory = tk.Entry(master)
        self.ent_base_directory.config(width=50, justify=tk.CENTER)
        self.ent_base_directory.config(textvariable=self.str_base_directory)
        self.ent_base_directory.grid(row=0, column=1, sticky=tk.W, padx=2)
        self.str_base_directory.set('/'.join(os.getcwd().split('/')[:-1] + ['examples']))
        #button
        self.btn_base_directory = tk.Button(master, text="...", **common_config)
        self.btn_base_directory.grid(row=0, column=2, padx=2)

    def build_port_config(self, master):
        self.lbl_ports = tk.Label(master, text="ports :", **common_config)
        self.lbl_ports.grid(row=0, column=0, sticky=tk.E, padx=2)
        #just to add space (I know, it's ugly)
        tk.Label(master, text=" " * 7, **common_config).grid(row=0, column=1, sticky=tk.E, padx=2)
        #agent stuff
        self.lbl_agents_ports = tk.Label(master, text="agents:", **common_config)
        self.lbl_agents_ports.grid(row=0, column=2, sticky=tk.E, padx=2)
        self.str_agents_ports = tk.StringVar()
        self.ent_agents_ports = tk.Entry(master)
        self.ent_agents_ports.config(width=5, justify=tk.CENTER)
        self.ent_agents_ports.config(textvariable=self.str_agents_ports)
        self.ent_agents_ports.grid(row=0, column=3, sticky=tk.W, padx=2)
        #monitor stuff
        tk.Label(master, text="monitor:", **common_config).grid(row=0, column=4, sticky=tk.E, padx=2)
        self.str_monitor_port = tk.StringVar()
        self.ent_monitor_port = tk.Entry(master)
        self.ent_monitor_port.config(width=5, justify=tk.CENTER)
        self.ent_monitor_port.config(textvariable=self.str_monitor_port)
        self.ent_monitor_port.grid(row=0, column=5, sticky=tk.W, padx=2)
        self.str_monitor_port.set("")
        #strategy stuff
        tk.Label(master, text="strategy:", **common_config).grid(row=0, column=6, sticky=tk.E, padx=2)
        self.str_strategy_port = tk.StringVar()
        self.ent_strategy_port = tk.Entry(master)
        self.ent_strategy_port.config(width=5, justify=tk.CENTER)
        self.ent_strategy_port.config(textvariable=self.str_strategy_port)
        self.ent_strategy_port.grid(row=0, column=7, sticky=tk.W, padx=2)
        self.str_strategy_port.set("")

    def build_agents_control(self, master):
        self.btn_add_agent = tk.Button(master, text="+ agent", **common_config)
        self.btn_add_agent.grid(row=0, column=1)
        self.btn_rem_agent = tk.Button(master, text="- agent", **common_config)
        self.btn_rem_agent.grid(row=0, column=2)

    def build_agents_config(self, master):
        self.agents = {}
        for i in ['lbl', 'ent', 'str']:
            self.agents[i] = []

    def add_agent(self, master):
        lbl = tk.Label(master, text="executar agente (" + str(self.num_agents + 1) + "):", **common_config)
        self.agents['lbl'].append(lbl)
        self.agents['lbl'][-1].grid(row=self.num_agents + 1, column=0, sticky=tk.E, padx=2)
        #entry stuff
        self.agents['str'].append(tk.StringVar())
        self.agents['ent'].append(tk.Entry(master))
        self.agents['ent'][-1].config(width=50, justify=tk.CENTER)
        self.agents['ent'][-1].config(textvariable=self.agents['str'][-1])
        self.agents['ent'][-1].grid(row=self.num_agents + 1, column=1, sticky=tk.W, padx=2)
        self.agents['str'][-1].set("<MANUAL>")
        #
        self.num_agents += 1

    def rem_agent(self, master):
        if self.num_agents < 1:
            return False
        self.agents['lbl'][-1].grid_forget()
        self.agents['lbl'].pop()
        self.agents['str'].pop()
        self.agents['ent'][-1].grid_forget()
        self.agents['ent'].pop()
        self.num_agents -= 1

    def build_assistants_opt2(self, master):
        btn_config = {'width':50, 'justify':tk.CENTER}
        #environ stuff
        self.lbl_launch_environ = tk.Label(master, text="executar ambiente: ", **common_config)
        self.lbl_launch_environ.grid(row=0, column=0, sticky=tk.E, padx=2)
        self.str_launch_environ = tk.StringVar()
        self.ent_launch_environ = tk.Entry(master)
        self.ent_launch_environ.config(**btn_config)
        self.ent_launch_environ.config(textvariable=self.str_launch_environ)
        self.ent_launch_environ.grid(row=0, column=1, sticky=tk.W, padx=2)
        self.str_launch_environ.set("<MANUAL>")
        #tester stuff
        self.lbl_launch_tester = tk.Label(master, text="executar testador: ", **common_config)
        self.lbl_launch_tester.grid(row=1, column=0, sticky=tk.E, padx=2)
        self.str_launch_tester = tk.StringVar()
        self.ent_launch_tester = tk.Entry(master)
        self.ent_launch_tester.config(**btn_config)
        self.ent_launch_tester.config(textvariable=self.str_launch_tester)
        self.ent_launch_tester.grid(row=1, column=1, sticky=tk.W, padx=2)
        self.str_launch_tester.set("<MANUAL>")
        #monitor stuff
        self.lbl_launch_monitor = tk.Label(master, text="executar monitor: ", **common_config)
        self.lbl_launch_monitor.grid(row=2, column=0, sticky=tk.E, padx=2)
        self.str_launch_monitor = tk.StringVar()
        self.ent_launch_monitor = tk.Entry(master)
        self.ent_launch_monitor.config(**btn_config)
        self.ent_launch_monitor.config(textvariable=self.str_launch_monitor)
        self.ent_launch_monitor.grid(row=2, column=1, sticky=tk.W, padx=2)
        self.str_launch_monitor.set("<MANUAL>")
        #strategy stuff
        self.lbl_launch_strategy = tk.Label(master, text="executar estratégia: ", **common_config)
        self.lbl_launch_strategy.grid(row=3, column=0, sticky=tk.E, padx=2)
        self.str_launch_strategy = tk.StringVar()
        self.ent_launch_strategy = tk.Entry(master)
        self.ent_launch_strategy.config(**btn_config)
        self.ent_launch_strategy.config(textvariable=self.str_launch_strategy)
        self.ent_launch_strategy.grid(row=3, column=1, sticky=tk.W, padx=2)
        self.str_launch_strategy.set("<MANUAL>")

    def build_load_configuration(self, master):
        #configuration
        self.btn_load_conf = tk.Button(master, text="Carregar Configuração...", **common_config)
        self.btn_load_conf.grid(row=0, column=0)
        #script
        self.btn_load_script = tk.Button(master, text="Carregar Roteiro...", **common_config)
        self.btn_load_script.grid(row=0, column=1)
        #configuration display
        self.txt_config = tk.Text(master)
        self.txt_config.config(height=10, yscrollcommand=True, **common_config)
        self.txt_config.grid(row=1, columnspan=2)

    def build_log(self, master):
        self.lbl_log = tk.Label(master, text="log: ", **common_config)
        self.lbl_log.pack(anchor=tk.W)
        #log display
        self.txt_log = tk.Text(master)
        self.txt_log.config(height=10, yscrollcommand=True, bg='#000000', fg='#fff')
        self.txt_log.pack()

    def build_control(self, master):
        self.container = container = tk.Frame(master)
        # container = master
        grid_config = {'row':0, 'sticky':tk.E, 'padx':2, 'pady':2}
        #new button
        self.btn_new = tk.Button(container, text="Novo", width=6, **common_config)
        self.btn_new.grid(column=1, **grid_config)
        #open button
        self.btn_open = tk.Button(container, text="Abrir", width=6, **common_config)
        self.btn_open.grid(column=2, **grid_config)
        #save button
        self.btn_save = tk.Button(container, text="Salvar", width=6, **common_config)
        self.btn_save.grid(column=3, **grid_config)
        #exit button
        self.btn_exit = tk.Button(container, text="Sair", width=6, **common_config)
        self.btn_exit.grid(column=4, **grid_config)

    def clean_fields(self):
        self.str_base_directory.set('/'.join(os.getcwd().split('/')[:-1] + ['examples']))
        self.str_strategy_port.set("")
        self.str_monitor_port.set("")
        self.str_agents_ports.set("")
        for string_var in self.agents['str']:
            string_var.set("<MANUAL>")
        while self.num_agents > 1:
            self.rem_agent(None)
        self.str_launch_environ.set("<MANUAL>")
        self.str_launch_tester.set("<MANUAL>")
        self.str_launch_monitor.set("<MANUAL>")
        self.str_launch_strategy.set("<MANUAL>")


class Actions(Build):
    def __init__(self, master):
        super(Actions, self).__init__(master)

    def new_file(self):
        self.clean_fields()

    def choose_base_directory(self):
        self.str_base_directory.set(filedialog.askdirectory())

    def open_file(self):
        conf = {}
        conf['defaultextension'] = '.conf'
        conf['filetypes'] = [('arquivos de configuração', '.conf')]
        filename = filedialog.askopenfilename(**conf)
        self.clean_fields()
        if filename != '':
            configuration = json.load(open(filename))
            self.str_base_directory.set(configuration['base_dir'])
            self.str_agents_ports.set(configuration['agents_port'])
            self.str_monitor_port.set(configuration['monitor_port'])
            self.str_strategy_port.set(configuration['strategy_port'])
            for i in range(len(configuration['agents'])-1):
                self.add_agent(self.frm_agents)
            for i, agente in enumerate(configuration['agents']):
                self.agents['str'][i].set(configuration['agents'][i])
            self.str_launch_environ.set(configuration['environ'])
            self.str_launch_tester.set(configuration['tester'])
            self.str_launch_monitor.set(configuration['monitor'])
            self.str_launch_strategy.set(configuration['strategy'])
        else:
            pass

    def fill_configuration(self):
        configuration = {}
        configuration['base_ip'] = get_ip()
        configuration['base_dir'] = self.str_base_directory.get()
        configuration['agents_port'] = self.str_agents_ports.get()
        configuration['monitor_port'] = self.str_monitor_port.get()
        configuration['strategy_port'] = self.str_strategy_port.get()
        configuration['agents'] = []
        for string_var in self.agents['str']:
            configuration['agents'].append(string_var.get())
        configuration['environ'] = self.str_launch_environ.get()
        configuration['tester'] = self.str_launch_tester.get()
        configuration['monitor'] = self.str_launch_monitor.get()
        configuration['strategy'] = self.str_launch_strategy.get()
        #FIXME: incompleto!
        #prepare_configuration(configuration)
        return configuration

    def save_file(self):
        opt = {}
        opt['defaultextension'] = '.conf'
        opt['filetypes'] = [('arquivos de configuração', '.conf')]
        filename = filedialog.asksaveasfilename(**opt)
        configuration = self.fill_configuration()
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

        self.btn_add_agent.bind("<Button-1>", self.click_add_agent)
        self.btn_add_agent.bind("<space>", self.click_add_agent)
        self.btn_add_agent.bind("<Return>", self.click_add_agent)
        self.add_agent(self.frm_agents)

        self.btn_base_directory.bind("<Button-1>", self.click_choose_directory)
        self.btn_base_directory.bind("<space>", self.click_choose_directory)
        self.btn_base_directory.bind("<Return>", self.click_choose_directory)

        self.btn_rem_agent.bind("<Button-1>", self.click_rem_agent)
        self.btn_rem_agent.bind("<space>", self.click_rem_agent)
        self.btn_rem_agent.bind("<Return>", self.click_rem_agent)

        self.btn_new.bind("<Button-1>", self.click_new_file)
        self.btn_new.bind("<space>", self.click_new_file)
        self.btn_new.bind("<Return>", self.click_new_file)

        self.btn_open.bind("<Button-1>", self.click_open_file)
        self.btn_open.bind("<space>", self.click_open_file)
        self.btn_open.bind("<Return>", self.click_open_file)

        self.btn_save.bind("<Button-1>", self.click_save_file)
        self.btn_save.bind("<space>", self.click_save_file)
        self.btn_save.bind("<Return>", self.click_save_file)

        self.btn_exit.bind("<Button-1>", self.click_exit)
        self.btn_exit.bind("<space>", self.click_exit)
        self.btn_exit.bind("<Return>", self.click_exit)


    def click_choose_directory(self, event):
        self.choose_base_directory()

    def click_new_file(self, event):
        self.new_file()

    def click_rem_agent(self, event):
        self.rem_agent(self.frm_agents)

    def click_add_agent(self, event):
        self.add_agent(self.frm_agents)

    def click_open_file(self, event):
        self.open_file()

    def click_save_file(self, event):
        self.save_file()

    def click_exit(self, event):
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


if __name__ == '__main__':
    ZephyrusConfiguration()
