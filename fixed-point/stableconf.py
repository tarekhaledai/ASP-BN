"""Compute fixed points of a Boolean network using answer set programming.

Copyright (C) 2023 giang.trinh91@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import tempfile
import xml.etree.ElementTree as etree
from typing import Generator, IO, List

from sys import setrecursionlimit

from pyeda.boolalg import boolfunc
from pyeda.boolalg.bdd import bddvar, expr2bdd
from pyeda.boolalg.expr import AndOp, Constant, Literal, OrOp, Variable, expr

version = "0.4.1"

setrecursionlimit(2048)

nodes = []


def lit_to_atom(name: str) -> str:
    name = name.replace("~", "-")
    if name.startswith("-"):
        return "n" + name[1:]
    return "p" + name


def node_to_asp(node: str, value: bool):
    if value == True:
        return "p" + node
    else:
        return "n" + node


def write_asp(infile: IO, asp_file: IO):
    toclose = False
    if isinstance(infile, str):
        infile = open(infile, "r", encoding="utf-8")
        toclose = True

    funs = {}
    if infile.name.endswith(".bnet"):
        for line in infile.readlines():
            if line.startswith("#") or line.startswith("targets, factors"):
                continue
            try:
                x, fx = line.replace(" ", "").replace("!", "~").split(",", maxsplit=1)
            except ValueError:
                continue
            
            x = x.strip()
            nodes.append(x)

            # print("{", ("p" + x), "}."
            #     , file=asp_file, sep=""
            # )

            # print("{", ("n" + x), "}."
            #     , file=asp_file, sep=""
            # )

            fx = expr(fx)
            funs[x] = fx
    else:
        infile.close()
        raise ValueError("Currently limited to parsing .bnet files")

    if toclose:
        infile.close()

    """state constraints"""
    for node in nodes:
        print(f":- {node_to_asp(node, True)} ; {node_to_asp(node, False)}."
            , file=asp_file
        )

        print(f"{node_to_asp(node, True)} ; {node_to_asp(node, False)}."
            , file=asp_file
        )
        
        fx = funs[node]

        if fx.is_one():
            print(f"{node_to_asp(node, True)}."
                , file=asp_file
            )
            
        elif fx.is_zero():
            print(f"{node_to_asp(node, False)}."
                , file=asp_file
            )
        else:
            pfx = fx.to_dnf()
            nfx = (~fx).to_dnf()

            if isinstance(pfx, Literal):
                lhs = node_to_asp(node, True)
                rhs = lit_to_atom(str(pfx))
                print(f"{lhs} :- {rhs}."
                    , file=asp_file
                )
            elif isinstance(pfx, AndOp):
                atom_list = []
                for t in pfx.xs:
                    if isinstance(t, Literal):
                        atom_list.append(lit_to_atom(str(t)))
                    else:
                        raise ValueError("Not in DNF!")

                lhs = node_to_asp(node, True)
                rhs = " ; ".join(atom_list)
                print(f"{lhs} :- {rhs}."
                    , file=asp_file
                )
            elif isinstance(pfx, OrOp):
                for s in pfx.xs:
                    if isinstance(s, Literal):
                        lhs = node_to_asp(node, True)
                        rhs = lit_to_atom(str(s))
                        print(f"{lhs} :- {rhs}."
                            , file=asp_file
                        )
                    elif isinstance(s, AndOp):
                        atom_list = []
                        for t in s.xs:
                            if isinstance(t, Literal):
                                atom_list.append(lit_to_atom(str(t)))
                            else:
                                raise ValueError("Not in DNF!")

                        lhs = node_to_asp(node, True)
                        rhs = " ; ".join(atom_list)
                        print(f"{lhs} :- {rhs}."
                            , file=asp_file
                        )
                    else:
                        raise ValueError("Not in DNF!")
            else:
                raise ValueError("Not in DNF!")

            if isinstance(nfx, Literal):
                lhs = node_to_asp(node, False)
                rhs = lit_to_atom(str(nfx))
                print(f"{lhs} :- {rhs}."
                    , file=asp_file
                )
            elif isinstance(nfx, AndOp):
                atom_list = []
                for t in nfx.xs:
                    if isinstance(t, Literal):
                        atom_list.append(lit_to_atom(str(t)))
                    else:
                        raise ValueError("Not in DNF!")

                lhs = node_to_asp(node, False)
                rhs = " ; ".join(atom_list)
                print(f"{lhs} :- {rhs}."
                    , file=asp_file
                )              
            elif isinstance(nfx, OrOp):
                for s in nfx.xs:
                    if isinstance(s, Literal):
                        lhs = node_to_asp(node, False)
                        rhs = lit_to_atom(str(s))
                        print(f"{lhs} :- {rhs}."
                            , file=asp_file
                        ) 
                    elif isinstance(s, AndOp):
                        atom_list = []
                        for t in s.xs:
                            if isinstance(t, Literal):
                                atom_list.append(lit_to_atom(str(t)))
                            else:
                                raise ValueError("Not in DNF!")

                        lhs = node_to_asp(node, False)
                        rhs = " ; ".join(atom_list)
                        print(f"{lhs} :- {rhs}."
                            , file=asp_file
                        )
                    else:
                        raise ValueError("Not in DNF!")
            else:
                raise ValueError("Not in DNF!")


def solve_asp_clingo(asp_filename: str, max_output: int) -> str:
    """Run clingo on program asp_file and get the solutions."""  

    print(asp_filename)

    result = subprocess.run(
        [
            "clingo",
            str(max_output),
            #"--heuristic=Domain",
            #"--enum-mod=domRec",
            #dom_mod,
            "--outf=2",  # json output
            #f"--time-limit={time_limit}",
            asp_filename,
        ],
        capture_output=True,
        text=True,
    )

    # https://www.mat.unical.it/aspcomp2013/files/aspoutput.txt
    # 30: SAT, all enumerated, optima found, 10 stopped by max, 20 query is false
    if result.returncode != 30 and result.returncode != 10 and result.returncode != 20:
        print(f"Return code from clingo: {result.returncode}")
        result.check_returncode()  # will raise CalledProcessError

    if result.returncode == 20:
        return "UNSATISFIABLE"

    return result.stdout


def solve_asp_hc_asp(asp_filename: str, max_output: int) -> str:
    """Run hc-asp on program asp_file and get the solutions."""

    result = subprocess.run(
        [
            "./hc_asp",
            str(max_output),
            #"--heuristic=Domain",
            #"--enum-mod=domRec",
            #dom_mod,
            #"--outf=2",  # json output
            #f"--time-limit={time_limit}",
            asp_filename,
        ],
        capture_output=True,
        text=True,
        shell=True
    )

    # https://www.mat.unical.it/aspcomp2013/files/aspoutput.txt
    # 30: SAT, all enumerated, optima found, 10 stopped by max, 20 query is false
    if result.returncode != 30 and result.returncode != 10 and result.returncode != 20:
        print(f"Return code from clingo: {result.returncode}")
        result.check_returncode()  # will raise CalledProcessError

    if result.returncode == 20:
        return "UNSATISFIABLE"

    return result.stdout


def solution_to_bool(nodes: List[str], sol: List[str]) -> List[str]:
    return [node_in_sol(sol, p) for p in nodes]


def node_in_sol(sol: List[str], node: str) -> str:
    if "p" + node in sol:
        return "1"
    if "n" + node in sol:
        return "0"
    return "-"


def get_solutions_clingo(
    asp_output: str, nodes: List[str]
) -> List[List[str]]:
    """Display the ASP output back as stable configurations."""
    solutions = json.loads(asp_output)
    list_stable_configurations = []

    for sol in solutions["Call"][0]["Witnesses"]:
        list_stable_configurations.append(solution_to_bool(nodes, sol["Value"]))

    return list_stable_configurations


def get_solutions_hc_asp(
    asp_output: str, nodes: List[str]
) -> List[List[str]]:

    """Display the ASP output back as stable configurations."""

    solutions = json.loads(asp_output)
    list_stable_configurations = []

    for sol in solutions["Call"][0]["Witnesses"]:
        list_stable_configurations.append(solution_to_bool(nodes, sol["Value"]))

    return list_stable_configurations


def get_asp_output(
    infile: IO, max_output: int, solver: str
) -> str:
    """Generate and solve ASP file."""
    (fd, tmpname) = tempfile.mkstemp(suffix=".lp", text=True)
    with open(tmpname, "wt") as asp_file:
        write_asp(infile, asp_file)

    if solver == "clingo":
        solutions = solve_asp_clingo(tmpname, max_output)
    elif solver == "hc-asp":
        solutions = solve_asp_hc_asp(tmpname, max_output)
    else:
        raise ValueError("Only support the clingo and hc-asp solvers!")
    
    #print(f"ASP file {tmpname} written.")

    os.close(fd)
    os.unlink(tmpname)
    return solutions


def compute_stable_configurations(
    infile: IO,
    max_output: int = 0,
    solver: str = "clingo",
    display: bool = True,
) -> int:
    """Do the stable configuration computation on input file infile."""
    solutions_output = get_asp_output(infile, max_output, solver)

    if solutions_output == "UNSATISFIABLE":
        if display == True:
            print(f"No stable configuration!")
        return 0
    else:
        if solver == "clingo":
            solutions = get_solutions_clingo(solutions_output, nodes)
        else:
            solutions = get_solutions_hc_asp(solutions_output, nodes)

        if display == True:
            print("\n".join(" ".join(sol) for sol in solutions))
           
        return len(solutions)


