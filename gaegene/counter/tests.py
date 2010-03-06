from django.test import TestCase

from gaegene.counter.models import GeneCounter, GeneCounterConfig


COUNTER_NAME = 'test_counter'
COUNTER_NAME_2 = 'test_counter2'

class CounterTest(TestCase):
    def setUp(self):
        pass
    
    def test_backwards_compat(self):
        from gaegene.counter.models import GeneCounter as counter
        self.assertEqual(counter.count(COUNTER_NAME), 0)
        self.assertEqual(counter.incr(COUNTER_NAME), 1)
        self.assertEqual(counter.count(COUNTER_NAME), 1)
        self.assertEqual(counter.decr(COUNTER_NAME), 0)
        self.assertEqual(counter.count(COUNTER_NAME), 0)
    
    def test_counters(self):
        # First counter
        self.assertEqual(GeneCounter.count(COUNTER_NAME), 0)
        self.assertEqual(GeneCounter.all().count(), 0)
        self.assertEqual(GeneCounterConfig.all().count(), 1)
        # Second counter
        self.assertEqual(GeneCounter.count(COUNTER_NAME_2), 0)
        self.assertEqual(GeneCounter.all().count(), 0)
        self.assertEqual(GeneCounterConfig.all().count(), 2)
    
    def test_incr(self):
        self.assertEqual(GeneCounter.incr(COUNTER_NAME), 1)
        self.assertEqual(GeneCounter.count(COUNTER_NAME), 1)
        self.assertEqual(GeneCounter.all().count(), 1)
        self.assertEqual(GeneCounter.incr(COUNTER_NAME, delta=2), 3)
        self.assertEqual(GeneCounter.count(COUNTER_NAME), 3)
    
    def test_decr(self):
        self.assertEqual(GeneCounter.incr(COUNTER_NAME, delta=2), 2)
        self.assertEqual(GeneCounter.incr(COUNTER_NAME, delta=2), 4)
        self.assertEqual(GeneCounter.count(COUNTER_NAME), 4)
        self.assertEqual(GeneCounter.decr(COUNTER_NAME), 3)
        self.assertEqual(GeneCounter.count(COUNTER_NAME), 3)
        self.assertEqual(GeneCounter.decr(COUNTER_NAME, delta=2), 1)
        self.assertEqual(GeneCounter.count(COUNTER_NAME), 1)
    
    def test_counter_timout(self):
        self.assertEqual(GeneCounter.timeout(COUNTER_NAME), 60)
        GeneCounter.set_timeout(COUNTER_NAME, 120)
        self.assertEqual(GeneCounter.timeout(COUNTER_NAME), 120)
        GeneCounter.set_timeout(COUNTER_NAME, -10)
        self.assertEqual(GeneCounter.timeout(COUNTER_NAME), 120)
    
    def test_counter_shards(self):
        self.assertEqual(GeneCounter.max_shards(COUNTER_NAME), 1)
        GeneCounter.add_shards(COUNTER_NAME, 10)
        self.assertEqual(GeneCounter.max_shards(COUNTER_NAME), 11)
        GeneCounter.add_shards(COUNTER_NAME, -10)
        self.assertEqual(GeneCounter.max_shards(COUNTER_NAME), 11)
    

