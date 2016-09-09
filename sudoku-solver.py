import random

class SudokuCSP(object):
    '''
    Encapsulates the sudoku constraints problem.
    Encodes knowledge of how to perform consistency check, get unassgined values etc
    Maintains the config info of the game like n, m, k and also constraint check counts
    '''

    def __init__(self, n, m, k, initialBoard = None):
        self.n = n
        self.m = m
        self.k = k
        self.domain = set(range(1, self.n+1))
        self.reducedDomains = None
        self.checks = 0
        if initialBoard:
            self.initialBoard = [row[:] for row in initialBoard]
        else:
            self.initialBoard = None

    def getDomain(self):
        return self.domain

    def getChecks(self):
        return self.checks

    def getNeighbours(self, i, j):
        '''given a cell, return all its neighbours in the constraint graph'''

        neighbours = set()

        # add row and column neighbours i.e elments in ith row and jth column
        for x in range(self.n):
            neighbours.add((i, x))
            neighbours.add((x, j))

        # add all the elements in the sub-grid that i,j belongs to as its neighbours
        sb_i = i / self.m * self.m
        sb_j = j / self.k * self.k
        for si in range(sb_i, sb_i + self.m):
            for sj in range(sb_j, sb_j + self.k):
                neighbours.add((si, sj))

        # exclude i,j from the set of neighbours
        neighbours.remove((i,j))
        return neighbours

    def getUnassignedNeighbours(self, board, i, j):
        '''given a cell and a board, return all its unassigned neighbours in the constraint graph'''

        neighbours = set()

        # add row and column neighbours i.e elments in ith row and jth column, if they are unassigned
        for x in range(self.n):
            if board[i][x] == -1:
                neighbours.add((i, x))
            if board[x][j] == -1:
                neighbours.add((x, j))

        # add all the elements in the sub-grid that i,j belongs to as its neighbours, if they are unassigned
        sb_i = i / self.m * self.m
        sb_j = j / self.k * self.k
        for si in range(sb_i, sb_i + self.m):
            for sj in range(sb_j, sb_j + self.k):
                if board[si][sj] == -1:
                    neighbours.add((si, sj))

        # if present, exclude i,j from the set of neighbours
        neighbours.discard((i,j))
        return neighbours

    def check(self, board, i, j, incrCheckCount = True):
        '''check if the assignment in i,j pos of the board is consistent'''

        if incrCheckCount:
            self.checks += 1

        appeared = set()

        # add all the values of its neighbours into the appeared set
        for si, sj in self.getNeighbours(i, j):
            appeared.add(board[si][sj])

        # check that the value of i,j is not already taken by one of its neighbours
        return board[i][j] not in appeared

    def checkNeighboursConsistent(self, board, pos_i, pos_j):
        '''given a board and a position, check if all of the position's unassigned neighbours have legal domain values '''

        for i,j in self.getUnassignedNeighbours(board, pos_i, pos_j):
            if len(self.getLegalValues(board, i, j)) == 0:
                # if one of the neighbouts does not have any legal values left, then return falase
                return False

        return True

    def checkAll(self, board):
        '''given a full board, check if any row, column or sub-grid constraints are violated'''
        self.checks += 1

        # check row and column contraints
        for i in range(self.n):
            # check row constraint for ith row
            appeared = set()
            for digit in board[i]:
                if digit in appeared:
                    return False
                appeared.add(digit)

            # check column constraint of ith column
            appeared = set()
            for j in range(self.n):
                digit = board[j][i]
                if digit in appeared:
                    return False
                appeared.add(digit)

        # check subgrid constraint
        for i in range(0, self.n, self.m):
            for j in range(0, self.n, self.k):
                # check subgrid (i, i+m) * (j, j+k)
                appeared = set()
                for si in range(i, i + self.m):
                    for sj in range(j, j + self.k):
                        digit = board[si][sj]
                        if digit in appeared:
                            return False
                        appeared.add(digit)

        return True

    def isSatisfiable(self):
        '''check if the csp defined by the intial board is satisfiable'''

        if not self.initialBoard:
            return False

        self.checks += 1
        for i in range(self.n):
            for j in range(self.n):
                if self.initialBoard[i][j] != -1 and not self.check(self.initialBoard, i, j, False):
                    # if its a hard cell (value cannot be changed) and it is not satisfiable, return false
                    return False

        return True

    def getLegalValues(self, board, i, j):
        '''given a board and an unassigned position, return the set of all legal domain values that the position can take'''

        appeared = set()

        # add all the values of its neighbours into the appeared set
        for si, sj in self.getNeighbours(i, j):
            appeared.add(board[si][sj])

        # return the different between the set of adomain values and the set of values that the neighbours have already taken
        legalValues = self.reducedDomains[i][j] if self.reducedDomains else self.domain
        legalValues = legalValues - appeared
        return legalValues

    def computeReducedDomains(self):
        '''compute a matrix of domain values for each pos in the initial board by using arc consistency algorithm'''

        self.reducedDomains = [[self.domain.copy() for j in range(self.n)] for i in range(self.n)]
        arcs = []

        # initalize a list of directed arcs with all arcs in constraint graph
        # exclude arcs originating from non-open cells since these cell values cannot be changed
        for i in range(self.n):
            for j in range(self.n):
                if self.initialBoard[i][j] == -1:
                    for neighbour in self.getNeighbours(i, j):
                        arcs.append(( (i,j), neighbour ))
                else:
                    self.reducedDomains[i][j] = {self.initialBoard[i][j]}

        while len(arcs) != 0:
            x, y = arcs.pop(0)
            removed = False
            xvals = list(self.reducedDomains[x[0]][x[1]])
            for xval in xvals:
                if len(self.reducedDomains[y[0]][y[1]] - {xval}) == 0:
                    # if there is no legel value for y for value xval in x, there remove xval from the domain of x 
                    self.reducedDomains[x[0]][x[1]].remove(xval)
                    removed = True
            if removed:
                # if domain of x is reduced, then re-insert all arcs from x to its neighbours
                for neighbour in self.getNeighbours(x[0], x[1]):
                    arcs.append(( x, neighbour ))

    def getReducedDomain(self, i, j):
        '''given a position on the board, return the pre-computed reduced domain for that position'''
        return self.reducedDomains[i][j]

    def getOpenCellMRV(self, board):
        '''given a board, returns the open cell with fewest legal values'''

        mostRestrainedSize = self.n + 1
        mostRestrainedCell = (-1, -1)

        for i in range(self.n):
            for j in range(self.n):
                if board[i][j] == -1:
                    size = len(self.getLegalValues(board, i, j))
                    if size < mostRestrainedSize:
                        mostRestrainedSize = size
                        mostRestrainedCell = (i, j)

        return mostRestrainedCell

    def getLCVList(self, board, pos_i, pos_j):
        '''given a board, and an unassigned position, returns the list of its legal values in LCV order'''

        legalValues = self.getLegalValues(board, pos_i, pos_j)

        lcvValues = []
        neighbours = self.getUnassignedNeighbours(board, pos_i, pos_j)

        for value in legalValues:
            sizeNeighboursDomain = 0
            # for every value in legal values, compute the sum of legal domains of all pos_i,pos_j cell's neighbours
            for i,j in neighbours:
                legalNeighbourValues = self.getLegalValues(board, i, j)
                legalNeighbourValues.discard(value)
                sizeNeighboursDomain += len(legalNeighbourValues)
            lcvValues.append((sizeNeighboursDomain, value))

        # sort legalvalues in decreasing order of neighbours domain size
        lcvValues.sort(reverse=True)
        return [value for size, value in lcvValues]

    def getFirstOpenCell(self, board):
        '''takes the board as input and returns the row, col of the first open cell in the board'''

        for i in range(self.n):
            for j in range(self.n):
                if board[i][j] == -1:
                    return i,j

        # otherwise return row, col -1, -1
        return -1, -1

    def randomInitializeBoard(self, board):
        '''given a board, fill all the open cells with a random value from the domain'''

        for i in range(self.n):
            for j in range(self.n):
                if board[i][j] == -1:
                    board[i][j] = random.randint(1, self.n)

    def swapMinConflicts(self, board):
        '''given a board, pick a random changable cell with conflicts and replace its value with the least conflicting value in the domain. return the selected cell'''

        conflictingCells = []
        for i in range(self.n):
            for j in range(self.n):
                if self.initialBoard[i][j] == -1 and not self.check(board, i, j, False):
                    # make sure the conflicting cell wasnt filled in the original board. should not change this cell if that is the case and that cell wouldnt come under conflicting cell
                    conflictingCells.append((i,j))

        # randomly pick a cell from conflicting cells
        selectedI, selectedJ = random.choice(conflictingCells)

        neighbourValues = []
        for i, j in self.getNeighbours(selectedI, selectedJ):
            neighbourValues.append(board[i][j])

        # assume intially that minconflicts is with full board
        minConflicts = self.n ** 2
        minConflictValue = -1

        for value in self.domain:
            # for each value in domain, compute its conflicts and choose the minimum among them
            conflicts = neighbourValues.count(value)
            if conflicts < minConflicts:
                minConflicts = conflicts
                minConflictValue = value

        board[selectedI][selectedJ] = minConflictValue

        return selectedI, selectedJ

