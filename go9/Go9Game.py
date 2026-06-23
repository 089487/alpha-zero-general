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
        return (np.array(b.pieces),(0,None))

    def getBoardSize(self):
        # (a,b) tuple
        return (self.n, self.n)

    def getActionSize(self):
        # return number of actions
        return self.n*self.n + 1

    def getNextState(self, state, player, action):
        board, meta_data = state
        pass_count,prev2_board_hash = meta_data
        # if player takes action on board, return next (board,player)
        # action must be a valid move
        if action == self.n*self.n:
            return ((board, (pass_count+1, None)), -player)
        b = Board(self.n)
        b.pieces = np.copy(board)
        prev_board_hash = b._board_hash()
        move = (int(action/self.n), action%self.n)
        b.execute_move(move, player)
        return ((b.pieces, (0, prev_board_hash)), -player)

    def getValidMoves(self, state, player):
        # return a fixed size binary vector
        board, meta_data = state
        pass_count, prev2_board_hash = meta_data
        valids = [0]*self.getActionSize()
        valids[-1] = 1 # in go pass always is a valid move
        b = Board(self.n)
        b.pieces = np.copy(board)
        legalMoves =  b.get_legal_moves(player)
        for x, y in legalMoves:
            test_b = Board(self.n)
            test_b.pieces = np.copy(board)
            valids[self.n*x+y]=1
            test_b.execute_move((x,y), player)
            test_b_hash = test_b._board_hash()
            if prev2_board_hash is not None and test_b_hash == prev2_board_hash:
                valids[self.n*x+y]=0
        return np.array(valids)

    def getGameEnded(self, state, player):
        # return 0 if not ended, 1 if player 1 won, -1 if player 1 lost
        # player = 1
        board, meta_data = state
        pass_count,_ = meta_data
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
        board, meta_data = state
        return (player*board, meta_data)

    def getSymmetries(self, state, pi):
        # mirror, rotational
        board, meta_data = state
        pass_count, prev2_board_hash = meta_data
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
                l += [((newB, (pass_count, None)), list(newPi.ravel()) + [pi[-1]])]
        return l

    def stringRepresentation(self, state):
        board, meta_data = state
        pass_count, prev2_board_hash = meta_data
        prev2_part = prev2_board_hash if prev2_board_hash is not None else b""
        return board.tobytes() + b"|pass=" + str(pass_count).encode() + "b|prev2_hash=" + prev2_part  

    def stringRepresentationReadable(self, state):
        board, meta_data = state
        pass_count, _ = meta_data
        board_s = "".join(self.square_content[square] for row in board for square in row)
        return f"{pass_count};{board_s}"

    def getScore(self, state, player):
        board, meta_data = state
        pass_count, _ = meta_data
        b = Board(self.n)
        b.pieces = np.copy(board)
        return b.countDiff(player) + b.countRegionDiff(player)

    @staticmethod
    def display(state):
        board, meta_data = state
        pass_count, _ = meta_data
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
