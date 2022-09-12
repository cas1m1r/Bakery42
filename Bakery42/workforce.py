from colorama import init, Fore
import census as distributed
import bakeryutils as utils
import multiprocessing
from tasks import Task
from node import Node
import json
import time
import sys
import os


fB = Fore.LIGHTBLUE_EX
fR = Fore.RED
fW = Fore.WHITE
fM = Fore.MAGENTA
fC = Fore.CYAN
fG = Fore.GREEN
fY = Fore.YELLOW
fE = fW
OFF = '\033[0m'

class Master:
	def __init__(self, config={}):
		# Load nodes from configuration
		self.peers = self.load_nodes()
		# Check which are active 
		self.alive = self.whos_there()
		# Create folders for each node (easier for tracking file transfers while multithreading)
		self.generate_peer_folders()
		# Check if a configuration was given
		if config == {}:
			self.queue = []
			self.tasks_confirmed = {}
		else:
			self.queue = self.determine_node_assignments(config)
			self.tasks_confirmed = self.verify_assignments()	
		# Create Nodes
		self.nodes = {}
		self.fileowners = {}
		for name, label in self.peers.items():
			self.nodes[name] = Node(label, name)
		# Run all tasks on each node
		
		# self.run_tasks()


	def generate_peer_folders(self):
		for peer, nodestr in self.peers.items():
			# only bothering to make folders for live peers for now
			if self.alive[peer]:
				if not os.path.isdir(os.path.join(os.getcwd(),peer)):
					os.mkdir(os.path.join(os.getcwd(),peer))


	def load_nodes(self):
		return distributed.load_nodes(os.getcwd())

	def whos_there(self):
		return distributed.test_connections(self.peers)

	def determine_node_assignments(self, config):
		assignments = {}
		for node_name in config.keys():
			# Get target program name to run on remote node 
			if 'jobs' in config[node_name].keys():
				target_program = config[node_name]['jobs']
				target_args = config[node_name]['args'][0]
				print(f'{target_program} {target_args}')
			else:
				print(config[node_name])
				print(f'{fB}{fR}[X]{fE}{fB} No job present for {fR}{node_name}{fE}. Moving on...')
				continue
			# check if node is online
			if self.alive[node_name]:
				# insert assignment from the configration for this node 
				assignments[node_name]= [config[node_name]['jobs'], target_args] 
			else:
				print(f'{fB}{fR}[X] {fE}{fB}Cannot run {target_program} on {node_name} because {node_name} is offline')
		return config

	def verify_assignments(self):
		"""
		jobs = { 
				 'NODE1': { 
				 			'jobs': ['python3 test.py', 'python3 -m http.server']
							'args' ['', '4242']
							'run_path': ['/home/pi/Bakery42','/home/pi/Bakery42']
						  }
			   }
		This is an example of a node configuration telling NODE1 to run test.py, and when it's done
		run a http server using buitin python module on port 4242 out of the same path
		"""
		print(f'[-] Verifying Jobs:')
		verified = {}
		# check that the remote node will be able to complete assignment before giving it
		for peer in self.queue.keys():
			if 'jobs' in self.queue[peer].keys():
				verified[peer] = [False, '']
				# Parse the input program and args for different kinds of input 
				target_program = self.queue[peer]['jobs'][0].split(' ')[-1]
				args = self.queue[peer]['jobs'][-1]

				if 'fileout' not in self.queue[peer].keys():
					self.queue[peer]['fileout'] = ''
				
				# Determine if the target program is on this local machine (master) or on the remote node
				isLocal = False
				isRemote = False
				nodestr = self.peers[peer]
				if not os.path.isfile(target_program):
					print(f'{fY}[?] {fW}Job {fR}{target_program}{fW} is not locally present, checking {peer}')
				else:
					isLocal = True
					distributed.put_rmt_file(nodestr, target_program, f"{bakery_location(nodestr).split('@')[0]}/")
					verified[peer] = [True, 'local']
					continue
				# Make sure node has target job
				rpath  = os.path.join(bakery_location(nodestr), target_program.split(' ')[-1])
				if distributed.rmt_file_exists(nodestr, rpath):
					print(f'[+] {fG}{peer}{fW} has {fB}{target_program}{fW} to run')
					isRemote = True
					verified[peer] = [True, 'remote']
					continue
				if not isLocal and not isRemote:
					print(f'{fB}{fR}[!] Error{fE}{fB}: {fW}{peer}{fY} cannot run job because {target_program} doesnt exist anywhere{fW}')
			# If program is on both machines, prefer the remote one?
		print(f'Jobs Verified:\n\033[2m{verified}\033[0m')
		return verified


	def job_parser(self, peer):
		execution_strings = []
		n_jobs = len(self.queue[peer]['jobs'])
		print(f'[+] {peer} has {n_jobs} jobs to parse...')
		for jobid in range(n_jobs):
			program = self.queue[peer][jobid]
			args = self.queue[peer][jobid]
			if len(program.split(' ')) > 1:
				# A first binary operates on a second: python3 /home/node/Bakery42/test.py 
				command = f'{bakery_location(self.peers[peer])}/{program}'
			else:
				# Its an executable itself like ./home/node/Bakery42/compiledCode
				command = f'{bakery_location(self.peers[peer])}/{program}'
			execution_strings.append(command)
		return execution_strings

	def generate_test_task(self):
		# Now Create test.py for them 
		basic_file  = 'import os, sys, bakeryutils as butils\n' # should be able to check import statements...
		basic_file += 'ldate, ltime = butils.create_timestamp()\nmsg = f'
		basic_file += '"Test file {sys.argv[0]} was run on {ldate} at {ltime}"\n'
		basic_file += 'open("result.txt","w").write(msg)\n'
		open('test.py', 'w').write(basic_file)

		jobs = {}
		tasks_distributed = {}
		self.alive = self.whos_there()
		for peer, nodestr in self.peers.items():
			if self.alive[peer]:
				jobs[peer] = {'jobs': ['python3 test.py'],
							  'args': ['']}
				tasks_distributed[peer] = distributed.rmt_file_exists(nodestr, f'/home/{nodestr.split("@")[0]}/test.py')
				if not tasks_distributed[peer]:
					utils.rmt_cmd(nodestr, f'mkdir /home/{nodestr.split("@")[0]}/Bakery42')
					if not distributed.put_rmt_file(nodestr,'bakeryutils.py', f'{bakery_location(nodestr.split("@")[0])}'):
						print(f'{fY}[?] Utils library file May have failed to transfer\033[0m')
					if not distributed.put_rmt_file(nodestr,'test.py', f'{bakery_location(nodestr.split("@")[0])}'):
						print(f'{fY}[?] Test File May have failed to transfer\033[0m')
		return jobs

	def test_network(self):
		node_program_config = self.generate_test_task()
		# Now read the program_config to determine what each node should be doing
		self.queue = self.determine_node_assignments(node_program_config)
		# Probably shoudl do some verification of paths present, files/libs needed to run the tasks
		self.tasks_confirmed = self.verify_assignments()
		self.run_tasks()

	def whos_running(self, program):
		workers = {}
		for peer, nodestr in self.peers.items():
			if distributed.is_running(nodestr, program):
				workers[peer] = True 
			else:
				workers[peer] = False
		return workers

	# TODO: This is too chunky, clean it up!
	def run_tasks(self, estimated_completion_time=1):
		print(f'{fG}[~] {fW}Running jobs...')
		print(f'\033[2m{self.queue}\033[0m')
		confirmed = self.tasks_confirmed
		jobs = self.queue
		# PT 1. Distributed Tasks
		# Give the nodes the program/files needed to complete the task, and execute it
		threads = multiprocessing.Pool(len(self.peers.keys()))
		for peer, hasJob in self.tasks_confirmed.items():
			if hasJob:
				nodestr = self.peers[peer]
				program = f'{self.queue[peer]["jobs"][0].split(" ")[0]} {bakery_location(nodestr)}/{self.queue[peer]["jobs"][0].split(" ")[-1]} '
				if len(self.queue[peer]['args'])>=1:
					program += f"{' '.join(self.queue[peer]['args'])}"
				
				print(f'{fB} Executing:\n{fW}{program}')
				job = threads.apply_async(distributed.rmt_cmd, (nodestr, program))
				try:
					job.get(estimated_completion_time)
				except multiprocessing.TimeoutError:
					print(f'[!] Timeout Waiting for reply from {peer}')
					pass
				self.queue[peer]["jobs"].pop(0) # clear the que because the job ran
		# PT 2. Get the Results 
		# Not all jobs will take same amount of time, and if running across several machines
		# simulatneously they will finish at different times too
		print('Waiting for machines to work...')
		time.sleep(1)
		# Now look for result.txt
		# TODO: should continue to look while they work
		for peer, hasJob in self.tasks_confirmed.items():
			if hasJob:
				waiting_for_results = False 
				while not waiting_for_results:
					# check if fileout exists
					if len(self.queue[peer]["fileout"]):
						fout = f'/home/{self.peers[peer].split("@")[0]}/{self.queue[peer]["fileout"][0]}'
						localf = self.queue[peer]["fileout"][0]
					else:
						fout = 'result.txt'
						localf = fout
					print(f'[?] Waiting for output file {fout}')
					# check if the output file is there
					waiting_for_results = distributed.rmt_file_exists(self.peers[peer], fout)

					#
				distributed.get_rmt_file(self.peers[peer], os.getcwd(), fout)
				print('RESULT:\n')
				print(open(localf,'r').read())


	def run(self, estimated_run_time=5):
		print(f'{fG}[~] {fW}Running jobs on all {len(self.nodes.keys())} peers...')
		threads = multiprocessing.Pool(10)
		for peer, node in self.nodes.items():
			if self.alive[peer] and not node.unemployed:
				print(f'{fY}[+]{fG}{peer}{fW} has a job to run{OFF}')
				# Check the task will work (files present, etc. )
				if node.verify_task:
					# Run the task
						cmd_str = node.build_command()
						print(f'{fB} Executing:\n{fW}{node.task["job"]}{fE}')
						job = threads.apply_async(distributed.rmt_cmd, (node.nodestr, cmd_str))
						try:
							job.get(estimated_run_time)
						except multiprocessing.TimeoutError:
							print(f'[!] Timeout Waiting for reply from {peer}')
							pass


