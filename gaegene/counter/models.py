import random

from google.appengine.api import memcache
from google.appengine.ext import db


class GeneCounterConfig(db.Model):
    name = db.StringProperty(required=True)
    max_shards = db.IntegerProperty(required=False, default=1)
    timeout = db.IntegerProperty(required=False, default=60)


class GeneCounter(db.Model):
    name = db.StringProperty(required=True)
    shard_count = db.IntegerProperty(required=True, default=0)
    
    @staticmethod
    def get_cache_name(name):
        return "GeneCounterCache|%s" % name
    
    @staticmethod
    def count(name):
        cache_name = GeneCounter.get_cache_name(name)
        count = memcache.get(cache_name)
        if count is None:
            count = 0
            for counter in GeneCounter.all().filter('name =', name):
                count += counter.shard_count
            config = GeneCounterConfig.get_or_insert(name, name=name)
            memcache.add(cache_name, str(count), config.timeout)
        return int(count)
    
    @staticmethod
    def incr(name, delta=1):
        config = GeneCounterConfig.get_or_insert(name, name=name)
        
        def txn():
            shard = random.randint(1, config.max_shards)
            shard_key_name = "%s|shard-%s" % (name, shard)
            counter = GeneCounter.get_by_key_name(shard_key_name)
            if counter is None:
                counter = GeneCounter(key_name=shard_key_name, name=name)
            counter.shard_count += delta
            counter.put()
        
        db.run_in_transaction(txn)
        cache_name = GeneCounter.get_cache_name(name)
        if delta >= 0:
            memcache.incr(cache_name, delta=delta)
        else:
            memcache.decr(cache_name, delta=-delta)
        return GeneCounter.count(name)
    
    @staticmethod
    def decr(name, delta=1):
        return GeneCounter.incr(name, -delta)
    
    @staticmethod
    def timeout(name):
        config = GeneCounterConfig.get_or_insert(name, name=name)
        return config.timeout
    
    @staticmethod
    def set_timeout(name, timeout):
        if timeout > 0:
            config = GeneCounterConfig.get_or_insert(name, name=name)
            config.timeout = timeout
            config.put()
    
    @staticmethod
    def max_shards(name):
        config = GeneCounterConfig.get_or_insert(name, name=name)
        return config.max_shards
    
    @staticmethod
    def add_shards(name, shards):
        config = GeneCounterConfig.get_or_insert(name, name=name)
        
        def txn():
            if shards > 0:
                config.max_shards = config.max_shards + shards
                config.put()
        
        db.run_in_transaction(txn)
    

