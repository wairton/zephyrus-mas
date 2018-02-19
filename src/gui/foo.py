#-*-coding:utf-8-*-
import re
import string

def prepare_configuration(configuration):
    ip = configuration['baseIp']
    agents_port = int(configuration['agentsPort'])
#   configuration['environ'] = re.sub('<[iI][pP]>', ip + ':' + str(agents_port), configuration['environ'])
    configuration['environ'] = re.sub('<[iI][pP]>', ip, configuration['environ'])
    agents_port += 1
    for i in range(len(configuration['agents'])):
        agconfig = configuration['agents'][i]
        agconfig = re.sub('<[iI][pP]>', ip + ':' + str(agents_port + i), agconfig)
        configuration['agents'][i] = re.sub('<[iI][pP]>', ip, configuration['agents'][i])
#       configuration['agents'][i] = re.sub('<[iI][pP]>', ip + ':' + str(agents_port + i), configuration['agents'][i])
    monitor_port = configuration['monitorPort']
#   configuration['monitor'] = re.sub('<[iI][pP]>', ip + ':' + monitorPort, configuration['monitor'])
    configuration['monitor'] = re.sub('<[iI][pP]>', ip, configuration['monitor'])
    strategy_port = configuration['strategyPort']
#   configuration['strategy'] = re.sub('<[iI][pP]>', ip + ':' + strategyPort, configuration['strategy'])
    configuration['strategy'] = re.sub('<[iI][pP]>', ip, configuration['strategy'])
    print(configuration)
