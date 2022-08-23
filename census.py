import multiprocessing
from bakeryutils import *
import dotenv
import sys 
import re
import os

def check_node_str(nodestr):
	return len(nodestr.split('@')) >=2

def load_nodes(path):
	# Input: 	path	[type str("/path/to/.env")]
	# Output:	nodes 	[type dict{names:host@ipaddr}]
	if os.path.isfile(os.path.join(os.getcwd(),'.env')):
		dotenv.load_dotenv()
		nodes = {}
		for item in os.environ.keys():
			if item.find('NODE') >=0:
				nodes[item] = os.environ[item]
	else:
		print('[!] Missing .env file')
		exit()
	return nodes

def test_connections(nodes, n_threads=5,verbose=True):
	connected = {}
	pool = multiprocessing.Pool(n_threads)
	for name, addr in nodes.items():
		event = pool.apply_async(test_ssh, (addr,))
		try:
			if event.get(3):
				if verbose:	print(f'[+] {name} is connected')
				connected[name] = True
			else:
				connected[name] = False
		except multiprocessing.TimeoutError:
			connected[name] = False
			if verbose:	print(f'[-] {name} is NOT connected')
			pass
	return connected

def test_ssh(fulladdr):
	# Input : 	fulladdr 	[type str("host@ipaddr")]
	# Output:	result		[type bool(canSSH)]
	ans = rmt_cmd(fulladdr, 'id')[0]
	result = False
	try:
		if ans.split(')')[0].split('(')[1]==fulladdr.split('@')[0]:
			result = True
	except IndexError:
		pass
	return result

def make_node_dir(nodes, nodestr):
	if not check_node_str(nodestr):
		print(f'[!] Invalid node {nodestr}')
		exit()
	elif not os.path.isdir(nodes):
		os.mkdir(nodes.upper())

def put_rmt_file(nodestr, localpath, remotepath):
	execute(f'sftp {nodestr}:{remotepath} <<< $"put {localpath}"', False)
	return os.path.getsize(localpath)

def get_rmt_file(nodestr, localpath, remotepath):
	execute(f'sftp {nodestr}:{remotepath} <<< $"get {localpath}"', False)
	return os.path.getsize(localpath)


# TODO: hardcoding makes this one specific to the Titleist Project, but could be generalized
def pull_rmt_log(name, nodestr, log):
	make_node_dir(name, nodestr)
	node = nodestr.split('@')[0]
	# print(f'sftp {nodestr}:/home/{node}/Titleist/DataCollection/ <<< $"get {log}"')
	execute(f'sftp {nodestr}:/home/{node}/Titleist/DataCollection/ <<< $"get {log}"',False)
	os.system(f'mv {log} {name}')
	return os.path.getsize(os.path.join(name, log))

# TODO: hardcoding makes this one specific to the Titleist Project, but could be generalized
def check_for_logs(name, nodestr):
	print(f'[+] Pulling logs from {name}')
	node = nodestr.split('@')[0]
	threads = multiprocessing.Pool(4)
	transferred = []
	for filefound in local_cmd(f'ssh {nodestr} ls /home/{node}/Titleist/DataCollection/',False):
		if filefound.find('squatters') >= 0 and not os.path.isfile(os.path.join(os.getcwd(),name,filefound)):
			print(f'\t- grabbing {filefound}')
			sftp = threads.apply_async(pull_rmt_log, (name, nodestr, filefound))
			try:
				nbytes_transferred = sftp.get(5)
				print(f'\t- grabbed {filefound} [{nbytes_transferred/1000} KB]')	
				transferred.append(filefound)
			except multiprocessing.TimeoutError:
				pass
		elif os.path.isfile(os.path.join(os.getcwd(),name,filefound)):
			print(f'\t--> Already have {filefound}')
	return transferred

def is_watching(nodestr):
	cmd = 'ps aux | grep watcher.py'
	result = rmt_cmd(nodestr,cmd)
	if result.pop(0).find('watcher.py') > 0:
		return True
	else:
		return False

