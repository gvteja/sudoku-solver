# sudoku-solver
A generalized sudoku solver using finite domain CSP methods.

Input:
Grid is an N x N grid of cells composed of M x K sub-grids.
The grid input file is formatted as:
1. The first line will have three integers separated by ‘,’ and ending in ‘;’ that fix the values for N, M
and K in that order.
2. The next N lines describe the board configuration – one per row ended by ‘;’. An empty cell will
be denoted by ‘-‘.

The CSP methods implemented are:
1. Backtracking
2. Backtracking + MRV heuristic
3. Backtracking + MRV + Forward Checking
4. Backtracking + MRV + Constraint Propagation
5. Min-conflicts Heuristic
