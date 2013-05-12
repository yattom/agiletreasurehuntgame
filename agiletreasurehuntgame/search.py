# coding: utf-8

import bigheap
import datetime

class StdoutDumper(object):
    INTERVAL = 1000
    def __init__(self, search):
        self.search = search

    def start(self):
        self.started = datetime.datetime.now()
        self.lap = datetime.datetime.now()
        self.loop_count = 0

    def cycle(self, candidate):
        self.loop_count += 1
        if self.loop_count % StdoutDumper.INTERVAL == 0:
            now = datetime.datetime.now()
            print "#%05d elapsed:%s, candidates:%d, processed(normalized):%d, avg:%s, lap avg:%s"%(self.loop_count, now  - self.started, len(self.search.candidates_list), len(self.search._processed), (now - self.started) / self.loop_count, (now - self.lap) / StdoutDumper.INTERVAL)
            self.lap = now
            print candidate.dump()

    def best(self, best_score, candidate):
        print 'current best(score=%d)'%(best_score)
        print candidate.dump(history=True)

    def final_best(self, bests):
        if not bests: return
        print 'final bests: score=%d'%(bests[0].score())
        for b in bests:
            print b.dump(history=True)

    def log_error(self):
        import traceback
        traceback.print_exc()
        

class SilentDumper(object):
    def start(self):
        pass

    def cycle(self, candidate):
        pass

    def best(self, best_score, candidate):
        pass

    def final_best(self, bests):
        pass

    def log_error(self):
        import os, traceback
        f = open('error-%s.log'%(os.getpid()), 'w+')
        traceback.print_exc(file=f)
        f.flush()
        f.close()


class Search(object):
    '''
    >>> from othello import OthelloCandidate, Board
    >>> search = Search()
    >>> start = OthelloCandidate(3, Board(width=3, height=3))
    >>> search.add_candiates(start.next_states())
    >>> bests = search.search_single()
    >>> for b in bests:
    ...    print b.board.dump(history=True)
    ('.B.',
     '.B.',
     '.B.')(1, 1, 1)(2, 1, 2)(0, 1, 2)
    ('...',
     '...',
     'BBB')(2, 1, 1)(2, 2, 2)(2, 0, 2)
    ('B..',
     '.B.',
     '..B')(1, 1, 1)(2, 2, 2)(0, 0, 2)
    '''
    def __init__(self, dump=False, flavor=None):
        if not flavor:
            flavor = ComparableCandidatesFlavor
        self.candidates_list = flavor.create_candidates_list()
        self.dump = dump
        self._processed = flavor.create_processed()
        self.bests = flavor.create_bests()

    def start_dumper(self):
        if self.dump:
            self.dumper = StdoutDumper(self)
        else:
            self.dumper = SilentDumper()
        self.dumper.start()

    def search_single(self):
        try:
            self.start_dumper()
            for candidate in self.candidates():
                self.process_candidate(candidate)
            return self.bests
        except:
            self.dumper.log_error()

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
            if c.is_final():
                self.add_processed(c)
            else:
                self.candidates_list.append(c)

    def is_processed(self, candidate):
        if not candidate._normalized_id in self._processed:
            return False
        if self._processed[candidate._normalized_id] < candidate.score():
            return False
        return True

    def add_processed(self, candidate):
        if candidate.is_final():
            if candidate.score() > self.best_score():
                self.bests[:] = [candidate]
            elif candidate.score() == self.best_score():
                self.bests.append(candidate)
                self.dumper.best(self.best_score(), candidate)
        if not candidate._normalized_id in self._processed:
            self._processed[candidate._normalized_id] = candidate.score()
        elif candidate.score() > self._processed[candidate._normalized_id]:
            self._processed[candidate._normalized_id] = candidate.score()

    def best_score(self):
        if not self.bests: return 0
        return max((c.score() for c in self.bests))

    def final_bests(self):
        best_score = self.best_score()
        return (c for c in self.bests if c.score() == best_score)

class Candidate(object):
    def normalized_id(self):
        raise StandardError('must be implemented')

    def is_final(self):
        raise StandardError('must be implemented')

    def score(self):
        raise StandardError('must be implemented')

    def next_states(self):
        raise StandardError('must be implemented')

    def dump(self, **argv):
        raise StandardError('must be implemented')

    def __hash__(self):
        return hash(self.normalized_id())


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


class ComparableCandidatesFlavor(object):
    @staticmethod
    def create_candidates_list():
        return bigheap.BigHeap(max_threshold=30000, min_threshold=10000)

    @staticmethod
    def create_processed():
        '''
        create dict object which maps normalize_id to score (int)
        '''
        return {}

    @staticmethod
    def create_bests():
        return []

import multiprocessing

class CandidatesByQueue(object):
    def __init__(self):
        self.queue = multiprocessing.Queue()
    def pop(self):
        return self.queue.get()
    def __len__(self):
        return self.queue.qsize()
    def append(self, value):
        self.queue.put(value)

class MultiprocessingFlavor(object):
    '''
    Does not compare candidates; candidates are simply queued and shared.
    Processed are shared by multiprocessing.Array.
    '''
    def __init__(self):
        self._candidates_list = CandidatesByQueue()
        self.manager = multiprocessing.Manager()
        self._processed = self.manager.dict()
        self._bests = self.manager.list()

    def create_candidates_list(self):
        return self._candidates_list

    def create_processed(self):
        '''
        create dict object which maps normalize_id to score (int)
        '''
        return self._processed

    def create_bests(self):
        return self._bests