def is_spotting(nodestr):
	cmd = 'ps aux | grep spotasquat.py '
	result = rmt_cmd(nodestr, cmd)
	if result.pop(0).find('spotasquat.py') > 0:
		return True
	else:
		return False	

def is_running(nodestr, process):
	# generalized form of the two functions above for any process name
	result = rmt_cmd(nodestr, f'ps aux | grep {process}')
	if result.pop(0).find(process) > 0:
		return True
	else:
		return False

def get_pid(nodestr, program):
	res = local_cmd(f"ssh {nodestr} ps aux | grep {program}",False)
	pids = []
	for line in res:
		try:
			pid = pull_pid(nodestr,line)
			if pid > 0:
				pids.append(pid)
		except:
			pass
	return list(set(pids))


def pull_pid(nodestr, line):
	isnext = False
	pid = -1
	for item in line.split(' '):
		if isnext and len(item):
			pid = int(item)
			break
		if item == nodestr.split('@')[0]:
			isnext = True
	return pid 

def pause_pid(nodestr, program):
	pids = get_pid(nodestr, program)
	cmd = 'kill -PAUSE '
	for pid in pids:
		if pid>0:
			cmd += f'{pid} '
	rmt_cmd(nodestr, cmd)	
	

def resume_pid(nodestr, program):
	pids = get_pid(nodestr, program)
	cmd = 'kill -CONT '
	for pid in pids:
		if pid>0:
			cmd += f'{pid} '
	rmt_cmd(nodestr, cmd)	


def kill_pid(nodestr, program):
	pids = get_pid(nodestr, program)
	cmd = 'kill -9 '
	for pid in pids:
		if pid>0:
			cmd += f'{pid} > /dev/null >2&1'
	rmt_cmd(nodestr, cmd)	

def todays_log_name():
	ld, lt = create_timestamp()
	return f'squatters{"%02d" % int(ld.split("/")[0])}{ld.split("/")[1]}{ld.split("/")[-1][-2:]}.txt'

def rmt_file_exists(nodestr, remotepath):	
	return int(local_cmd(f'ssh {nodestr} test -f {remotepath};echo $?',True).pop(0)) == 0

def rmt_dir_exists(nodestr, remotepath):
	return int(rmt_cmd(nodestr, c).pop(0)) == 0

# TODO: This is prone to error, take a look at refactoring
def synchronize_latest_watcher(nodes, watching):
	found = False
	latest_log_data = ''
	for node in watching.keys():
		[isWatching, pids] = watching[node]
		if isWatching:
			print(f'{node} is running watcher.py, parsing live data')
			logname = todays_log_name()
			if os.path.isfile(os.path.join(os.getcwd(), node, logname)):
				print(f'Already have a recent copy of {logname}')
			else:
				nodestr = nodes[node]
				pull_rmt_log(node, nodestr, logname)
			latest_log_data = open(os.path.join(os.getcwd(), node, logname),'r').read().split('\n')
			print(f'[+] Parsing {len(latest_log_data)} entries from {logname}')
			found = True
	if not found:
		print('[!] No nodes watching right now...')
		# TODO: Starting watcher on one of the nodes
	return latest_log_data


def syncronize_peers():
	nodes = load_nodes(os.getcwd())


def node_census():
	nodes = load_nodes(os.getcwd())
	connections =  test_connections(nodes)
	watching = {}
	spotting = {}
	for name, isConnected in connections.items():
		if isConnected:
			# check if node is actively running the code to monitor domain registrations
			watching[name] = [is_watching(nodes[name]), get_pid(nodes[name], 'watcher.py')]
			spotting[name] = [is_spotting(nodes[name]), get_pid(nodes[name], 'spotasquat.py')]
			# download any logs of domain regstrations
			files_downloaded = check_for_logs(name, nodes[name])
			print(f'[+] {len(files_downloaded)} files downloaded from {name}')
	return nodes, connections, watching, spotting



