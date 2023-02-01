'''
Execution Time: 0.485060453414917 (30 msgs) (1 thread)
Execution Time: 2.728044271469116 (300 msgs) (1 thread)
Execution TIme: 14.48613452911377 (3000 msgs) (1 thread)
Execution TIme: 129.23896980285645 (30000 msgs) (1 thread)

Execution Time: 0.5633082389831543 (30 msgs) (3 threads)
Execution Time: 2.6907970905303955 (300 msgs) (1 thread)
Execution TIme: 16.369880199432373 (3000 msgs) (1 thread)
Execution TIme: 143.8931679725647 (30000 msgs) (1 thread)
'''

import requests
import string
import time
import threading


end_point = "http://20.85.209.0:3000"

def publish(queue, message_count):
    for _ in range(message_count):
        publish_url = f'{end_point}/queues/{queue}'
        
        for message in string.ascii_uppercase[0]:
            response = requests.post(publish_url, json={"message": message})
            # print(response.json())
            
        
def create_queue(queue_name):
    create_queue_url = f'{end_point}/queues'
    response = requests.post(create_queue_url, json={"name": queue_name})
    print(response.json())


def acknowledge(message_id):
    ack_url = f'{end_point}/messages/{message_id}' 
    response = requests.delete(ack_url)
    #print(response.json())


def consume(queue, num_messages, partial=True):
    consume_url = f'{end_point}/queues/{queue}?num_messages={num_messages}'
    response = requests.get(consume_url)
    assert(response.status_code == 200)
    data = response.json()
    counter = 0
    if partial:
        for message in data[:len(data)//2]:
            acknowledge(message['message_id'])
    else:
        for message in data:
            acknowledge(message['message_id'])



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--threads", type=int,
                    help="Number of producer and consumer threads to run", required=True)
    parser.add_argument("-q", "--queuename", type=str,
                    help="queue name", required=True)
    parser.add_argument("-m", "--messages", type=int,
                    help="Number of messages to be published", required=True)
    
    args = parser.parse_args()
    
    queue_name = args.queuename
    thread_count = args.threads
    message_count = args.messages

    create_queue(queue_name)

    p_threads = []
    for i in range(thread_count):
        p_thread = threading.Thread(target=publish, args=(queue_name, message_count,))
        p_threads.append(p_thread)
        p_thread.start()

    for th in p_threads:
        th.join()

    print("Production complete")

    
    time.sleep(5)
    
    start = time.time()
    c_threads = []
    for i in range(thread_count):
        c_thread = threading.Thread(target=consume, args=(queue_name, message_count))
        c_threads.append(c_thread)
        c_thread.start()

    for th in c_threads:
        th.join()
    end = time.time()
    print("Execution Time:", end - start)
    time.sleep(10)
