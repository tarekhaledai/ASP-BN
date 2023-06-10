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

import networkx as nx

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

def lit_to_atom_Inoue(name: str) -> str:
    name = name.replace("~", "-")
    if name.startswith("-"):
        return "not x" + name[1:]
    return "x" + name

def node_to_asp(node: str, value: bool):
    if value == True:
        return "p" + node
    else:
        return "n" + node

def node_to_asp_Inoue(node: str, value: bool):
    if value == True:
        return "x" + node
    else:
        return "not x" + node

def write_asp_Inoue(infile: IO, asp_file: IO, computation: str):
    toclose = False
    if isinstance(infile, str):
        #print ("Exist")
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

            x_node = "x" + x
            print("{", x_node, "}."
                , file=asp_file, sep=""
            )

            fx = expr(fx)
            funs[x] = fx
    else:
        infile.close()
        raise ValueError("Currently limited to parsing .bnet files")

    if toclose:
        infile.close()

    """fixed point constraints"""
    if computation == "fix":
        for node in nodes:
            #print (node, ",", funs[node])
            fx = funs[node]

            if fx.is_one():
                print(f"{node_to_asp_Inoue(node, True)}."
                    , file=asp_file
                )
            elif fx.is_zero():
                print(f"{node_to_asp_Inoue(node, False)}."
                    , file=asp_file
                )
            else:
                pfx = fx.to_dnf()
                #print (node, ",", pfx)
                nfx = (~fx).to_dnf()
                #print (node, ",", pfx)

                if isinstance(pfx, Literal):
                    lhs = node_to_asp_Inoue(node, True)
                    rhs = lit_to_atom_Inoue(str(pfx))
                    print(f"{lhs} :- {rhs}."
                        , file=asp_file
                    )
                elif isinstance(pfx, AndOp):
                    atom_list = []
                    for t in pfx.xs:
                        if isinstance(t, Literal):
                            atom_list.append(lit_to_atom_Inoue(str(t)))
                        else:
                            raise ValueError("Not in DNF!")

                    lhs = node_to_asp_Inoue(node, True)
                    rhs = " ; ".join(atom_list)
                    print(f"{lhs} :- {rhs}."
                        , file=asp_file
                    )
                elif isinstance(pfx, OrOp):
                    for s in pfx.xs:
                        if isinstance(s, Literal):
                            lhs = node_to_asp_Inoue(node, True)
                            rhs = lit_to_atom_Inoue(str(s))
                            print(f"{lhs} :- {rhs}."
                                , file=asp_file
                            )
                        elif isinstance(s, AndOp):
                            atom_list = []
                            for t in s.xs:
                                if isinstance(t, Literal):
                                    atom_list.append(lit_to_atom_Inoue(str(t)))
                                else:
                                    raise ValueError("Not in DNF!")

                            lhs = node_to_asp_Inoue(node, True)
                            rhs = " ; ".join(atom_list)
                            print(f"{lhs} :- {rhs}."
                                , file=asp_file
                            )
                        else:
                            raise ValueError("Not in DNF!")
                else:
                    raise ValueError("Not in DNF!")

                if isinstance(nfx, Literal):
                    lhs = node_to_asp_Inoue(node, False)
                    rhs = lit_to_atom_Inoue(str(nfx))
                    print(f"{lhs} :- {rhs}."
                        , file=asp_file
                    )
                elif isinstance(nfx, AndOp):
                    atom_list = []
                    for t in nfx.xs:
                        if isinstance(t, Literal):
                            atom_list.append(lit_to_atom_Inoue(str(t)))
                        else:
                            raise ValueError("Not in DNF!")

                    lhs = node_to_asp_Inoue(node, False)
                    rhs = " ; ".join(atom_list)
                    print(f"{lhs} :- {rhs}."
                        , file=asp_file
                    )
                elif isinstance(nfx, OrOp):
                    for s in nfx.xs:
                        if isinstance(s, Literal):
                            lhs = node_to_asp_Inoue(node, False)
                            rhs = lit_to_atom_Inoue(str(s))
                            print(f"{lhs} :- {rhs}."
                                , file=asp_file
                            )
                        elif isinstance(s, AndOp):
                            atom_list = []
                            for t in s.xs:
                                if isinstance(t, Literal):
                                    atom_list.append(lit_to_atom_Inoue(str(t)))
                                else:
                                    raise ValueError("Not in DNF!")

                            lhs = node_to_asp_Inoue(node, False)
                            rhs = " ; ".join(atom_list)
                            print(f"{lhs} :- {rhs}."
                                , file=asp_file
                            )
                        else:
                            raise ValueError("Not in DNF!")
                else:
                    raise ValueError("Not in DNF!")

