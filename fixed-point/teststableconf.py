from sys import argv, stdin, stdout
from typing import Generator, IO, List, Set
from subprocess import CalledProcessError
import subprocess
import json
import time
import os

from stableconf import compute_stable_configurations

model = argv[1]
max_sol = int(argv[2])
solver = argv[3]

total_time = 0

try:
  start = time.perf_counter()
  n_stables = compute_stable_configurations(model, max_output=max_sol, solver=solver, display=False)
  end = time.perf_counter()
  total_time += end - start
  print(f"{n_stables} stable configurations {total_time:.2f}s\n===")
except MemoryError:
  print ("MemoryError")
    


