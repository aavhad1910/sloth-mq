import queue
from time import sleep
import requests
import string
from threading import Thread, Lock


end_point = "http://20.81.91.73:3000"

mutex = Lock()

total_consumed = 0
total_published = 0
total_acknowledged = 0


def publish(queue):
    for _ in range(5):
        publish_url = f'{end_point}/queues/{queue}'
        
        for message in string.ascii_uppercase:
            response = requests.post(publish_url, json={"message": message})
            print(response.json())
    
    mutex.acquire()
    try:
        global total_published
        total_published += (5 * 26)
    finally:
        mutex.release()
            
        
def create_queue(queue_name):
    create_queue_url = f'{end_point}/queues'
    response = requests.post(create_queue_url, json={"name": queue_name})
    print(response.json())


def acknowledge(message_id):
    ack_url = f'{end_point}/messages/{message_id}' 
    response = requests.delete(ack_url)
    assert(response.status_code == 200)


def consume(queue, num_messages, partial=False):
    consume_url = f'{end_point}/queues/{queue}?num_messages={num_messages}'
    response = requests.get(consume_url)
    assert(response.status_code == 200)
    data = response.json()

    if partial:
        to_ack = len(data) // 2
    else:
        to_ack = len(data)

    for i in range(to_ack):
        message = data[i]
        acknowledge(message['message_id'])
    
    mutex.acquire()
    try:
        global total_consumed
        global total_acknowledged
        
        total_consumed += len(data)
        total_acknowledged += to_ack
    
    finally:
        mutex.release()


queue_name = "tod9"
create_queue(queue_name)


def client_produce():
    p_threads = []
    for i in range(10):
        p_thread = Thread(target=publish, args=(queue_name, ))
        p_threads.append(p_thread)
        p_thread.start()
    
    for th in p_threads:
        th.join()


def client_consume():
    c_threads = []
    for i in range(20):
        c_thread = Thread(target=consume, args=(queue_name, 100))
        c_threads.append(c_thread)
        c_thread.start()
    for th in c_threads:
        th.join()


def client_consume_partial():
    c_threads = []
    for i in range(20):
        c_thread = Thread(target=consume, args=(queue_name, 100), kwargs={"partial": True})
        c_threads.append(c_thread)
        c_thread.start()
    for th in c_threads:
        th.join()


def compose_with_failure():
    client_produce()
    print("Production Complete.")
    print("Partial Consumption starts")
    client_consume_partial()
    print("Partial consumption complete")
    print("Simulating Failure. Client restarting")
    print(f"{queue_name} statistics: Total Published {total_published} Total Consumed {total_consumed} Total ack {total_acknowledged}")
    sleep(30)
    print("Full consumption starts")
    client_consume()
    print(f"{queue_name} statistics: Total Published {total_published} Total Consumed {total_consumed} Total ack {total_acknowledged}")
    print("Client completed")


def compose():
    client_produce()
    print("Production Complete")
    print("Full consumption starts")
    client_consume()
    print(f"{queue_name} statistics: Total Published {total_published} Total Consumed {total_consumed} Total ack {total_acknowledged}")
    print("Client completed")

compose_with_failure()
# compose()
