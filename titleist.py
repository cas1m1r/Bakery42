from colorama import init, Fore
import census as distributed
import bakeryutils as utils
import multiprocessing
import pandas as pd
import numpy as np
import random
import json
import sys
import os
from workforce import *



top1m = pd.read_csv('top-1m.csv')
TOP_DOMAINS = list(top1m[:]['DOMAIN'])[0:999]

def pull_logs(controller):
	parse_task = {}
	titlated = {}
	# check for TitleistPath (assumed to be installed in home directory)
	for peer, nodestr in controller.peers.items():
		parse_task[peer] = {'jobs':['python3 log2json.py'],'args':[],'fileout':[]}
		titleist_path = f'/home/{utils.nodestr2host(nodestr)}/Titleist/DataCollection'
		if distributed.rmt_dir_exists(nodestr, titleist_path):
			print(f'{fW}[+]{fG} {peer}{fW} has Titleist Data')
			for logfile in distributed.rmt_cmd(nodestr,f'ls /home/{utils.nodestr2host(nodestr)}/Titleist/DataCollection/squatters*'):
				fileout = f"result{logfile.split('.')[0].split('/')[-1].split('squatters')[-1]}.json"
				if controller.alive[peer] and fileout not in os.listdir(os.getcwd()):
					parse_task[peer] = {'jobs':['python3 log2json.py'],'args':[],'fileout':[]}
				parse_task[peer]['args'].append(f'{logfile}')
				parse_task[peer]['fileout'].append(fileout)
				# try to run the task....
				controller.queue = controller.determine_node_assignments(parse_task)
				controller.tasks_confirmed = controller.verify_assignments()
				controller.run_tasks(45)

			titlated[peer] = True
		else:
			titlated[peer] = False


def local_cleaning():
	for item in os.listdir(os.getcwd()):
		if len(item.split('.')) >3:
			for filename in os.path.listdir(item):
				open(os.patah.join(os.getcwd(),item,filename),'w').write('')


def distribute_hostnames(controller:Master, hosts:dict):
	n_peers = len(controller.peers.keys())
	host_per_host = round(len(hosts)/len(controller.peers.keys()))
	print(f'[+] Assinging {host_per_host} hosts per peer [{n_peers} peers]')
	splits = np.linspace(0,len(hosts),len(controller.peers.keys())+2)
	hostnames = list(hosts.keys())
	assignments = {}
	n = 0
	for bucket in range(n_peers+1):
		if n > 0:
			assignment = {}
			for node in controller.nodes.values():
				peer = node.nodename
				nodestr = node.nodestr
				localf = f'assignment_{peer}.json'
				for i in range(int(splits[n-1]),int(splits[n])):
					assignment[hostnames[i]] = hosts[hostnames[i]]
			assignments[node] = assignment
		n += 1
	return assignments

def log_exists():
	if os.path.isfile(sys.argv[-1]):
		print(f'[+] Parsing {sys.argv[-1]} and distributing among nodes')
		return True
	else:
		print(f'[!] Please provide a file to parse')
		return False


def distributed_viewers(logfile):
	hosts = json.loads(open(logfile,'r').read())

	controller = Master({})
	n_peers = len(controller.peers.keys())

	host_per_host = round(len(hosts)/len(controller.peers.keys()))
	print(f'[+] Assinging {host_per_host} hosts per peer [{n_peers} peers]')
	# split up large file and distribute to peers 
	splits = np.linspace(0,len(hosts),len(controller.peers.keys())+2)
	# have each peer explore their portions
	hostnames = list(hosts.keys())
	assignments = {}
	n = 0
	for bucket in range(n_peers+1):
		if n > 0:
			# assignments[controller.peers.keys()[n-1]]= hosts[int(splits[n-1]):int(splits[n])]
			node = list(controller.peers.keys())[n-1]
			nodestr = controller.peers[node].split('@')[0]
			localf = f'assignment_{node}.json'
			assignment = {}
			for i in range(int(splits[n-1]),int(splits[n])):
				assignment[hostnames[i]] = hosts[hostnames[i]]
			open(f'{localf}','w').write(json.dumps(assignment))
			print(f'[+] Giving {node} {int(splits[n])-int(splits[n-1])} hosts')
			distributed.put_rmt_file(controller.peers[node], localf,f'/home/{nodestr.split("@")[0]}/Bakery42')
			distributed.put_rmt_file(controller.peers[node], 'visitor.py',f'/home/{nodestr.split("@")[0]}/Bakery42')
			assignments[node] = assignment
		n += 1
	return assignments


