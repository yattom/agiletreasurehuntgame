# coding: utf-8

import unittest
from hamcrest import *
import tempfile
import os
import random

import pickle
import bigheap


class BigHeapTest(unittest.TestCase):
    def test_initial(self):
        heap = bigheap.BigHeap()
        assert_that(len(heap), is_(0))

    def test_initial_with_items(self):
        heap = bigheap.BigHeap(1, 2, 3)
        assert_that(len(heap), is_(3))
        assert_that(repr(heap), is_('BigHeap(1, 2, 3)'))

    def test_items_over_threshold(self):
        heap = bigheap.BigHeap(max_threshold=10)
        items = range(11)
        for i in items: heap.append(i)

        assert_that(len(heap._top_list), is_not(greater_than(10)))
        
        retrieved = []
        while len(heap) > 0:
            retrieved.append(heap.pop())
        items.sort(reverse=True)
        assert_that(retrieved, is_(items))

    def test_many_items_can_be_retrieved(self):
        heap = bigheap.BigHeap(max_threshold=10)
        items = range(10 * 100)
        random.shuffle(items)
        for i in items: heap.append(i)

        assert_that(len(heap._top_list), is_not(greater_than(heap.max_threshold)))
        assert_that(len(heap), is_(10 * 100))
        
        retrieved = []
        while len(heap) > 0:
            retrieved.append(heap.pop())
        items.sort(reverse=True)
        assert_that(retrieved, is_(items))

    def test_many_items_tmpfile_handling(self):
        heap = bigheap.BigHeap(max_threshold=20, min_threshold=8)
        items = range(10 * 100)
        random.shuffle(items)
        for i in items: heap.append(i)

        for frag in heap._storage._fragments:
            f = open(frag.filename)
            loaded = pickle.load(f)
            f.close()

            assert_that(len(loaded), is_not(greater_than(heap.max_threshold)))
            for i in loaded:
                assert_that(i, less_than_or_equal_to(frag.maximum))
        
        while len(heap) > 0: heap.pop()
        assert_that(len(heap._storage._fragments), is_(0))



if __name__=='__main__':
    unittest.main()

