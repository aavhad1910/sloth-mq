from sys import stderr
import time
import requests
import string
import threading
from messaging import MessagingManagerFactory

end_point = "http://20.121.83.214:3000"


def publish_task(queue):
    publish_url = f'{end_point}/queues/{queue}'        
    response = requests.post(publish_url)
    print(response.content, file=stderr)


def fetch_queue_list():
    messaging = MessagingManagerFactory.get_messaging_manager()
    queues = messaging.get_all_queues()
    return queues

def schedule():
    print("SCHEDULER STARTED", file=stderr)
    cc = 0
    while(True):
        queues = fetch_queue_list()      
        for q in queues:
            print(f'For queue {q}, cleanup invoked.')
            publish_task(q)        
        time.sleep(2)
        print("Cycle Number {cc} complete".format(cc=cc), file=stderr)
        cc+=1
        
schedule()
