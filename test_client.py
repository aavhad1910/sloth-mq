import requests
import string
import time
import threading


end_point = "http://20.85.209.0:3000"

def publish(queue):
    for _ in range(5):
        publish_url = f'{end_point}/queues/{queue}'
        
        for message in string.ascii_uppercase:
            response = requests.post(publish_url, json={"message": message})
            print(response.json())
            
        
def create_queue(queue_name):
    create_queue_url = f'{end_point}/queues'
    response = requests.post(create_queue_url, json={"name": queue_name})
    print(response.json())


def acknowledge(message_id):
    ack_url = f'{end_point}/messages/{message_id}' 
    response = requests.delete(ack_url)
    print(response.json())


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


queue_name = "dt_27"
create_queue(queue_name)

p_threads = []
for i in range(1):
    p_thread = threading.Thread(target=publish, args=(queue_name, ))
    p_threads.append(p_thread)
    p_thread.start()

for th in p_threads:
    th.join()

print("Production complete")

while True:
    time.sleep(30)

# c_threads = []
# for i in range(50):
#     c_thread = threading.Thread(target=consume, args=(queue_name, 30))
#     c_threads.append(c_thread)
#     c_thread.start()

# for th in c_threads:
#     th.join()

# time.sleep(10)


# f_threads = []
# for i in range(50):
#     f_thread = threading.Thread(target=consume, args=(queue_name, 30, False))
#     f_threads.append(f_thread)
#     f_threads.start()

# for th in f_threads:
#     th.join()
