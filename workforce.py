import census as distributed
import bakeryutils as utils
import multiprocessing
from analysis import *



class Master:
	def __init__(self, node_program_config):
		self.peers = self.load_nodes()
		self.alive = self.whos_there()
		if node_program_config == {}:
			node_program_config = self.generate_test_task()
		# Now read the program_config to determine what each node should be doing
		self.queue = self.determine_node_assignments(node_program_config)
		# Probably shoudl do some verification of paths present, files/libs needed to run the tasks
		self.tasks_confirmed = self.verify_assignments()
		# Run all tasks on each node
		self.run_tasks(self.tasks_confirmed, self.queue)

	def load_nodes(self):
		return distributed.load_nodes(os.getcwd())

	def whos_there(self):
		return distributed.test_connections(self.peers)

	def are_peers_running(self, program):
		are_running = {}
		for peer, nodestr in self.peers.items():
			if distributed.is_running(nodestr, program):
				are_running[peer] = True
			else:
				are_running[peer] = False
		return are_running

	def determine_node_assignments(self, config):
		assignments = {}
		for node_name in config.keys():
			# Get target program name to run on remote node 
			if 'jobs' in config[node_name].keys():
				target_program = config[node_name]['jobs'].pop(0)
				target_args = config[node_name]['args'].pop(0)
			else:
				print(config[node_name])
				print(f'{fB}{fR}[X]{fE}{fB} No job present for {fR}{node_name}{fE}. Moving on...')
				continue
			# check if node is online
			if self.alive[node_name]:
				# insert assignment from the configration for this node 
				assignments[node_name]= {'jobs': [target_program, target_args]}
			else:
				print(f'{fB}{fR}[X] {fE}{fB}Cannot run {target_program} on {node_name} because {node_name} is offline')
		return assignments

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
				target_program = self.queue[peer]['jobs'][0]
				# Determine if the target program is on this local machine (master) or on the remote node
				isLocal = False
				isRemote = False
				if not os.path.isfile(target_program):
					print(f'{fY}[?] {fW}Job {fR}{target_program}{fW} is not locally present, checking {peer}')
				else:
					isLocal = True
					verified[peer] = [True, 'local']
					continue
				# Make sure node has target job
				rpath  = os.path.join(bakery_location(self.peers[peer]), target_program.split(' ')[-1])
				if distributed.rmt_file_exists(self.peers[peer], rpath):
					print(f'[+] {fG}{peer}{fW} has {fB}{target_program}{fW} to run')
					isRemote = True
					verified[peer] = [True, 'remote']
					continue
				if not isLocal and not isRemote:
					print(f'{fB}{fR}[!] Error{fE}{fB}: {fW}{peer}{fY} cannot run job because {target_program} doesnt exist anywhere{fW}')
			# If program is on both machines, prefer the remote one?
		print(f'Jobs Verified:\n\033[2m{verified}\033[0m')
		return verified


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


	def run_tasks(self, confirmed, jobs):
		print(f'{fG}[~] {fW}Running jobs...')
		print(f'\033[2m{jobs}\033[0m')
		
		threads = multiprocessing.Pool(len(self.peers.keys()))
		for peer, nodestr in self.peers.items():
			program = f'{self.queue[peer]["jobs"][0].split(" ")[0]} {bakery_location(nodestr)}/{self.queue[peer]["jobs"][0].split(" ")[-1]}'
			job = threads.apply_async(distributed.rmt_cmd, (nodestr, program))
			job.get(2)
		print('Waiting for machines to work...')
		
		# Now look for result.txt
		# TODO: should continue to look while they work
		for peer,nodestr in self.peers.items():
			if distributed.rmt_file_exists(nodestr, f'/home/{nodestr.split("@")[0]}/result.txt'):
				print(f'{fR}[>] {fW}{peer}{fG}  sucessfully completed {fG} test program, getting results')
				job2 = threads.apply_async(get_test_results, (peer, nodestr))
				job2.get(3)
				

def get_test_results(peer, nodestr):
	if not os.path.isdir(peer.upper()):
		os.mkdir(peer.upper())
	rpath = f'/home/{nodestr.split("@")[0]}/result.txt'
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

if __name__ == '__main__':
	main()