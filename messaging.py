import io
import json
import logging
import os
import sys
import uuid

from redis import Redis

from collections import defaultdict
from collections import namedtuple
from performance_timer import PerformanceTimer
from statistics_manager import StatisticsManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MessageStorageInfo:

    def __init__(self, queue, message_id, file_name, start, end):
        self.queue = queue
        self.message_id = message_id
        self.file_name = file_name
        self.start = start
        self.end = end
        self.created_at = None
        self.last_consumed_at = None
    
    def set_creation(self, unix_time):
        self.created_at = unix_time
    
    def set_last_consumption(self, unix_time):
        self.last_consumed_at = unix_time
    
    def serialize(self, encoding_scheme):
        data_dict = {
            'queue': self.queue,
            'message_id': str(self.message_id),
            'file_name': self.file_name,
            'start': self.start,
            'end': self.end,
            'created_at': self.created_at or '',
            'last_consumed_at': self.last_consumed_at or ''
        }
        return json.dumps(data_dict, ensure_ascii=False).encode(encoding_scheme)
    
    @classmethod
    def deserialize(cls, data, encoding_scheme):
        data = json.loads(data)
        
        msi = MessageStorageInfo(
            queue=data['queue'],
            message_id=data['message_id'],
            file_name=data['file_name'],
            start=data['start'],
            end=data['end'],
        )
        if data.get('created_at'):
            msi.set_creation(data['created_at'])
        if data.get('last_consumed_at'):
            msi.set_last_consumption(data['last_consumed_at'])
        return msi


class StorageManager:
    
    def __init__(self, session_id):
        self.sequence = 0
        self.session_id = session_id
    
    def get_base_path(self):
        path = '/code/shared_volume/messaging'
        os.makedirs(path, exist_ok=True)
        return path
    
    def get_encoding_scheme(self):
        return 'utf-8'
    
    def should_switch(self, file_name):
        if not os.path.exists(file_name):
            return False
        
        size_in_bytes = os.stat(file_name).st_size
        #File size is more than 1 MB. Switch now.
        if (size_in_bytes / pow(10, 6)) > 1:
            return True
        return False          

    def get_messaging_file_name(self):
        current_file = os.path.join(self.get_base_path(), f'{self.session_id}_{self.sequence}.bin')
        
        if self.should_switch(current_file):
            self.sequence = self.sequence + 1
            return os.path.join(self.get_base_path(), f'{self.session_id}_{self.sequence}.bin')
        
        return current_file
        
    def put(self, message_str, message_id, queue):
        data_dict = {"message_id": str(message_id), "data": message_str}
        serialized_data = json.dumps(data_dict, ensure_ascii=False).encode(self.get_encoding_scheme())
        
        file_name = self.get_messaging_file_name()

        with open(file_name, 'ab') as fp:
            start = fp.tell() + 1
            bytes_written = fp.write(serialized_data)
            end = (start + bytes_written) - 1
        
        return MessageStorageInfo(queue=queue, message_id=message_id, file_name=file_name, start=start, end=end)
        
    def get(self, msi_list):
        data_list = []
        file_grouped = defaultdict(lambda: [])
        msi_list_sorted = sorted(msi_list, key=lambda msi: msi.start)

        for msi in msi_list_sorted:
            file_grouped[msi.file_name].append(msi)
        
        for file_name, file_msi in file_grouped.items():
            fp = open(file_name, 'rb')
            
            for msi in file_msi:
                fp.seek(msi.start - 1)
                size = (msi.end - msi.start) + 1
                serialized_data = fp.read(size)
                decoded_string = serialized_data.decode(self.get_encoding_scheme())
                data_list.append(json.loads(decoded_string))
        
            fp.close()
        return data_list


class MessagingManager:

    def __init__(self):
        self.session_id = uuid.uuid4()
        self.redis = Redis(host='my-release-redis-master', port=6379, decode_responses=True,  password='oAwaVyMiSP')
        self.storage = StorageManager(self.session_id)
        self.sm = StatisticsManager(self.redis)
    
    def is_valid_queue(self, queue_name):
        return self.redis.sismember('queues', queue_name) 

    def create_queue(self, queue_name):
        self.redis.sadd('queues', queue_name)
    
    def get_encoding_scheme(self):
        return 'utf-8'
    
    def get_time(self):
        return self.redis.time()[0]
        
    def publish(self, queue, message_str):
        timer = PerformanceTimer()
        timer.start("Publish time")
        message_id = str(uuid.uuid4())

        timer.lap("Storage")
        msi = self.storage.put(message_str, message_id, queue)
        
        timer.lap("Redis Lpush")
        self.redis.lpush(queue, message_id)
        
        msi.set_creation(self.get_time())

        timer.lap("Redis hashmap set")
        self.redis.hset('messages',message_id, msi.serialize(self.get_encoding_scheme()))
        
        timer.lap("Statistics update")
        self.sm.publish(queue)

        timer.end()
        print("Publish Messaging class", timer.get_presentable(), file=sys.stderr)
        return message_id
    
    def consume(self, queue, num_messages=1):
        msi_list = []
        popped_message_list = self.redis.rpop(queue, num_messages)
        
        if not popped_message_list:
            return msi_list
        
        actual_consumed = len(popped_message_list)
        popped_msi_list = self.redis.hmget('messages' , popped_message_list)
        current_redis_time = int(self.get_time())
        # Adding to the sorted set
        data = {}
        for message_id, msi_encoded in zip(popped_message_list, popped_msi_list):
            msi = MessageStorageInfo.deserialize(msi_encoded, self.get_encoding_scheme())
            assert(message_id == msi.message_id)
            print(msi.message_id)
            data[msi.message_id] = int(current_redis_time)
            msi_list.append(msi)
        
        print(data)
        self.redis.zadd('messages_' + queue + "_ss" , data)

        data_list = self.storage.get(msi_list)
        self.sm.consume(queue, actual_consumed)
        return data_list
    
    def get_message(self, message_id):
        if not self.redis.hexists('messages' , message_id):
            return False
        msi_encoded = self.redis.hget('messages', message_id)
        msi = MessageStorageInfo.deserialize(msi_encoded, self.get_encoding_scheme())
        return msi
    
    def delete_message(self, message_id):
        msi = self.get_message(message_id)
        if not msi:
            return False
        # returns zero if does not exist
        queue = msi.queue
        num_deleted_sorted_set = self.redis.zrem('messages_' + queue + "_ss", message_id)
        if(num_deleted_sorted_set == 0):
            print("Message id {mid} was reordered".format(mid=message_id))
            return True
        num_deleted = self.redis.hdel('messages', message_id)
        
        assert(num_deleted == 1)
        self.sm.acknowledge(msi.queue)
        return True
    
    def get_all_queues(self):
        queues = list(self.redis.smembers('queues'))[:]
        return queues

class MessagingManagerFactory:

    @classmethod
    def get_messaging_manager(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = MessagingManager()
        return cls.instance
