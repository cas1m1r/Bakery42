from bakeryutils import create_timestamp
import multiprocessing
import json
import sys
import os



def parse_entry(line):
	try:
		fields = line.split(' ')
		ldate = fields[0].replace('[','')
		ltime = fields[1].replace(']','')
		site = fields[2]
		ipv4 = fields[-1]
	except:
		return False, {}
	return True, {'date_registered': [ldate,ltime], 'site_registered':site,'ip_address': ipv4}
	
if __name__ == '__main__':

	if not os.path.isdir(f'/home/{os.getlogin()}/Bakery42/results'):
		os.mkdir(f'/home/{os.getlogin()}/Bakery42/results')

	if len(sys.argv) > 1:
		logfile = sys.argv[-1]
	else:
		ld, lt = create_timestamp()
		print(f'squatters{"%02d" % int(ld.split("/")[0])}{ld.split("/")[1]}{ld.split("/")[-1][-2:]}.txt')
		exit()
	logdata = {'entries':[]}
	threads = multiprocessing.Pool(10)
	for entry in open(logfile,'r').read().split('\n'):
		parse = threads.apply_async(parse_entry, (entry,))
		parsed, data = parse.get(1)
		if parsed:
			logdata['entries'].append(data)
	# dump results
	result = f"result{logfile.split('.')[0].split('/')[-1].split('squatters')[-1]}.json"
	open(f'{result}','w').write(json.dumps(logdata,indent=2))
