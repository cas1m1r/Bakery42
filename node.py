from colorama import init, Fore, Style
import census as distributed
from tasks import Task
import os

fB = Fore.LIGHTBLUE_EX
fR = Fore.RED
fW = Fore.WHITE
fM = Fore.MAGENTA
fC = Fore.CYAN
fG = Fore.GREEN
fY = Fore.YELLOW
fE = '\033[0m'
OFF = Fore.RESET

class Node:
	def __init__(self, nodestr, peername):
		self.hostname, self.ip = self.setup(nodestr, peername)
		self.unemployed = True # Intiially nodes have no tasks
		self.nodename = peername
		self.nodestr = nodestr
		# Nodes can have files 
		self.files = {}
		# Nodes can run tasks
		self.tasks = {}

	def setup(self, label, name):
		localdir = os.path.join(os.getcwd(), name.upper())
		if not os.path.isdir(localdir):
			os.mkdir(localdir)
		return label.split('@')[0], label.split('@')[1]


	def add_file(self, filename):
		if filename not in self.files.keys():
			self.files[filename] = filename

	def add_task(self, job):
		# Rebuild the task checking each field of submitted job to be sure its all good
		task = {}
		# Check that job has correct fields
		if 'job' in job.keys():
			task['job'] = job['job'] # check if the program exists on Node?
			if len(job['job'][0].split(' ')) > 1:
				# two part command name like python3 ex.py, or bash script.sh
				binfile = job['job'][0].split(' ')[0]
				exe = job['job'][0].split(' ')[1]
			else:
				exe = job['job'][0]
			if not distributed.rmt_file_exists(self.nodestr, exe):
				print(f'{Fore.LIGHTRED_EX}[!] {fR}Warning: The remote file {exe} isnt on {self.nodestr}{OFF}')
			# else:
			# 	print(f'{Fore.LIGHTGREEN_EX}[>]{fG}{self.hostname}{fW} will be running {fB}{exe}{fE}')
		else:
			print(f'{Fore.LIGHTRED_EX}[!]{fR} Missing job title! Will not run...{fE}')
		if 'args' in job.keys():
			task['args'] = job['args']
		if 'fileout' in job.keys():
			task['fileout'] = job['fileout']
			# TODO: Maybe double check this isnt something we already have?
		self.unemployed = False
		return task


	def build_command(self):
		if 'job' not in self.tasks.keys():
			print(f'{Fore.LIGHTRED_EX}[X]{fR}No Job Configured!{fE}')
		prog = self.tasks['job']
		args = ' '.join(self.tasks['args'])
		output = self.tasks['fileout']
		return f'{progr} {args}'

	def verify_task(self):
		if len(self.tasks['job'].spllit(' ')) <= 1:
			binary = self.tasks['job']
		else:
			binfile = self.tasks['job'].split(' ')[0]
			exe = self.tasks['job'].split(' ')[1]
			if not os.path.isfile(exe):
				return False
		if not os.path.isfile(binary):
			return False
		else:
			return True
