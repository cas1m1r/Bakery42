from colorama import init, Fore
from workforce import *
import pandas as pd
import numpy as np
from census import *
from bakeryutils import*
import threading
import json


top1m = pd.read_csv('top-1m.csv')
TOP_DOMAINS = list(top1m[:]['DOMAIN'])[0:999]


fB = Fore.LIGHTBLUE_EX
fR = Fore.RED
fW = Fore.WHITE
fM = Fore.MAGENTA
fC = Fore.CYAN
fG = Fore.GREEN
fY = Fore.YELLOW
fE = fW
OFF = ''


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


def spot_a_squat(ts, domain, real_domains):
	# pool = multiprocessing.Pool(5)
	for legit in real_domains:
		score = levenshtein(domain, legit)
		if 2 >= score > 0:
			print(f'{ts} {fR} {domain} {fW} [similar to {legit}?]')
			return True, legit
	return False, ''


def solo_check_for_squatters(log_name, log_data, n_threads=4):

	if len(log_name.split('assignment_'))>1:
		output = f'results_{log_name.split("assignment_")[1].split(".")[0]}.json'
		always_log = True
		worker = True
	else:
		always_log = False
		output = 'suspicious.json'
	pool = multiprocessing.Pool(n_threads)
	bad_domains = {'logfile': log_name, 'squatters': []}
	for entry in log_data:
		parse = pool.apply_async(parse_entry, (entry,always_log, output))
		try:
			squatting, squatters = parse.get(5)
			if squatting:
				bad_domains['squatters'].append(squatters)
			
		except multiprocessing.TimeoutError:
			pass

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


def distributed_squat_power(log_name, log_data, n_threads=25):
	# Create a version of the job each node can do
	bad_domains = {'logfile': log_name, 'squatters': []}
	# check which peers are available
	peers = load_nodes(os.getcwd())
	n_peers = 0 # include this computer as 1 node
	# count how many are active
	for node, is_connected in test_connections(peers).items():
		if is_connected:
			n_peers += 1
			print(f'[>] Transferring project files to {node} to allow them to work')
			transfer_project_files(peers[node])

	print('='*80)		
	entries_per_worker = round(len(log_data) / n_peers)
	
	# Create temp files for each worker with their portion of the log
	splits = np.linspace(0,len(log_data),n_peers+1)
	print(f'[+] {n_peers} are active and there are {len(log_data)} entries in {log_name}')
	assignments = {}; i = 0
	threads = multiprocessing.Pool(n_peers)
	for peer, nodestr in peers.items():
		i += 1
		# create a batch for the peer to work on
		assignments[peer] = log_data[round(splits[i-1]):round(splits[i])]
		
		# Make a temp file of this assignment/batch
		rmt_batch = f'assignment_{peer.lower()}.txt'
		open(rmt_batch,'w').write('\n'.join(assignments[peer]))
		execute(f'sftp {nodestr}:/home/{nodestr.split("@")[0]}/Bakery42/ <<< $"put {rmt_batch}"',False)
		os.remove(rmt_batch)
		
		# Now tell it to start parsing
		c = f'python3 analysis.py --file {rmt_batch}'
		job = threads.apply_async(remote_execute, (nodestr, c, f'/home/{nodestr.split("@")[0]}/Bakery42/', False))
		job.get(10)
		print(f'[+] {peer} is working on {len(assignments[peer])} entries')
	
	# Now watch while they work 
	print('='*80)
	working = True
	workers = {}
	try:
		while working:
			# check in on progress every N min
			print('[-] Pausing while nodes work')
			timer(time.time(), 30, 60)
			not_working = 0
			for peer, nodestr in peers.items():
				worker_threads = get_pid(nodestr, 'analysis.py')
				if len(worker_threads) > 0:
					workers[peer] = True
					print(f'\t- {peer} has {len(worker_threads)} active threads working')
				else:
					not_working += 1
			# only stop if no peers are still working 
			working = (n_peers - not_working) > 0

	except KeyboardInterrupt:

		print('[!] Killing Workers')
		# TODO: Kill all remote PIDs
		for peer, nodestr in peers.items():
			event = threads.apply_async(get_pid, (nodestr, 'analysis.py'))
			for pid in event.get(3):
				kill_pid(nodestr, pid)
				print(f'[X] Ended {nodestr}:{pid}')
		working = False
		pass


def main():
	# Last argument shoould be the logfile to analyze
	log = todays_log_name()
	if '--file' not in sys.argv:
		for name, watching in load_nodes(os.getcwd()).items():
			if watching:
				logfile = os.path.join(os.getcwd(), name, log)
	else:
		logfile = sys.argv[-1]
	if not os.path.isfile(logfile):
		nodes, connections, watching, spotting = node_census()
		rawdata = synchronize_latest_watcher(nodes, watching)
	else:
		rawdata = open(logfile,'r').read().split('\n')

	node = logfile.split('/')[0]
	logfilename = logfile.split('/')[-1]

	distributed = False
	if '--party' in sys.argv:
		distributed = True

	if distributed:
		distributed_squat_power(logfilename, rawdata)
	else:
		solo_check_for_squatters(logfilename, rawdata)



if __name__ == '__main__':
	main()


