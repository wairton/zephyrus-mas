import os
import sys
from subprocess import Popen, PIPE


def killpython():
    os.system("ps aux | grep python | grep {} > delme".format(sys.argv[1]))
    for line in open('delme').readlines():
        os.system('kill {}'.format(line.strip().split()[1]))
    os.system("rm crap")


if __name__ == '__main__':
    killpython()
