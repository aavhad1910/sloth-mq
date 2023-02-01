import json
import os
import sys
import uuid

from flask import Flask
from flask import jsonify
from flask import request
from flask import Response

from messaging import MessagingManagerFactory
from performance_timer import PerformanceTimer

app = Flask(__name__)


@app.route('/queues/<queue_name>', methods=['POST'])
def publish(queue_name):
    timer = PerformanceTimer()
    timer.start("Request processing")
    messaging = MessagingManagerFactory.get_messaging_manager()
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return Response("Message not present", status=400)
    
    if not queue_name:
        return Response("Queue Name not present", status=400)
    
    if not messaging.is_valid_queue(queue_name):
        return Response(f"Queue {queue_name} invalid. Create one first before publishing", status=400)
    
    timer.lap("Messaging complexity")
    message_id = messaging.publish(queue_name, message)
    
    timer.end()
    print("Production Overall", timer.get_presentable(), file=sys.stderr)
    return jsonify({"message_id": message_id, "queue": queue_name, "message": message})


@app.route('/queues', methods=['POST'])
def create_queue():
    data = request.get_json()
    name = data.get('name')
    messaging = MessagingManagerFactory.get_messaging_manager()
    
    if messaging.is_valid_queue(name):
        return jsonify({"message": f'Queue {name} already exists. Dont test my smartness'}), 400
        
    messaging.create_queue(name)
    return jsonify({"message": 'created', "queue": name})


@app.route('/messages/<message_id>', methods=['DELETE'])
def acknowledge(message_id):
    messaging = MessagingManagerFactory.get_messaging_manager()
    deletion_status = messaging.delete_message(message_id)
    return jsonify({"delete_status": deletion_status, "message_id": message_id}), 200


@app.route('/queues/<queue_name>', methods=['GET'])
def consume(queue_name):
    num_messages = request.args.get('num_messages', 1)
    messaging = MessagingManagerFactory.get_messaging_manager()

    if not messaging.is_valid_queue(queue_name):
        return Response(f"Queue {queue_name} does not exist", status=400)
    
    data_list = messaging.consume(queue_name, num_messages=num_messages)
    return jsonify(data_list), 200

@app.route('/test', methods=['GET'])
def test():
    print("The request ended up here in server")
    return '', 200


