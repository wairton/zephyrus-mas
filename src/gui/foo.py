#-*-coding:utf-8-*-
import re
import string

def prepareConfiguration(configuration):
    ip = configuration['baseIp']
    agentsPort = int(configuration['agentsPort'])
#   configuration['environ'] = re.sub('<[iI][pP]>', ip + ':' + str(agentsPort), configuration['environ'])
    configuration['environ'] = re.sub('<[iI][pP]>', ip, configuration['environ'])
    agentsPort += 1
    for i in range(len(configuration['agents'])):
        agconfig = configuration['agents'][i]
        agconfig = re.sub('<[iI][pP]>', ip + ':' + str(agentsPort + i), agconfig)
        configuration['agents'][i] = re.sub('<[iI][pP]>', ip, configuration['agents'][i])
#       configuration['agents'][i] = re.sub('<[iI][pP]>', ip + ':' + str(agentsPort + i), configuration['agents'][i])
    monitorPort = configuration['monitorPort']
#   configuration['monitor'] = re.sub('<[iI][pP]>', ip + ':' + monitorPort, configuration['monitor'])
    configuration['monitor'] = re.sub('<[iI][pP]>', ip, configuration['monitor'])
    strategyPort = configuration['strategyPort']
#   configuration['strategy'] = re.sub('<[iI][pP]>', ip + ':' + strategyPort, configuration['strategy'])
    configuration['strategy'] = re.sub('<[iI][pP]>', ip, configuration['strategy'])
    print configuration
