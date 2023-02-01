import json
import os
import sys
import uuid
import threading

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response
from utils import *
from messaging import MessagingManagerFactory

app = Flask(__name__)


def cleanup_job(queue_name, current_time_sec):
    messaging = MessagingManagerFactory.get_messaging_manager() 
    # list to be removed from queue and repopulated
    msi_list = list(messaging.redis.zrangebyscore('messages_' + queue_name + "_ss", 0, int(current_time_sec)))
    if(msi_list):
        total_repopulated_in_queue = messaging.redis.lpush(queue_name, *msi_list)           
        total_removed_from_heap = messaging.redis.zrem('messages_' + queue_name + "_ss", *msi_list)
        print(f"Total repopulated in queue {queue_name}: {total_repopulated_in_queue}", file=sys.stderr)
        print(f"Total removed from heap for {queue_name}: {total_removed_from_heap}", file=sys.stderr)
    else:
        print(f'No messages to cleanup in queue {queue_name}', file=sys.stderr)


@app.route('/queues/<queue_name>', methods=['POST'])
def cleanup(queue_name):
    messaging = MessagingManagerFactory.get_messaging_manager()
    current_time_sec = messaging.get_time()
    current_time_sec -=  RETENTION_PERIOD_SEC
    cleanup_job(queue_name, current_time_sec)
    return Response("Cleanup job for queue_name {queue_name} submitted successfully".format(queue_name=queue_name), status=200)


@app.route('/test', methods=['GET'])
def test():
    print("The cleanup request ended up here in cleanup worker test")
    return '', 200