def write_asp(infile: IO, asp_file: IO, computation: str):
    toclose = False
    if isinstance(infile, str):
        #print ("Exist")
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

            print("{", ("p" + x), "}."
                , file=asp_file, sep=""
            )

            print("{", ("n" + x), "}."
                , file=asp_file, sep=""
            )
            
            # print("{", ("p" + x), "}."
            #     , file=out_asp_file, sep=""
            # )

            # print("{", ("n" + x), "}."
            #     , file=out_asp_file, sep=""
            # )

            fx = expr(fx)
            funs[x] = fx
    else:
        infile.close()
        raise ValueError("Currently limited to parsing .bnet files")

    if toclose:
        infile.close()

    """fixed point constraints"""
    if computation == "fix":
        for node in nodes:
            print(f":- {node_to_asp(node, True)} ; {node_to_asp(node, False)}."
                , file=asp_file
            )

            print(f"{node_to_asp(node, True)} ; {node_to_asp(node, False)}."
                , file=asp_file
            )
            
            # print(f":- {node_to_asp(node, True)} ; {node_to_asp(node, False)}."
            #     , file=out_asp_file
            # )

            # print(f"{node_to_asp(node, True)} ; {node_to_asp(node, False)}."
            #     , file=out_asp_file
            # )

            #print (node, ",", funs[node])
            fx = funs[node]

            if fx.is_one():
                print(f"{node_to_asp(node, True)}."
                    , file=asp_file
                )
                
                # print(f"{node_to_asp(node, True)}."
                #     , file=out_asp_file
                # )
            elif fx.is_zero():
                print(f"{node_to_asp(node, False)}."
                    , file=asp_file
                )
                
                # print(f"{node_to_asp(node, False)}."
                #     , file=out_asp_file
                # )
            else:
                pfx = fx.to_dnf()
                #print (node, ",", pfx)
                nfx = (~fx).to_dnf()
                #print (node, ",", pfx)

                if isinstance(pfx, Literal):
                    lhs = node_to_asp(node, True)
                    rhs = lit_to_atom(str(pfx))
                    print(f"{lhs} :- {rhs}."
                        , file=asp_file
                    )
                    
                    # print(f"{lhs} :- {rhs}."
                    #     , file=out_asp_file
                    # )
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
                    
                    # print(f"{lhs} :- {rhs}."
                    #     , file=out_asp_file
                    # )
                elif isinstance(pfx, OrOp):
                    for s in pfx.xs:
                        if isinstance(s, Literal):
                            lhs = node_to_asp(node, True)
                            rhs = lit_to_atom(str(s))
                            print(f"{lhs} :- {rhs}."
                                , file=asp_file
                            )
                            
                            # print(f"{lhs} :- {rhs}."
                            #     , file=out_asp_file
                            # )
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
                            
                            # print(f"{lhs} :- {rhs}."
                            #     , file=out_asp_file
                            # )
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
                    
                    # print(f"{lhs} :- {rhs}."
                    #     , file=out_asp_file
                    # )
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
                    
                    # print(f"{lhs} :- {rhs}."
                    #     , file=out_asp_file
                    # )
                elif isinstance(nfx, OrOp):
                    for s in nfx.xs:
                        if isinstance(s, Literal):
                            lhs = node_to_asp(node, False)
                            rhs = lit_to_atom(str(s))
                            print(f"{lhs} :- {rhs}."
                                , file=asp_file
                            )
                            
                            # print(f"{lhs} :- {rhs}."
                            #     , file=out_asp_file
                            # )
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
                            
                            # print(f"{lhs} :- {rhs}."
                            #     , file=out_asp_file
                            # )
                        else:
                            raise ValueError("Not in DNF!")
                else:
                    raise ValueError("Not in DNF!")
            
        # nodeA = "A"
        # nodeB = "B"
        # print(f"{node_to_asp(nodeA, True)} :- {node_to_asp(nodeA, True)} ; {node_to_asp(nodeB, True)}."
        #     , file=asp_file
        # )

        # print(f"{node_to_asp(nodeA, False)} :- {node_to_asp(nodeA, False)}."
        #     , file=asp_file
        # )

        # print(f"{node_to_asp(nodeA, False)} :- {node_to_asp(nodeB, False)}."
        #     , file=asp_file
        # ) 

        # print(f"{node_to_asp(nodeB, True)} :- {node_to_asp(nodeA, False)}."
        #     , file=asp_file
        # )

        # print(f"{node_to_asp(nodeB, True)} :- {node_to_asp(nodeB, True)}."
        #     , file=asp_file
        # )

        # print(f"{node_to_asp(nodeB, False)} :- {node_to_asp(nodeA, True)} ; {node_to_asp(nodeB, False)}."
        #     , file=asp_file
        # )


