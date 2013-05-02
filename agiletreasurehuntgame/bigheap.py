# coding: utf-8

import tempfile
import pickle
import os

def my_bisect_insert(a, x, cmp=cmp):
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if cmp(x, a[mid]) < 0: hi = mid
        else: lo = mid + 1
    a.insert(lo, x)

class BigHeap(object):
    '''
    Basic protocol.  You can only do append(item) and pop().

    >>> heap = BigHeap()
    >>> heap.append(5)
    >>> heap.append(2)
    >>> heap.append(4)
    >>> heap.append(1)
    >>> heap.append(2)
    >>> heap.append(4)
    >>> heap.append(3)
    >>> heap
    BigHeap(1, 2, 2, 3, 4, 4, 5)
    >>> len(heap)
    7
    >>> heap.pop()
    5
    >>> heap.pop()
    4
    >>> heap.pop()
    4
    >>> heap.pop()
    3
    >>> heap
    BigHeap(1, 2, 2)
    >>> heap.append(20)
    >>> heap.append(10)
    >>> heap
    BigHeap(1, 2, 2, 10, 20)
    >>> heap.pop()
    20
    >>> heap.pop()
    10
    >>> heap.pop()
    2
    >>> heap.pop()
    2
    >>> heap.pop()
    1
    >>> len(heap)
    0
    >>> heap.pop()
    Traceback (most recent call last):
        ...
    IndexError: pop from empty list
    '''

    def __init__(self, *args, **argv):
        self._top_list = []
        self._len = 0
        self.max_threshold = argv['max_threshold'] if 'max_threshold' in argv else 10000
        self.min_threshold = argv['min_threshold'] if 'min_threshold' in argv else self.max_threshold // 10
        self._storage = DistributedItems(self.max_threshold, self.min_threshold)

        if args:
            for v in args: self.append(v)

    def append(self, item):
        self.append_to_top_list(item)
        if len(self._top_list) > self.max_threshold:
            self.save_surplus()
        self._len += 1

    def append_to_top_list(self, item):
        my_bisect_insert(self._top_list, item)

    def save_surplus(self):
        surplus = self._top_list[:len(self._top_list) - self.min_threshold]
        self._top_list = self._top_list[len(self._top_list) - self.min_threshold:]
        self._storage.store_items(surplus)

    def pop(self):
        if len(self._top_list) <= self.min_threshold:
            self.load_surplus()
        elif self._storage.maximum() and self._top_list[-1] < self._storage.maximum():
            self.load_surplus()
        self._len -= 1
        return self._top_list.pop()

    def load_surplus(self):
        for item in self._storage.pop_items():
            my_bisect_insert(self._top_list, item)

    def __repr__(self):
        return 'BigHeap(' + (', '.join([repr(v) for v in self._top_list])) + ')'

    def __len__(self):
        return self._len


class DistributedItems(object):
    class Fragment(object):
        def __init__(self, filename, maximum):
            self.filename = filename
            self.maximum = maximum

        def __cmp__(self, other):
            return cmp(self.maximum, other.maximum)

        def store_items(self, items):
            f = open(self.filename, 'wb')
            pickle.dump(items, f)
            f.close()
            self.maximum = items[-1]

        def discard(self):
            os.remove(self.filename)
            self.maximum = None

        @staticmethod
        def create(items):
            f = tempfile.NamedTemporaryFile(delete=False)
            pickle.dump(items, f)
            f.close()
            return DistributedItems.Fragment(f.name, items[-1])

    def __init__(self, max_threshold, min_threshold):
        self.max_threshold = max_threshold
        self.min_threshold = min_threshold
        self._fragments = []

    def save_new_files(self, items):
        while items:
            new_items = items[:self.min_threshold]
            items = items[self.min_threshold:]
            my_bisect_insert(self._fragments, DistributedItems.Fragment.create(new_items))

    def store_items(self, items):
        distribution = [[] for _ in self._fragments] + [[]]
        for item in items:
            for i, frag in enumerate(self._fragments):
                if item <= frag.maximum:
                    distribution[i].append(item)
                    break
            else:
                distribution[-1].append(item)

        for i, frag in enumerate(self._fragments[:]):
            # self._fragments is copied so it's safe to add/remove frags in this loop
            if not distribution[i]: continue
            f = open(frag.filename)
            loaded = pickle.load(f)
            f.close()
            for item in distribution[i]:
                my_bisect_insert(loaded, item)

            if len(loaded) > self.max_threshold:
                self._fragments.remove(frag)
                frag.discard()
                self.save_new_files(loaded)
            else:
                frag.store_items(loaded)

        if distribution[-1]:
            new_list = []
            for item in distribution[-1]:
                my_bisect_insert(new_list, item)
            self.save_new_files(new_list)

    def pop_items(self):
        if not self._fragments: return []
        frag = self._fragments.pop()
        f = open(frag.filename)
        surplus = pickle.load(f)
        f.close()
        os.remove(frag.filename)
        return surplus

    def maximum(self):
        if not self._fragments: return None
        return self._fragments[-1].maximum
