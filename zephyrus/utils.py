import os
from subprocess import Popen, PIPE


def killpython():
    os.system("ps aux | grep zdt > crap")
    for line in open('crap').readlines():
        os.system('kill {}'.format(line.strip().split()[1]))
    os.system("rm crap")


if __name__ == '__main__':
    killpython()
