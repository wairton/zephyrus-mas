from subprocess import Popen, PIPE

out, err = Popen("ps ux", shell=True, stdout=PIPE).communicate()
for line in out.split('\n'):
    if not 'python' in line:
        continue
    print line
