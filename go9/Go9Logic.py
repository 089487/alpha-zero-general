'''
Author: Eric P. Nichols
Date: Feb 8, 2008.
Board class.
Board data:
  1=white, -1=black, 0=empty
  first dim is column , 2nd is row:
     pieces[1][7] is the square in column 2,
     at the opposite end of the board in row 8.
Squares are stored and manipulated as (x,y) tuples.
x is the column, y is the row.
'''

class Board():

    # list of all 4 directions on the board, as (x,y) offsets
    __directions = ((1,0),(0,1),(-1,0),(0,-1))

    def __init__(self, n):
        "Set up initial board configuration."

        self.n = n
        # Create the empty board array.
        self.pieces = [None]*self.n
        for i in range(self.n):
            self.pieces[i] = [0]*self.n

    # add [][] indexer syntax to the Board
    def __getitem__(self, index): 
        return self.pieces[index]
    
    def _neighbors(self, x, y):
        for dx, dy in self.__directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.n and 0 <= ny < self.n:
                yield nx, ny

    def _get_group(self, x, y):
        color = self[x][y]
        if color == 0:
            return set()

        group = set()
        stack = [(x, y)]

        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in group:
                continue
            if self[cx][cy] != color:
                continue

            group.add((cx, cy))
            for nx, ny in self._neighbors(cx, cy):
                if (nx, ny) not in group and self[nx][ny] == color:
                    stack.append((nx, ny))

        return group
    def _get_liberties(self, group):
        liberties = set()

        for x, y in group:
            for nx, ny in self._neighbors(x, y):
                if self[nx][ny] == 0:
                    liberties.add((nx, ny))

        return liberties

    def _is_legal_move(self, move, color):
        x, y = move
        if self[x][y] !=0 : 
            return False
        self[x][y] = color
        # check if this move can capture any opponent pieces
        capture = False
        for nx, ny in self._neighbors(x, y):
            if self[nx][ny] == -color:
                opponent_group = self._get_group(nx, ny)
                liberties = self._get_liberties(opponent_group)
                if len(liberties) == 0 and len(opponent_group) > 0:
                    capture = True
                    break
        illegal = not capture and len(self._get_liberties(self._get_group(x, y))) == 0
        self[x][y] = 0
        return not illegal

    def countDiff(self, color):
        """Counts the # pieces of the given color
        (1 for white, -1 for black, 0 for empty spaces)"""
        count = 0
        for x in range(self.n):
            for y in range(self.n):
                if self[x][y]==color:
                    count += 1
                if self[x][y]==-color:
                    count -= 1
        return count
    def countRegionDiff(self, color):
        
        visited = set()
        count = 0
        for x in range(self.n):
            for y in range(self.n):
                if self[x][y] == 0 and (x, y) not in visited:
                    region = set()
                    stack = [(x, y)]
                    touches_color = False
                    touches_opponent = False

                    while stack:
                        cx, cy = stack.pop()
                        if (cx, cy) in region:
                            continue
                        region.add((cx, cy))
                        visited.add((cx, cy))

                        for nx, ny in self._neighbors(cx, cy):
                            if self[nx][ny] == color:
                                touches_color = True
                            elif self[nx][ny] == -color:
                                touches_opponent = True
                            elif self[nx][ny] == 0 and (nx, ny) not in region:
                                stack.append((nx, ny))
                    count += touches_color*len(region) - touches_opponent*len(region)
        return count


    def get_legal_moves(self, color):
        """Returns all the legal moves for the given color.
        (1 for white, -1 for black
        """
        moves = set()  # stores the legal moves.

        # Get all the squares with pieces of the given color.
        for y in range(self.n):
            for x in range(self.n):
                if self._is_legal_move((x,y), color):
                    moves.add((x,y))
        return list(moves)

    def has_legal_moves(self, color):
        return len(self.get_legal_moves(color)) > 0

    def get_moves_for_square(self, square):
        """Returns all the legal moves that use the given square as a base.
        That is, if the given square is (3,4) and it contains a black piece,
        and (3,5) and (3,6) contain white pieces, and (3,7) is empty, one
        of the returned moves is (3,7) because everything from there to (3,4)
        is flipped.
        """
        (x,y) = square

        # determine the color of the piece.
        color = self[x][y]

        # skip empty source squares.
        if color==0:
            return None

        # search all possible directions.
        moves = []
        for direction in self.__directions:
            move = self._discover_move(square, direction)
            if move:
                # print(square,move,direction)
                moves.append(move)

        # return the generated move list
        return moves

    def execute_move(self, move, color):
        """Perform the given move on the board; flips pieces as necessary.
        color gives the color pf the piece to play (1=white,-1=black)
        """

        #Much like move generation, start at the new piece's square and
        #follow it on all 8 directions to look for a piece allowing flipping.

        # Add the piece to the empty square.
        # print(move)
        x,y = move
        assert self[x][y]==0
        self[x][y] = color
        for nx,ny in self._neighbors(x,y):
            if self[nx][ny]==-color:
                opponent_group = self._get_group(nx,ny)
                liberties = self._get_liberties(opponent_group)
                if len(liberties)==0:
                    for gx,gy in opponent_group:
                        self[gx][gy] = 0


    def _discover_move(self, origin, direction):
        """ Returns the endpoint for a legal move, starting at the given origin,
        moving by the given increment."""
        x, y = origin
        color = self[x][y]
        flips = []

        for x, y in Board._increment_move(origin, direction, self.n):
            if self[x][y] == 0:
                if flips:
                    # print("Found", x,y)
                    return (x, y)
                else:
                    return None
            elif self[x][y] == color:
                return None
            elif self[x][y] == -color:
                # print("Flip",x,y)
                flips.append((x, y))

    def _get_flips(self, origin, direction, color):
        """ Gets the list of flips for a vertex and direction to use with the
        execute_move function """
        #initialize variables
        flips = [origin]

        for x, y in Board._increment_move(origin, direction, self.n):
            #print(x,y)
            if self[x][y] == 0:
                return []
            if self[x][y] == -color:
                flips.append((x, y))
            elif self[x][y] == color and len(flips) > 0:
                #print(flips)
                return flips

        return []

    @staticmethod
    def _increment_move(move, direction, n):
        # print(move)
        """ Generator expression for incrementing moves """
        move = list(map(sum, zip(move, direction)))
        #move = (move[0]+direction[0], move[1]+direction[1])
        while all(map(lambda x: 0 <= x < n, move)): 
        #while 0<=move[0] and move[0]<n and 0<=move[1] and move[1]<n:
            yield move
            move=list(map(sum,zip(move,direction)))
            #move = (move[0]+direction[0],move[1]+direction[1])

