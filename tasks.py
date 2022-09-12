import json
import sys
import os

class Task:
	def __init__(self,conf={}):
		self.job = ''
		self.args = ''
		self.fileout = ''
		self.unemployed = self.check_config(conf)
		if self.unemployed:
			self.add_assignment(conf)

	def check_config(self, config):
		if config == {}:
			# alowed to have empty config, but return empty items
			return True
		else:
			return False

	def add_assignment(self, taskconf):
		if 'jobs' in taskconf.keys():
			self.job = taskconf['job']
		if 'args' in taskconf.keys():
			self.args = taskconf['args']
		if 'fileout' in taskconf.keys():
			self.fileout = taskconf['fileout']


