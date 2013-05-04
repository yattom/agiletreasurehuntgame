# coding: utf-8

import bigheap
import datetime

class Dumper(object):
    INTERVAL = 500
    def __init__(self, search):
        self.search = search

    def start(self):
        self.started = datetime.datetime.now()
        self.lap = datetime.datetime.now()
        self.loop_count = 0

    def cycle(self, candidate):
        self.loop_count += 1
        if self.loop_count % Dumper.INTERVAL == 0:
            now = datetime.datetime.now()
            print "#%05d elapsed:%s, candidates:%d, processed(normalized):%d, avg:%s, lap avg:%s"%(self.loop_count, now  - self.started, len(self.search.candidates_list), len(self.search._processed), (now - self.started) / self.loop_count, (now - self.lap) / Dumper.INTERVAL)
            self.lap = now
            print candidate.dump()

    def best(self, best_score, candidate):
        print 'current best(score=%d)'%(best_score)
        print candidate.dump(history=True)

    def final_best(self, bests):
        print 'final bests: score=%d'%(bests[0].score())
        for b in bests:
            print b.dump(history=True)

class DumbDumper(object):
    def start(self):
        pass

    def cycle(self, candidate):
        pass

    def best(self, best_score, candidate):
        pass

    def final_best(self, bests):
        pass

class Search(object):
    '''
    >>> from othello import OthelloCandidate, Board
    >>> search = Search()
    >>> start = OthelloCandidate(3, Board(width=3, height=3))
    >>> search.add_candiates(start.next_states())
    >>> bests = search.search_single()
    >>> for b in bests:
    ...    print b.board.dump(history=True)
    ('...',
     '...',
     'BBB')(2, 1, 1)(2, 2, 2)(2, 0, 2)
    ('.B.',
     '.B.',
     '.B.')(1, 1, 1)(2, 1, 2)(0, 1, 2)
    ('B..',
     '.B.',
     '..B')(1, 1, 1)(2, 2, 2)(0, 0, 2)
    '''
    def __init__(self, dump=False):
        self.candidates_list = bigheap.BigHeap(max_threshold=30000, min_threshold=10000)
        self.dump = dump
        self._processed = {}

    def start_dumper(self):
        if self.dump:
            self.dumper = Dumper(self)
        else:
            self.dumper = DumbDumper()
        self.dumper.start()

    def reset_best(self):
        self.best_score = 0
        self.bests = []

    def search_single(self):
        self.start_dumper()
        self.reset_best()
        for candidate in self.candidates():
            self.process_candidate(candidate)
        return self.bests

    def process_candidate(self, candidate):
        self.dumper.cycle(candidate)
        if not candidate.is_final():
            self.add_candiates(candidate.next_states())
        self.add_processed(candidate)

    def candidates(self):
        while True:
            if len(self.candidates_list) == 0: raise StopIteration
            # making it pop(0) slows down the operation dramatically
            candidate = self.candidates_list.pop()
            if not self.is_processed(candidate): yield candidate

    def pop_candidate(self):
        while True:
            if len(self.candidates_list) == 0:
                self.dumper.final_best(self.bests)
                return None
            candidate = self.candidates_list.pop()
            if not self.is_processed(candidate): return candidate

    def add_candiates(self, candidates):
        for c in candidates:
            self.candidates_list.append(c)

    def is_processed(self, candidate):
        if not candidate._normalized_id in self._processed:
            return False
        if self._processed[candidate._normalized_id] < candidate.score():
            return False
        return True

    def add_processed(self, candidate):
        if candidate.is_final():
            if candidate.score() > self.best_score:
                self.best_score = candidate.score()
                self.bests = []
            if candidate.score() == self.best_score:
                self.bests.append(candidate)
                self.dumper.best(self.best_score, candidate)
        if not candidate._normalized_id in self._processed:
            self._processed[candidate._normalized_id] = candidate.score()
        elif candidate.score() > self._processed[candidate._normalized_id]:
            self._processed[candidate._normalized_id] = candidate.score()


class Candidate(object):
    def distance_sum(self):
        return 0

    def normalized_id(self):
        return str(hash(self))

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
        return -cmp(self._distance_sum, other._distance_sum)


class SearchWithGenerator(Search):
    '''
    This version uses generator to conserve memory.
    self.candidate_list contains generators of candidates.
    ie. self.candidat_list == [<generator>, <generator>, ...]
    where each generator yields a series of candidates.

    This is about 10 times slow and it's unable to sort candidates with
    evaluation funcations.  Practically useless.
    '''
    def __init__(self):
        self.candidates_generator_list = []

    def candidates(self):
        while True:
            if len(self.candidates_generator_list) == 0: raise StopIteration
            candidates_generator = self.candidates_generator_list.pop(-1)
            for c in candidates_generator:
                if not self.is_processed(c):
                    yield c

    def add_candiates(self, candidates):
        self.candidates_generator_list.append(candidates)


