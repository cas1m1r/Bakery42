>>> from workforce import *
>>> task = {'NODE1':{'jobs':['python3 log2json.py'],'args':['squatters081122.txt'],'fileout':['result.json']}}
>>> 


















>>> master = Master();
[+] NODE1 is connected
[+] NODE2 is connected
[+] NODE3 is connected
[+] NODE4 is connected
[~] Running jobs...
[]
Waiting for machines to work...
>>> master.test_network()
[+] NODE1 is connected
[+] NODE2 is connected
[+] NODE3 is connected
[+] NODE4 is connected
mkdir: cannot create directory ‘/home/pi/Bakery42’: File exists
Connected to 10.13.33.102.
Connected to 10.13.33.102.
mkdir: cannot create directory ‘/home/pi/Bakery42’: File exists
Connected to 10.13.33.100.
Connected to 10.13.33.100.
mkdir: cannot create directory ‘/home/pi/Bakery42’: File exists
Connected to 10.13.33.110.
Connected to 10.13.33.110.
mkdir: cannot create directory ‘/home/pi/Bakery42’: File exists
Connected to 10.13.33.108.
Connected to 10.13.33.108.
['python3 test.py'] 
['python3 test.py'] 
['python3 test.py'] 
['python3 test.py'] 
[-] Verifying Jobs:
Connected to 10.13.33.102.
Connected to 10.13.33.100.
Connected to 10.13.33.110.
Connected to 10.13.33.108.
Jobs Verified:
{'NODE1': [True, 'local'], 'NODE2': [True, 'local'], 'NODE3': [True, 'local'], 'NODE4': [True, 'local']}
[~] Running jobs...
{'NODE1': {'jobs': ['python3 test.py'], 'args': [''], 'fileout': ''}, 'NODE2': {'jobs': ['python3 test.py'], 'args': [''], 'fileout': ''}, 'NODE3': {'jobs': ['python3 test.py'], 'args': [''], 'fileout': ''}, 'NODE4': {'jobs': ['python3 test.py'], 'args': [''], 'fileout': ''}}
 Executing:
python3 /home/pi/Bakery42/test.py /home/pi/Bakery42/
 Executing:
python3 /home/pi/Bakery42/test.py /home/pi/Bakery42/
 Executing:
python3 /home/pi/Bakery42/test.py /home/pi/Bakery42/
 Executing:
python3 /home/pi/Bakery42/test.py /home/pi/Bakery42/
Waiting for machines to work...
[?] Waiting for output file /home/pi/result.txt
Connected to 10.13.33.102.
RESULT:

Test file /home/pi/Bakery42/test.py was run on 8/23/2022 at 20:33:47
[?] Waiting for output file /home/pi/result.txt
Connected to 10.13.33.100.
RESULT:

Test file /home/pi/Bakery42/test.py was run on 8/24/2022 at 1:33:47
[?] Waiting for output file /home/pi/result.txt
Connected to 10.13.33.110.
RESULT:

Test file /home/pi/Bakery42/test.py was run on 8/24/2022 at 1:33:49
[?] Waiting for output file /home/pi/result.txt
Connected to 10.13.33.108.
RESULT:

Test file /home/pi/Bakery42/test.py was run on 8/24/2022 at 1:33:49
>>> master.queue = master.determine_node_assignments(task)
['python3 log2json.py'] squatters081122.txt
>>> master.tasks_confirmed = master.verify_assignments()
[-] Verifying Jobs:
Connected to 10.13.33.102.
Jobs Verified:
{'NODE1': [True, 'local']}
>>> master.run_tasks(12)
[~] Running jobs...
{'NODE1': {'jobs': ['python3 log2json.py'], 'args': ['squatters081122.txt'], 'fileout': ['result.json']}}
 Executing:
python3 /home/pi/Bakery42/log2json.py /home/pi/Bakery42/squatters081122.txt
Waiting for machines to work...
[?] Waiting for output file /home/pi/result.json
Connected to 10.13.33.102.
RESULT:

{"entries": [[true, {"date_registered": ["08/11/22", "18:57:54"], "site_registered": "*.thumpar2.direct.quickconnect.to", "ip_address": "71.231.42.214"}], [true, {"date_registered": ["08/11/22", "18:57:55"], "site_registered": "*.semiotik.direct.quickconnect.to", "ip_address": "45.139.215.25"}], [true, {"date_registered": ["08/11/22", "18:57:56"], "site_registered": "*.samtan123.direct.quickconnect.to", "ip_address": "121.6.106.202"}], [true, {"date_registered": ["08/11/22", "18:58:02"], "site_registered": "test.partner.pik-digital.ru", "ip_address": "130.193.49.205"}], [true, {"date_registered": ["08/11/22", "18:58:06"], "site_registered": "*.zxcmnbasdlkjqwepoi.club", "ip_address": "43.240.29.20"}], [true, {"date_registered": ["08/11/22", "18:58:09"], "site_registered": "3f639017b279d66e20f34ae9cf6a867d.indubitably.xyz", "ip_address": "34.86.164.15"}], [true, {"date_registered": ["08/11/22", "18:58:11"], "site_registered": "*.thumpar2.direct.quickconnect.to", "ip_address": "71.231.42.214"}], [true, {"date_registered": ["08/11/22", "18:58:15"], "site_registered": "mail.whatsupband.ru", "ip_address": "185.215.4.20"}],