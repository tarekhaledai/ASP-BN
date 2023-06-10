from sys import argv, stdin, stdout
from typing import Generator, IO, List, Set
from subprocess import CalledProcessError
import subprocess
import json
import time
import os

# PyBoolNet initialization
from pyboolnet.repository import get_all_names, get_bnet
from pyboolnet.file_exchange import bnet2primes
from pyboolnet.trap_spaces import compute_steady_states
from pyboolnet import log

model = argv[1]
timeout = int(argv[2])
max_sol = int(argv[3])
number = 1

successes = 0
total_time = 0

for i in range(number):
  try:
    start = time.perf_counter()
    primes = bnet2primes(model)
    if max_sol == 0:
      # compute all stable configurations
      tspaces = compute_steady_states(primes, max_output=100000000000)
    else:
      # compute first max_sol stable configurations
      tspaces = compute_steady_states(primes, max_output=max_sol)
    n_fixed_points = len(tspaces)
    end = time.perf_counter()
    total_time += end - start
    successes += 1
  except MemoryError:
    print ("MemoryError")
    total_time += timeout
            
if successes > 0:
  print(f"{n_fixed_points} stable configurations {total_time/number:.2f}\n===")
else:
  print("DNF\n===")


