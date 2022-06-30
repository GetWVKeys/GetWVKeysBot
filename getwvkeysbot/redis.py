from enum import Enum
import json
import random
import redis

from getwvkeysbot.config import REDIS_URI


class OPCode(Enum):
    DISABLE_USER = 0
    DISABLE_USER_BULK = 1
    ENABLE_USER = 2
    KEY_COUNT = 3
    USER_COUNT = 4
    SEARCH = 5
    UPDATE_PERMISSIONS = 6
    QUARANTINE = 7
    REPLY = 8


redis_cli = redis.Redis.from_url(REDIS_URI, decode_responses=True, encoding="utf8")

p = redis_cli.pubsub(ignore_subscribe_messages=True)


# def redis_message_handler(msg):
#     try:
#         data = json.loads(msg.get("data"))
#         op = data.get("op")
#         d = data.get("d")

#         if not op in OPCode:
#             r = {"op": -1, "d": "Invalid OP code"}
#             redis_cli.publish("api", json.dumps(r))
#             return

#         print("Recieved OP Code {}".format(op))

#     except json.JSONDecodeError as e:
#         print(e)


# p.subscribe(**{"bot": redis_message_handler})
# redis_thread = p.run_in_thread(daemon=True)


def make_api_request(action: OPCode, data={}):
    reply_address = "api-" + str(random.randint(1000, 9999))
    p.subscribe(reply_address)
    payload = {"op": action.value, "d": data, "reply_to": reply_address}

    redis_cli.publish("api", json.dumps(payload))
    for message in p.listen():
        print(message)
        if message["type"] == "message":
            p.unsubscribe(reply_address)
            return json.loads(message["data"])["d"]["message"]
