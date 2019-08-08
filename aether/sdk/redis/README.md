# Redis Helper
This provides an interface to a Redis server via supplied redis parameters.

It makes available a number of `CRUD` redis operation which include but not limited to:
    - Formats document keys into `_{type}:{tenant}:{id}` before being cached on redis.
    - Retrieves documents based on preformated keys.
    - Removes documents based on preformated keys.
    - Subscribes to key based channels with a callback function.

## Usage

```
from aether.sdk.redis.task import TaskHelper

REDIS_TASK = TaskHelper(settings, redis_instance)

# Settings must have the following properties:
# REDIS_HOST str - Redis server host,
# REDIS_PORT int - Redis server port,
# REDIS_PASSWORD str - Redis server password,
# REDIS_DB str - Redis database name

# redis_instance (Optional) - Pass an existing redis connection
# (If provided, ignores all settings and uses redis_instance)

document = {
    'id': 'document_id',
    'name': 'document name'
}

document_type = 'test_document'
aether_tenant = 'prod'

# add document to redis
REDIS_TASK.add(task=document, type=document_type, tenant=aether_tenant)

# retrieve document from redis
REDIS_TASK.get(_id=document['id'], type=document_type, tenant=aether_tenant)

# subcribe to a key based channel

CHANNEL = '_test_document*' # listens for messages published to all channels starting with '_test_document'

def handle_callback(msg):
    print(msg) # handle returned message

REDIS_TASK.subscribe(callback=handle_callback, pattern=CHANNEL, keep_alive=True)


# publish document
REDIS_TASK.publish(task=document, type=document_type, tenant=aether_tenant) # this will trigger the 'handle_callback' function with the published document to all subscribed clients
```