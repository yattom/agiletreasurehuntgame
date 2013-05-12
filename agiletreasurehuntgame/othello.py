# coding: utf-8

import datetime
import bisect

from agiletreasurehuntgame.search import Search, MultiprocessingFlavor

class Board(object):
    '''
    >>> b = Board()
    >>> print b.dump()
    ('......',
     '......',
     '......',
     '......',
     '......',
     '......')
    >>> b.place(0, 0, Board.BLACK)
    >>> b.place(0, 1, Board.WHITE)
    >>> b.place(0, 2, Board.WHITE)
    >>> print b.dump()
    ('BWW...',
     '......',
     '......',
     '......',
     '......',
     '......')
    >>> b.place(0, 3, Board.BLACK)
    >>> print b.dump()
    ('BBBB..',
     '......',
     '......',
     '......',
     '......',
     '......')
    >>> b.flip_count
    {'BtoW': 0, 'WtoB': 2}
    >>> b.place(2, 2, Board.BLACK)
    >>> b.place(3, 3, Board.BLACK)
    >>> b.place(1, 4, Board.BLACK)
    >>> b.place(2, 4, Board.BLACK)
    >>> b.place(3, 4, Board.BLACK)
    >>> b.place(1, 1, Board.WHITE)
    >>> b.place(0, 4, Board.WHITE)
    >>> print b.dump()
    ('BBBBW.',
     '.W..B.',
     '..B.B.',
     '...BB.',
     '......',
     '......')
    >>> b.place(4, 4, Board.WHITE)
    >>> print b.dump()
    ('BBBBW.',
     '.W..W.',
     '..W.W.',
     '...WW.',
     '....W.',
     '......')
    >>> b.flip_count
    {'BtoW': 5, 'WtoB': 2}

    To copy a board, use Board(old_board.state())

    >>> b2 = Board(b.state())
    >>> b.dump() == b2.dump()
    True
    >>> b.flip_count == b2.flip_count
    True
    >>> b.place_history == b2.place_history
    True

    All place() calls are logged in place_history

    >>> b = Board()
    >>> b.place_history
    []
    >>> b.place(0, 0, Board.WHITE)
    >>> b.place_history
    [(0, 0, 1)]
    >>> b.place(1, 1, Board.WHITE)
    >>> b.place(2, 2, Board.BLACK)
    >>> b.place_history
    [(0, 0, 1), (1, 1, 1), (2, 2, 2)]
    '''
    EMPTY = 0
    WHITE = 1
    BLACK = 2
    CHARS = ['.', 'W', 'B']

    VECTORS = [(c, r) for c in range(-1, 2) for r in range(-1, 2) if not c == r == 0]

    def __init__(self, state={}, width=6, height=6):
        if 'size' in state:
            self.width = state['size'][0]
            self.height = state['size'][1]
        else:
            self.width = width
            self.height = height

        if 'board' in state:
            self.board = state['board']
        else:
            self.board = [Board.EMPTY] * (self.width * self.height)

        if 'flip_count' in state:
            self.flip_count = state['flip_count']
        else:
            self.flip_count = { 'BtoW': 0, 'WtoB': 0 }

        if 'place_history' in state:
            self.place_history = state['place_history']
        else:
            self.place_history = []

    def state(self):
        return {
            'board': self.board[:],
            'flip_count': dict(self.flip_count),
            'place_history': self.place_history[:],
            'size': (self.width, self.height),
        }

    @staticmethod
    def build(initial):
        '''
        >>> initial = (
        ...   '..WB.B',
        ...   '...BWB',
        ...   '...B..',
        ...   'WWB...',
        ...   '...BWB',
        ...   '...WWB',
        ... )
        >>> board = Board.build(initial)
        >>> print board.dump()
        ('..WB.B',
         '...BWB',
         '...B..',
         'WWB...',
         '...BWB',
         '...WWB')

        >>>
        '''
        w, h = len(initial), len(initial[0])
        board = Board(width=w, height=h)
        for r in range(h):
            for c in range(w):
                color = Board.CHARS.index(initial[r][c])
                board.board[board._index(r, c)] = color
        return board

    def dump(self, history=False):
        buf = ''
        for r in range(self.height):
            if r == 0: buf += '('
            else: buf += ' '
            buf += "'"
            for c in range(self.width):
                buf += Board.CHARS[self.get(r, c)]
            buf += "'"
            if r < self.height - 1: buf += ',\n'
            else: buf += ')'
        if history:
            buf += ''.join([str(p) for p in self.place_history])
        return buf

    def _index(self, row, col):
        return row + col * self.height

    def get(self, row, col):
        return self.board[self._index(row, col)]

    def place(self, row, col, color):
        assert self.get(row, col) == Board.EMPTY
        self.board[self._index(row, col)] = color
        self.turn(placed=(row, col))
        self.place_history.append((row, col, color))

    def turn(self, placed):
        for row, col, before_color in self.turnable(placed):
            self.flip(row, col)

    def turnable(self, placed):
        turnable = []
        placed_row, placed_col = placed
        for v in Board.VECTORS:
            line = self.get_line(placed_row, placed_col, v)
            turnable += self.turnable_in_line(line)
        return turnable

    def flip(self, row, col):
        assert self.get(row, col) != Board.EMPTY
        if self.get(row, col) == Board.BLACK:
            new_color = Board.WHITE
            self.flip_count['BtoW'] += 1
        elif self.get(row, col) == Board.WHITE:
            new_color = Board.BLACK
            self.flip_count['WtoB'] += 1
        self.board[self._index(row, col)] = new_color

    def get_line(self, row, col, v):
        '''
        >>> initial = (
        ...   '..WB.B',
        ...   '...BWW',
        ...   '...B..',
        ...   'WWB...',
        ...   '...BWB',
        ...   '...WWB',
        ... )
        >>> board = Board.build(initial)
        >>> board.get_line(1, 3, (0, 1))
        [(1, 3, 2), (1, 4, 1), (1, 5, 1)]
        >>> board.get_line(3, 1, (0, 1))
        [(3, 1, 1), (3, 2, 2)]
        >>> board.get_line(5, 4, (-1, -1))
        [(5, 4, 1), (4, 3, 2), (3, 2, 2)]
        '''
        line = []
        for i in xrange(1000):
            r = row + v[0] * i
            c = col + v[1] * i
            if r < 0 or self.height <= r or c < 0 or self.width <= c: break
            if self.get(r, c) == Board.EMPTY:
                break
            line.append((r, c, self.get(r, c)))
        return line

    def turnable_in_line(self, line):
        head = line[0][2]
        middle = []
        tail = None
        for i in range(1, len(line)):
            if line[i][2] == head:
                tail = line[i][2]
                break
            middle.append(line[i])
        if tail:
            return middle
        else:
            return []


