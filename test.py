import os, sys, bakeryutils as butils
ldate, ltime = butils.create_timestamp()
msg = f"Test file {sys.argv[0]} was run on {ldate} at {ltime}"
open("result.txt","w").write(msg)
