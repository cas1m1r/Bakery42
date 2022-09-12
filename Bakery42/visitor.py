from colorama import init, Fore
import multiprocessing
import requests
import random
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



def checkout_link(ip, domain):
	url = f"https://{domain.replace('*.','')}"
	result= {}
	try:
		ans = requests.get(url)
		ans.close()
		result['status'] = int(ans.status_code)
		result['html'] = ans.text
		result['host'] = ip
		if ans.status_code == 200:
			print(f'{fW}[+] {fG}{domain}{OFF}{fW} is viewable {fB}[{ip}]{OFF}')
		elif ans.status_code == 403:
			print(f'{fW}[+] {fR}{domain}{OFF}{fW} is unauthorized {fC}[{ip}]{OFF}')
	except:
		pass
	open(os.path.join(ip, domain),'w').write(json.dumps(result))


def explore_host(hosts, interesting):
	if not os.path.isdir(interesting):
		os.mkdir(interesting)
	threads = multiprocessing.Pool(25)
	for domain in hosts[interesting]:
		# checkout_link(interesting, domain)
		event = threads.apply_async(checkout_link, (interesting, domain))
		try:
			event.get(5)
		except multiprocessing.TimeoutError:
			print(f'{fY}[!] TimeOut waiting for {fR}{interesting} to serve {domain}{OFF}')
			pass

def main():
	
	hosts = json.loads(open('all_results_by_host.json','r').read())
	most_doms = 0
	most_interesting = ''
	
	avg = 2
	interesting = []
	for ip in hosts.keys():
		if len(ip.split('.'))>2:
			if len(hosts[ip]) > most_doms:
				most_doms = len(hosts[ip])
				most_interesting = ip
		if len(hosts[ip]) > 2:
			interesting.append(ip)
	random.shuffle(interesting)
	for ip in interesting:
		if ip != most_interesting:
			print(f'[+] Exploring the \033[1m{len(hosts[ip])}\033[0m sites hosted by \033[1m\033[31m{ip}\033[0m')
			explore_host(hosts, ip)


if __name__ == '__main__':
	main()