class BoardNormalizer(object):
    '''
    >>> b = Board(width=3, height=3)
    >>> b.place(0, 0, 1)
    >>> b.place(0, 1, 2)
    >>> b.place(0, 2, 2)
    >>> BoardNormalizer.width = 3
    >>> BoardNormalizer.height = 3
    >>> BoardNormalizer.no_transform(b)
    '122000000'
    >>> BoardNormalizer.vertical_mirror(b)
    '221000000'
    >>> BoardNormalizer.horizontal_mirror(b)
    '000000122'
    >>> BoardNormalizer.diagonal_mirror_left_up(b)
    '100200200'
    >>> BoardNormalizer.diagonal_mirror_right_up(b)
    '002002001'
    >>> BoardNormalizer.rotate_90(b)
    '001002002'
    >>> BoardNormalizer.rotate_180(b)
    '000000221'
    >>> BoardNormalizer.rotate_270(b)
    '200200100'
    '''

    @classmethod
    def coords(cls):
        try:
            return cls._coords
        except AttributeError:
            cls._coords = [(r, c) for r in range(cls.height) for c in range(cls.width)]
            return cls._coords

    @classmethod
    def str(cls, l):
        return ''.join([str(i) for i in l])

    @classmethod
    def no_transform(cls, board):
        return cls.str([str(board.get(r, c)) for (r, c) in cls.coords()])

    @classmethod
    def vertical_mirror(cls, board):
        return cls.str([str(board.get(r, cls.width - c - 1)) for (r, c) in cls.coords()])

    @classmethod
    def horizontal_mirror(cls, board):
        return cls.str([str(board.get(cls.height - r - 1, c)) for (r, c) in cls.coords()])

    @classmethod
    def diagonal_mirror_left_up(cls, board):
        return cls.str([str(board.get(c, r)) for (r, c) in cls.coords()])

    @classmethod
    def diagonal_mirror_right_up(cls, board):
        return cls.str([str(board.get(cls.width - c - 1, cls.height - r - 1)) for (r, c) in cls.coords()])

    @classmethod
    def rotate_90(cls, board):
        return cls.str([str(board.get(cls.height - c - 1, r)) for (r, c) in cls.coords()])

    @classmethod
    def rotate_180(cls, board):
        return cls.str([str(board.get(cls.height - r - 1, cls.width - c - 1)) for (r, c) in cls.coords()])

    @classmethod
    def rotate_270(cls, board):
        return cls.str([str(board.get(c, cls.width - r - 1)) for (r, c) in cls.coords()])


