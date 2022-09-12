from colorama import init, Fore
import census as distributed
import bakeryutils as utils
import multiprocessing
import numpy as np
import random
import json
import sys
import os
from workforce import *

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

def save_work(nx:Master, hosts:dict):
	finished = {}
	jobs = distribute_hostnames(nx, hosts)
	# threads = multiprocessing.Pool(len(nx.peers.keys()))
	for node in nx.nodes.values():
		finished[node.nodename] = check_work(nx, jobs, node)	
	return finished


def check_work(nx:Master, jobs:dict, node:Node):
	finished = {}
	finished[node.nodename] = {}
	# Check assignments for this node
	threads = multiprocessing.Pool(3)
	node_tasks = jobs[node]
	print(f'[>] {node.nodename} is viewing pages from {len(node_tasks.keys())} differents hosts. Saving their Work...')
	for ipaddr in node_tasks.keys():
		domains = node_tasks[ipaddr]
		domdir = os.path.join(os.getcwd(),node.nodename.upper(),ipaddr)
		if not os.path.isdir(domdir):
			os.mkdir(domdir)
		finished[node.nodename][ipaddr] = []
		for domain in domains:
			rpath = f'/home/{node.hostname}/Bakery42/{ipaddr}/{domain.replace("*.","")}'
			lpath = os.path.join(domdir, domain.replace("*.",""))
			test = threads.apply_async(distributed.rmt_file_exists, (node.nodestr, rpath))
			try:
				if test.get(5):
					print(f'\t[+] {node.nodename} finished viewing {domain} at {ipaddr}')
					distributed.get_rmt_file(node.nodestr, lpath)
					finished[node.nodename][ipaddr].append(domain)
			except multiprocessing.TimeoutError:
				print(f'[!] Error looking for {rpath} on {node.nodename}[{node.ip}]')
				pass
	return finished



def main():
	nx = Master({})
	if '--get-logs' in sys.argv:
		pull_logs(nx)	

	if '--parse-log' in sys.argv:
		print(f'Distributing Tasks...')
		if log_exists():
			distributed_viewers(sys.argv[-1])

	if '--save-work' in sys.argv:
		if log_exists():
			hosts = json.loads(open(sys.argv[-1],'r').read())
			save_work(nx, hosts)

if __name__ == '__main__':
	main()