# Utility functions
def parseInput(filename):
    '''take the game file and return n,m,k params along with the initial game state'''
    with open(filename) as gameFile:
        params = gameFile.readline().strip(' \n;')
        params = params.split(',')
        if len(params) != 3:
            print 'Invalid number of params. Please check'
            raise ValueError

        for i in range(3):
            params[i] = int(params[i])
        n, m, k = params

        if (n % m != 0) or (n % k != 0):
            print 'Invalid subgrid params. Please check'
            raise ValueError

        # Board:
        # All the unfilled pos will be represented by -1. 
        # Numbers will be represented as is
        # Initializing the board with all -1
        board = [[-1 for x in range(n)] for x in range(n)]

        for i in range(n):
            line = gameFile.readline().strip(' \n;')
            digits = line.split(',')
            if len(digits) != n:
                print 'Invalid number of columns in board. Please check'
                raise ValueError
            for j in range(n):
                if digits[j] != '-':
                    digit = int(digits[j])
                    board[i][j] = digit
                    if not (0 < digit < n + 1):
                        print 'Invalid digit {0} in row, col = {1}, {2}. Please check'.format(digit, i, j)
                        raise ValueError

    return n, m, k, board

def printBoard(board):
    for row in board:
        print row

def backtrackingRecursive(board, csp):
    '''takes the sudoku board and constraint definition and returns the solved board using vanilla backtracking algorithm'''
    
    i,j = csp.getFirstOpenCell(board)
    if i == -1 and j == -1:
        return True, board

    for value in csp.getDomain():
        board[i][j] = value
        if csp.check(board, i, j):
            result, resultBoard = backtrackingRecursive(board, csp)
            if result:
                return result, resultBoard
        board[i][j] = -1

    return False, [[]]