class OthelloCandidate(object):
    def __init__(self, place_limit, board):
        self.place_limit = place_limit
        self.board = board
        self._normalized_id = self.normalized_id()

    def distance_sum(self):
        if '_distance_sum' in dir(self):
            return self._distance_sum
        pieces = [(r, c) for r in range(self.board.height) for c in range(self.board.width) if self.board.get(r, c) != Board.EMPTY]
        if not pieces: return 0
        sum = 0
        for row, col in pieces:
            distances = [abs(row - r) + abs(col - c) for (r, c) in pieces if not (row == r and col == c)]
            sum += min(distances) if distances else 0
        #return (sum + 0.0) / (len(pieces) ** 2)
        self._distance_sum = sum
        return sum

    def normalized_id(self):
        BoardNormalizer.width = self.board.width
        BoardNormalizer.height = self.board.height
        
        coords = [(r, c) for r in range(self.board.height) for c in range(self.board.width)]

        patterns = [
            BoardNormalizer.no_transform(self.board),
            BoardNormalizer.vertical_mirror(self.board),
            BoardNormalizer.horizontal_mirror(self.board),
        ]
        if self.board.width == self.board.height:
            patterns += [
                BoardNormalizer.diagonal_mirror_left_up(self.board),
                BoardNormalizer.diagonal_mirror_right_up(self.board),
                BoardNormalizer.rotate_90(self.board),
                BoardNormalizer.rotate_180(self.board),
                BoardNormalizer.rotate_270(self.board),
            ]
        return ''.join((str(c) for c in min(patterns)))

    def is_final(self):
        return len(self.board.place_history) >= self.place_limit

    def score(self):
        return self.board.flip_count['WtoB']

    def next_states(self):
        for r in range(self.board.height):
            for c in range(self.board.width):
                if self.board.get(r, c) != Board.EMPTY: continue
                for color in [Board.WHITE, Board.BLACK]:
                    next_board = Board(self.board.state())
                    next_board.place(r, c, color)
                    yield OthelloCandidate(self.place_limit, next_board)


    def dump(self, **argv):
        return self.board.dump(**argv)

    def __hash__(self):
        return hash(self._normalized_id)

    def __cmp__(self, other):
        return -cmp(self.distance_sum(), other.distance_sum())


def parse_args():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='single')
    parser.add_argument('-d', '--depth', type=int, default=3)
    parser.add_argument('-s', '--size', type=int, default=3)
    parser.add_argument('-b', '--batchsize', type=int, default=2)
    parser.add_argument('-c', '--concurrency', type=int, default=1)
    parser.add_argument('--width', type=int)
    parser.add_argument('--height', type=int)

    args = parser.parse_args()
    if not args.width: args.width = args.size
    if not args.height: args.height = args.size
    return args


def run_server(args):
    import sys
    sys.argv[1] = '' # bypass ip arg in web/wsgi.py
    search = Search(dump=True)
    search.start_dumper()

    start = OthelloCandidate(args.depth, Board(width=args.width, height=args.height))
    search.add_candiates(start.next_states())
    for candidate in search.candidates():
        search.process_candidate(candidate)
        if len(search.candidates_list) > args.concurrency * args.batchsize: break

    import search_server
    search_server.SearchServer.run(search)


def run_by_multiprocessing(args):
    import datetime
    started = datetime.datetime.now()
    import multiprocessing
    flavor = MultiprocessingFlavor()
    search = Search(dump=False, flavor=flavor)
    search.start_dumper()

    start = OthelloCandidate(args.depth, Board(width=args.width, height=args.height))
    search.add_candiates(start.next_states())
    for candidate in search.candidates():
        search.process_candidate(candidate)
        if len(search.candidates_list) > args.concurrency * args.batchsize: break

    processes = []
    for i in range(args.concurrency):
        p = multiprocessing.Process(target=search.search_single)
        p.start()
        processes.append(p)

    [p.join() for p in processes]
    print 'Finished! elapsed: %s'%(datetime.datetime.now() - started)
    for b in search.final_bests():
        print 'score=%d'%(b.score())
        print b.board.dump(history=True)


def run_single(args):
    import datetime
    started = datetime.datetime.now()
    search = Search(dump=True)
#    search = SearchWithGenerator()
    start = OthelloCandidate(args.depth, Board(width=args.width, height=args.height))
    search.add_candiates(start.next_states())
    search.search_single()
    print 'elapsed: %s'%(datetime.datetime.now() - started)
    for b in search.final_bests:
        print 'score=%d'%(b.score())
        print b.board.dump(history=True)


def main():
    args = parse_args()
    if args.mode == 'http':
        run_server(args)
    elif args.mode == 'multiprocessing':
        run_by_multiprocessing(args)
    elif args.mode == 'single':
        run_single(args)
    else:
        run_single(args)

if __name__=='__main__':
    main()

