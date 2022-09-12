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

def levenshtein(seq1, seq2):
	size_x = len(seq1) + 1
	size_y = len(seq2) + 1
	matrix = np.zeros ((size_x, size_y))
	for x in range(size_x):
		matrix [x, 0] = x
	for y in range(size_y):
 		matrix [0, y] = y

	for x in range(1, size_x):
		for y in range(1, size_y):
			if seq1[x-1] == seq2[y-1]:
				matrix [x,y] = min(
					matrix[x-1, y] + 1,
					matrix[x-1, y-1],
					matrix[x, y-1] + 1)
			else:
				matrix [x,y] = min(
					matrix[x-1,y] + 1,
					matrix[x-1,y-1] + 1,
					matrix[x,y-1] + 1)
	return matrix[size_x - 1, size_y - 1]

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

def nodestr2host(nodestr):
	return nodestr.split('@')[0]

def spot_a_squat(ts, domain, real_domains):
	for legit in real_domains:
		score = levenshtein(domain, legit)
		if 2 >= score > 0:
			print(f'{ts} {fR} {domain} {fW} [similar to {legit}?]')
			return True, legit
	return False, ''

def parse_entry(line, dolog, fileout):
	try:
		fields = line.split(' ')
		ldate = fields[0].replace('[','')
		ltime = fields[1].replace(']','')
		site = fields[2]
		ipv4 = fields[-1]
	except:
		return False, {}
	is_squatter, site_squatted = spot_a_squat(' '.join(fields[0:1]), site, TOP_DOMAINS)
	if is_squatter:
		return True, {'squatter': is_squatter, 'date_registered': [ldate,ltime], 'site_registered':site,'site_squatted': site_squatted}
	else:
		return False, {}