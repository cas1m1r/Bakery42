from datetime import date
import random
import string
import time
import os

def create_timestamp():
    date = time.localtime(time.time())
    mo = str(date.tm_mon)
    day = str(date.tm_mday)
    yr = str(date.tm_year)

    hr = str(date.tm_hour)
    min = str(date.tm_min)
    sec = str(date.tm_sec)

    date = mo + '/' + day + '/' + yr
    timestamp = hr + ':' + min + ':' + sec
    return date, timestamp


def random_filename(ext):
	alphas = list(string.ascii_lowercase)
	return f'{"".join(random.sample(alphas,6))}{ext}'

def rmt_cmd(fulladdr, cmd):
	tmp = random_filename('.txt')
	result = ''
	try:
		os.system(f'ssh {fulladdr} {cmd} > {tmp}')
		result = open(tmp,'r').read().split('\n')
	except:
		pass
	os.remove(tmp)
	return result

def execute(cmd, verbose):
	tmp = random_filename('.sh')
	open(tmp,'w').write(f'#!/bin/bash\n{cmd}\nrm $0\n#EOF')
	return local_cmd(f'bash {tmp} ', verbose)

def remote_execute(nodestr, cmd, rpath, verbose):
	tmp = random_filename('.sh')
	open(tmp,'w').write(f'#!/bin/bash\ncd {rpath}\n{cmd} \nrm $0\n#EOF')
	execute(f'sftp {nodestr}:/home/{nodestr.split("@")[0]}/ <<< $"put {tmp}"',False)
	# rmt_cmd(nodestr, f'chmod +x {tmp}')
	return rmt_cmd(nodestr, f'bash {tmp} &')

def local_cmd(cmd, verbose):
	tmp = random_filename('.txt')
	try:
		os.system(f'{cmd} > {tmp}')
		result = open(tmp,'r').read().split('\n')
	except:
		pass
	os.remove(tmp)
	return result 

def timer(start, interval, maxwait):
	timing = True
	last_tick = 0
	try:
		while timing:
			dt = time.time() - start
			if int(dt)>0 and int(dt)%interval == 0 and int(dt) > last_tick:
				print(f'{time.time()-start}s have elapsed')
				last_tick = int(dt)
			if dt >= maxwait:
				timing = False
	except KeyboardInterrupt:
		timing = False
		pass
	return