def solve_asp(asp_filename: str, max_output: int, time_limit: int, computation: str) -> str:
    """Run an ASP solver on program asp_file and get the solutions."""
    dom_mod = "--dom-mod=3, 16" # for min. trap spaces and fixed points

    if computation == "max":
        dom_mod = "--dom-mod=5, 16" # for max. trap spaces
        
    result = subprocess.run(
        [
            "clingo",
            str(max_output),
            #"--heuristic=Domain",
            #"--enum-mod=domRec",
            #dom_mod,
            "--outf=2",  # json output
            f"--time-limit={time_limit}",
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


def solution_to_bool(nodes: List[str], sol: List[str]) -> List[str]:
    """Convert a list of present nodes in sol, to a tri-valued vector."""
    return [node_in_sol(sol, p) for p in nodes]

def solution_to_bool_Inoue(nodes: List[str], sol: List[str]) -> List[str]:
    """Convert a list of present nodes in sol, to a tri-valued vector."""
    return [node_in_sol_Inoue(sol, p) for p in nodes]

def node_in_sol(sol: List[str], node: str) -> str:
    """Return 0/1/- if node is absent, present or does not appear in sol."""
    if "p" + node in sol:
        return "1"
    if "n" + node in sol:
        return "0"
    return "-"

def node_in_sol_Inoue(sol: List[str], node: str) -> str:
    """Return 0/1/- if node is absent, present or does not appear in sol."""
    if "x" + node in sol:
        return "1"
    else:
        return "0"

def get_solutions(
    asp_output: str, nodes: List[str]
) -> Generator[List[str], None, None]:
    """Display the ASP output back as trap spaces."""
    solutions = json.loads(asp_output)
    yield from (
        solution_to_bool(nodes, sol["Value"])
        for sol in solutions["Call"][0]["Witnesses"]
    )

def get_solutions_Inoue(
    asp_output: str, nodes: List[str]
) -> Generator[List[str], None, None]:
    """Display the ASP output back as trap spaces."""
    solutions = json.loads(asp_output)
    yield from (
        solution_to_bool_Inoue(nodes, sol["Value"])
        for sol in solutions["Call"][0]["Witnesses"]
    )

def get_asp_output(
    infile: IO, max_output: int, time_limit: int, computation: str
) -> str:
    """Generate and solve ASP file."""
    (fd, tmpname) = tempfile.mkstemp(suffix=".lp", text=True)
    with open(tmpname, "wt") as asp_file:
        write_asp(infile, asp_file, computation)
    solutions = solve_asp(tmpname, max_output, time_limit, computation)
    #print(f"ASP file {tmpname} written.")
    os.close(fd)
    os.unlink(tmpname)
    return solutions


def get_asp_output_Inoue(
    infile: IO, max_output: int, time_limit: int, computation: str
) -> str:
    """Generate and solve ASP file."""
    (_, tmpname) = tempfile.mkstemp(suffix=".lp", text=True)
    with open(tmpname, "wt") as asp_file:
        write_asp_Inoue(infile, asp_file, computation)
    solutions = solve_asp(tmpname, max_output, time_limit, computation)
    #print(f"ASP file {tmpname} written.")
    os.unlink(tmpname)
    return solutions


def compute_trap_spaces(
    infile: IO,
    display: bool = False,
    max_output: int = 0,
    time_limit: int = 0,
    computation: str = "min",
    method: str = "asp",
) -> Generator[List[str], None, None]:
    """Do the minimal trap space computation on input file infile."""
    start = time.process_time()

    computed_object = "min. trap spaces"
    if computation == "max":
        computed_object = "max. trap spaces"
    elif computation == "min":
        computed_object = "min. trap spaces"
    elif computation == "fix":
        computed_object = "fixed points"
    else:
        raise ValueError("Support computing only max. trap spaces, min. trap spaces, and fixed points")

    print(f"Compute {computed_object}")

    # if display:
    #     print(" ".join(places))

    if method == "asp":
        solutions_output = get_asp_output(infile, max_output, time_limit, computation)
        #solutions_output = get_asp_output_Inoue(infile, max_output, time_limit, computation)

        if solutions_output == "UNSATISFIABLE":
            print(f"No {computed_object}")
            return
        else:
            solutions = get_solutions(solutions_output, nodes)
            #solutions = get_solutions_Inoue(solutions_output, nodes)

    if display:
        #print("\n".join(" ".join(sol) for sol in solutions))
        print(f"Return {len(list(solutions))} fixed points")
        print(f"Running time {time.process_time() - start:.2f}s\n===")
        return
    else:
        yield from solutions


def main():
    """Read the Petri-net send the output to ASP and print solution."""
    parser = argparse.ArgumentParser(
        description=" ".join(__doc__.splitlines()[:3]) + " GPLv3"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s v{version}".format(version=version),
    )
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        default=0,
        help="Maximum number of solutions (0 for all).",
    )
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=0,
        help="Maximum number of seconds for search (0 for no-limit).",
    )
    parser.add_argument(
        "-c",
        "--computation",
        choices=["min", "max", "fix"],
        default="min",
        type=str,
        help="Computation option.",
    )
    parser.add_argument(
        "-s",
        "--solver",
        choices=["asp"],
        default="asp",
        type=str,
        help="Solver to compute the conflict-free siphons.",
    )
    parser.add_argument(
        "infile",
        type=argparse.FileType("r", encoding="utf-8"),
        nargs="?",
        default=sys.stdin,
        help=".bnet file",
    )
    args = parser.parse_args()

    try:
        next(compute_trap_spaces(
            args.infile,
            display=True,
            max_output=args.max,
            time_limit=args.time,
            computation=args.computation,
            method=args.solver,
        ))
    except StopIteration:
        pass

if __name__ == "__main__":
    main()

