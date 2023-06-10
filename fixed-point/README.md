# stableconf
Efficient enumeration of stable configurations in Boolean networks using answer set programming



## Requirements



+ `Python` >= 3.6

+ `pyeda` >= 0.28

+ `clingo` ASP solver in your PATH. Instructions are provided directly on the [Potassco pages](https://github.com/potassco/clingo/releases/)

+ To test `PyBoolNet`, you need to install it following the instructions at <https://github.com/hklarner/pyboolnet>

  

## Run `stableconf` from the command line

`python teststableconf.py infile max_sol solver`

where:

+ `infile` is the input BoolNet (.bnet) file.
+ `max_sol` is the maximum number of solutions (0 for all).
+ `solver` is the ASP solver (`clingo` or `hc-asp`)



## Run benchmarks

Test `stableconf` on models in the folder `models`.

`./benchstableconf.sh max_sol solver timeout`



Test `PyBoolNet` on models in the folder `models`.

`./benchPBN.sh max_sol timeout`