def get_test_results(peer, nodestr, fileout='result.txt'):
	if not os.path.isdir(peer.upper()):
		os.mkdir(peer.upper())
	rpath = f'/home/{nodestr.split("@")[0]}/{fileout}'
	distributed.get_rmt_file(nodestr, os.path.join(os.getcwd(), peer.upper()),rpath)
	os.system(f'mv result.txt {peer.upper()}')
	print(open(f'{peer.upper()}/result.txt','r').read())


def bakery_location(nodestr):
	return f'/home/{nodestr.split("@")[0]}/Bakery42'


def transfer_project_files(nodestr):
	threads = multiprocessing.Pool(4)
	node = nodestr.split("@")[0]
	utils.rmt_cmd(nodestr, f'mkdir /home/{node}/Bakery42')
	utils.rmt_cmd(nodestr, f'mkdir /home/{node}/Bakery42')
	for file in os.listdir(os.getcwd()):
		event = threads.apply_async(utils.execute, (f'sftp {nodestr}:/home/{node}/Bakery42/ <<< $"put {file}"',False))
		event.get(60)

def enable_all_nodes(nodes):
	for node in nodes.keys():
		nodestr = nodes[node]
		transfer_project_files(nodestr)


def kill_all_workers(peers):
	threads = multiprocessing.Pool(len(peers.keys()))
	for peer, nodestr in peers.items():
		event = threads.apply_async(get_pid, (nodestr, 'analysis.py'))
		for pid in event.get(3):
			distributed.kill_pid(nodestr, pid)
			print(f'[X] Ended {nodestr}:{pid}')

def destroy_bakery(peers):
	threads = multiprocessing.Pool(len(peers.keys()))
	for peer, nodestr in peers.items():
		event = threads.apply_async(utils.rmt_cmd, (nodestr, f'rm -rf {bakery_location(nodestr)}'))
		event.get(1)
			

def main():
	if '--kill' in sys.argv:
		kill_all_workers(distributed.load_nodes(os.getcwd()))

	if '--clean' in sys.argv:
		destroy_bakery(distributed.load_nodes(os.getcwd()))
	else:
		controller = Master({})
		# controller.test_network()
		if '--query-nodes' in sys.argv:
			print(json.dumps(distributed.cmd_all_peers(controller.peers, ' '.join(sys.argv[2:])),indent=2))

		if '--whos-running' in sys.argv:
			print(json.dumps(controller.whos_running(sys.argv[-1]), indent=2))


if __name__ == '__main__':
	main()