def backtrackingMRVRecursive(board, csp):
    '''takes the sudoku board and constraint definition and return the solved board using backtracking plus MRV order for choosing open cells + LCV order for values'''
    
    i,j = csp.getOpenCellMRV(board)
    if i == -1 and j == -1:
        return True, board

    for value in csp.getLCVList(board, i, j):
        board[i][j] = value
        if csp.check(board, i, j):
            result, resultBoard = backtrackingMRVRecursive(board, csp)
            if result:
                return result, resultBoard
        board[i][j] = -1

    return False, [[]]

def backtrackingMRVfwdRecursive(board, csp):
    '''takes the sudoku board and constraint definition and returns the solved board using backtracking plus MRV order for choosing open cells + LCV order for values + plus forward checking'''
    
    i,j = csp.getOpenCellMRV(board)
    if i == -1 and j == -1:
        return True, board

    for value in csp.getLCVList(board, i, j):
        board[i][j] = value
        if csp.check(board, i, j) and csp.checkNeighboursConsistent(board, i, j):
            result, resultBoard = backtrackingMRVfwdRecursive(board, csp)
            if result:
                return result, resultBoard
        board[i][j] = -1

    return False, [[]]

def backtrackingMRVcpRecursive(board, csp):
    '''takes the sudoku board and constraint definition and return the solved board using backtracking plus MRV order for choosing open cells'''
    
    i,j = csp.getOpenCellMRV(board)
    if i == -1 and j == -1:
        return True, board

    for value in csp.getLCVList(board, i, j):
        board[i][j] = value
        if csp.check(board, i, j):
            result, resultBoard = backtrackingMRVcpRecursive(board, csp)
            if result:
                return result, resultBoard
        board[i][j] = -1

    return False, [[]]

def backtracking(filename):
    ###
    # use backtracking to solve sudoku puzzle here,
    # return the solution in the form of list of 
    # list as describe in the PDF with # of consistency
    # checks done
    ###

    n, m, k, board = parseInput(filename)
    csp = SudokuCSP(n, m, k)

    result, resultBoard = backtrackingRecursive(board, csp)

    return (resultBoard, csp.getChecks())

def backtrackingMRV(filename):
    ###
    # use backtracking + MRV to solve sudoku puzzle here,
    # return the solution in the form of list of 
    # list as describe in the PDF with # of consistency
    # checks done
    ###
    
    n, m, k, board = parseInput(filename)
    csp = SudokuCSP(n, m, k)

    result, resultBoard = backtrackingMRVRecursive(board, csp)

    return (resultBoard, csp.getChecks())

def backtrackingMRVfwd(filename):
    ###
    # use backtracking +MRV + forward propogation
    # to solve sudoku puzzle here,
    # return the solution in the form of list of 
    # list as describe in the PDF with # of consistency
    # checks done
    ###

    n, m, k, board = parseInput(filename)
    csp = SudokuCSP(n, m, k)

    result, resultBoard = backtrackingMRVfwdRecursive(board, csp)

    return (resultBoard, csp.getChecks())

def backtrackingMRVcp(filename):
    ###
    # use backtracking + MRV + cp to solve sudoku puzzle here,
    # return the solution in the form of list of 
    # list as describe in the PDF with # of consistency
    # checks done
    ###

    n, m, k, board = parseInput(filename)
    csp = SudokuCSP(n, m, k, board)

    csp.computeReducedDomains()
    result, resultBoard = backtrackingMRVcpRecursive(board, csp)

    return (resultBoard, csp.getChecks())

def minConflict(filename):
    ###
    # use minConflict to solve sudoku puzzle here,
    # return the solution in the form of list of 
    # list as describe in the PDF with # of consistency
    # checks done
    ###

    n, m, k, board = parseInput(filename)
    csp = SudokuCSP(n, m, k, board)

    csp.randomInitializeBoard(board)

    # limit the number of iterations of min-conflicts to 5000
    for i in range(5000):
        if csp.checkAll(board):
            break
        csp.swapMinConflicts(board)

    return (board, csp.getChecks())