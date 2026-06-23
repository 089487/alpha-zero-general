from __future__ import print_function
import sys
sys.path.append('..')
from Game import Game
from .Go9Logic import Board
import numpy as np

class Go9Game(Game):
    square_content = {
        -1: "X",
        +0: "-",
        +1: "O"
    }

    @staticmethod
    def getSquarePiece(piece):
        return Go9Game.square_content[piece]

    def __init__(self, n):
        self.n = n

    def getInitBoard(self):
        # return initial board (numpy board,pass_count)
        b = Board(self.n)
        return (np.array(b.pieces),0)

    def getBoardSize(self):
        # (a,b) tuple
        return (self.n, self.n)

    def getActionSize(self):
        # return number of actions
        return self.n*self.n + 1

    def getNextState(self, state, player, action):
        board, pass_count = state
        # if player takes action on board, return next (board,player)
        # action must be a valid move
        if action == self.n*self.n:
            return ((board,pass_count+1), -player)
        b = Board(self.n)
        b.pieces = np.copy(board)
        move = (int(action/self.n), action%self.n)
        b.execute_move(move, player)
        return ((b.pieces, 0), -player)

    def getValidMoves(self, state, player):
        # return a fixed size binary vector
        board, pass_count = state
        valids = [0]*self.getActionSize()
        valids[-1] = 1 # in go pass always is a valid move
        b = Board(self.n)
        b.pieces = np.copy(board)
        legalMoves =  b.get_legal_moves(player)
        for x, y in legalMoves:
            valids[self.n*x+y]=1
        return np.array(valids)

    def getGameEnded(self, state, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        # player = 1
        board, pass_count = state
        b = Board(self.n)
        b.pieces = np.copy(board)
        if pass_count < 2:
            if b.has_legal_moves(player):
                return 0
            if b.has_legal_moves(-player):
                return 0
        if self.getScore(state,player) > 0:
            return 1
        return -1

    def getCanonicalForm(self, state, player):
        # return state if player==1, else return -state if player==-1
        board, pass_count = state
        return (player*board, pass_count)

    def getSymmetries(self, state, pi):
        # mirror, rotational
        board, pass_count = state
        assert(len(pi) == self.n**2+1)  # 1 for pass
        pi_board = np.reshape(pi[:-1], (self.n, self.n))
        l = []

        for i in range(1, 5):
            for j in [True, False]:
                newB = np.rot90(board, i)
                newPi = np.rot90(pi_board, i)
                if j:
                    newB = np.fliplr(newB)
                    newPi = np.fliplr(newPi)
                l += [((newB, pass_count), list(newPi.ravel()) + [pi[-1]])]
        return l

    def stringRepresentation(self, state):
        board, pass_count = state
        return board.tobytes() + str(pass_count).encode()

    def stringRepresentationReadable(self, state):
        board, pass_count = state
        board_s = "".join(self.square_content[square] for row in board for square in row)
        return f"{pass_count};{board_s}"

    def getScore(self, state, player):
        board, pass_count = state
        b = Board(self.n)
        b.pieces = np.copy(board)
        return b.countDiff(player) + b.countRegionDiff(player)

    @staticmethod
    def display(state):
        board, pass_count = state
        n = board.shape[0]
        print("Pass count:", pass_count)
        print("   ", end="")
        for y in range(n):
            print(y, end=" ")
        print("")
        print("-----------------------")
        for y in range(n):
            print(y, "|", end="")    # print the row #
            for x in range(n):
                piece = board[y][x]    # get the piece to print
                print(Go9Game.square_content[piece], end=" ")
            print("|")

        print("-----------------------")