def save_work(nx):
	# for each node list all logs 
	# grab any dont already have 
	print('saving work...')
	lfiles= {}
	threads = multiprocessing.Pool(64)
	
	NODES  = list(nx.nodes.keys())
	random.shuffle(NODES)
	for peer in NODES:
		node = nx.nodes[peer]
		ipaddrs = []
		lfiles[peer] = os.listdir(os.path.join(os.getcwd(),peer.upper()))
		for elmt in utils.rmt_cmd(node.nodestr, f'ls /home/{node.hostname}/Bakery42'):
			if len(elmt.split('.')) > 3:
				ip = os.path.join('/home',node.hostname,'Bakery42',elmt)
				rfiles = utils.rmt_cmd(node.nodestr, f'ls {ip}')
				N = len(rfiles)
				ii = 0
				random.shuffle(rfiles)
				for domain in rfiles:
					ii += 1
					
					if domain not in os.listdir(peer) and len(list(domain)) > 3:
						rpath = os.path.join('/home',node.hostname,'Bakery42',elmt,domain)
						lpath = os.path.join(os.getcwd(),peer.upper(),domain)
						# distributed.get_rmt_file(node.nodestr,lpath, rpath)
						ftransfer = threads.apply_async(distributed.get_rmt_file, (node.nodestr,lpath, rpath))
						try:
							bytes_transferred = ftransfer.get(2)
							# print(f'{fR}[+]{fY} Downloaded {fB}{bytes_transferred}bytes [{domain}]{OFF}')
							lfiles[peer].append(domain)
						except multiprocessing.TimeoutError:
							print(f'{fR}[X] Error Getting {fY}{domain}{fR} data{OFF}')
							pass
					else:
						print(f'{fG}[-]{fW} Already have {fG}{domain}{fW} data skipping...{OFF}')
						# empty_file = f'echo "" > {os.path.join(rpath)}'
						# distributed.rmt_cmd(node.nodestr, empty_file)
						os.system('rm *.txt')

def consolidate_log(squatfile,verbose=True):
	data = {}
	try:
		results = json.loads(open(squatfile,'r').read())
		for entry in results['entries']:
			ip = entry['ip_address']
			domain = entry['site_registered']
			print(f'{fG}{domain}{fW} is hosted at {fC}{ip}{OFF}')
			if ip not in list(data.keys()) and len(ip.split('.'))>3:
				data[ip] = [domain]
			elif len(ip.split('.'))>3:
				data[ip].append(domain)
	except json.decoder.JSONDecodeError:
		print(f'[X] Unable to parse {squatfile}')
		pass                           
	return data


def combine_logs():
	if not os.path.isdir(os.path.join(os.getcwd(),'LOGS')):
		print(f'[!] Missing LOGS folder, nothing to do')
		exit()
	domaindata = {}
	n_domains = 0
	for filename in os.listdir('LOGS'):
		logdata = consolidate_log(os.path.join(os.getcwd(),'LOGS',filename))
		for ip in logdata.keys():
			if ip not in domaindata.keys():
				domaindata[ip] = []
			for domain in logdata[ip]:
				if domain not in domaindata[ip]:
					domaindata[ip].append(domain)
					n_domains += 1
	print(f'[>]{fY}COMPLETED{OFF}')
	print(f'[-]{fC}{len(list(domaindata.keys()))}{fW} IPs logged hosting {fR}{n_domains} domains{OFF}')
	return domaindata



def levenshtein(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros ((size_x, size_y))

    # Trying to make this a bit faster
    matrix[:,0] = list(range(size_x))
    matrix[0,:] = list(range(size_y))

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix [x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix [x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    return matrix[size_x - 1, size_y - 1]



def spot_a_squat(domain):
	victim = ''
	squatting = False
	for legit in TOP_DOMAINS:
		if 3 >= levenshtein(domain, legit) > 0:
			victim = legit
			squatting = True
			break
	return squatting, victim


def local_power_squat(logfile):
	if not os.path.isfile(logfile):
		print(f'[!] Cannot find {logfile}')
		return False
	squatters = []
	log = json.loads(open(logfile,'r').read())
	threads = multiprocessing.Pool(64)
	print(f'[$] Checking for Bitsquatters in {logfile}')
	hosters = list(log.keys())
	random.shuffle(hosters)
	n_processed = 0

	for ipaddr in hosters:
		print(f'\t->{fW}\033[1m Checking if {fG}{ipaddr} {fW}hosts any Bitsquatters...{fC}[{len(log[ipaddr])} domains]{OFF}')
		for domain in log[ipaddr]:
			if len(domain) < 42: # checked list and this would automatically disqualify top 1k domains
				squat = threads.apply_async(spot_a_squat, (domain,))
				try:
					squatting, victim = squat.get(5)
					n_processed += 1
					if squatting:
						print(f'\t\t{fR} {domain} {fW}[similar to {legit}?]{OFF}')
						squatters.append(victim)
				except:
					print(f'{fR}[X] Error Processing:{fB}{domain}{OFF}')
					pass
			else:
				print(f'{fY}[~]{fW} Skipping over {fC}{domain}{fW}{OFF}')
			if n_processed > 1 and n_processed%100:
				print(f'{fW}[#]{fG} {n_processed} domains have been examined.')
	return squatters 


def local_cleaning(nx):
	for nodedir in nx.peers.keys():
		for item in os.listdir(nodedir):
			open(os.path.join(nodedir,item),'w').write('')


def main():
	if '--local-squat' in sys.argv:
		open(f'possible_squats.json','w').write(json.dumps({'squatters':local_power_squat(sys.argv[-1])}))
		exit()

	nx = Master({})
	

	if '--parse-log' in sys.argv:
		print(f'Distributing Tasks...')
		if log_exists():
			distributed_viewers(sys.argv[-1])

	elif '--combine-logs' in sys.argv:
		data_out = combine_logs()
		if os.path.isfile('all_results_by_host.json'):
			# Warn user this would overwrite existing
			os.system('mv all_results_by_host.json older_results_by_hosts.json')
		open('all_results_by_host.json','w').write(json.dumps(combine_logs(),indent=2))

	elif '--get-logs' in sys.argv:
		pull_logs(nx)	

	elif '--save-work' in sys.argv:
		if log_exists():
			hosts = json.loads(open(sys.argv[-1],'r').read())
			save_work(nx)

	elif '--clean-local' in sys.argv:
		local_cleaning(nx)


if __name__ == '__main__':
	main()
