from redis import Redis

class StatisticsManager:

    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    def publish(self, queue):
        self.redis.incr(f'{queue}_msgs_published')
    
    def consume(self, queue, num_messages):
        self.redis.incrby(f'{queue}_msgs_consumed', num_messages)
    
    def acknowledge(self, queue):
        self.redis.incr(f'{queue}_msgs_acked')
