SlothMQ is a pure Python fault-tolerant, high-performance message queue broker that supports large number of producers and consumers operating on queues concurrently. We support Atleast-Once Semantics while guaranteeing no data loss. 


Redis internal Data Structures to implement message Queue.
Messgaes dumped in azure files
Metadata in redis

Producers can create new queues and send new messages/tasks


Reliable ACKs to producers that task/message has been received and processed.
Consumer: At least once until acked. (Message stays in queue till ack is received, then can be deleted)
    Even if a Consumer processes a message, if no ack is received, we shall dump it back in the queue.


Moving components, easily replicable infra setup, the system should be very easy to get up and running, lightweight setup.
