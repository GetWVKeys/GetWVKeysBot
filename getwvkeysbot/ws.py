import ast
import asyncio
import json
import time
import uuid

import websockets

from getwvkeysbot.utils import OPCode


class WebSocketClient:
    def __init__(self, host: str, port: str) -> None:
        self.host = host
        self.port = port
        self.server = None
        self.queue = {}
        self.websocket: websockets.WebSocketClientProtocol = None

    async def connect(self):
        uri = f"ws://{self.host}:{self.port}"
        self.websocket = await websockets.connect(uri)
        print(f"Connected to WebSocket server at {uri}")

        # start listening for messages
        asyncio.ensure_future(self.receive_message())

    def disconnect(self):
        self.websocket.close()

    async def receive_message(self):
        print("listening for messages")
        while True:
            message = await self.websocket.recv()
            try:
                data = json.loads(message)
                req_id = data.get("req_id")
                self.queue[req_id] = data
            except json.JSONDecodeError:
                print("invalid json received")

    def publish_error(self, req_id: str, e):
        """
        Publishes an error response
        """
        print("publishing error")
        payload = {"op": -1, "d": {"error": True, "message": e}, "req_id": req_id}
        self.websocket.send(json.dumps(payload))

    def publish_response(self, req_id: str, msg=None):
        """
        Publishes a response
        """
        print("publishing response")
        payload = {
            "op": OPCode.REPLY.value,
            "d": {"error": False, "message": msg},
            "req_id": req_id,
        }
        self.websocket.send(json.dumps(payload))

    async def get_response(self, req_id):
        start_time = time.time()
        while self.queue[req_id] is None:
            await asyncio.sleep(0.1)
            now = time.time()
            # timeout after 5 seconds
            if now - start_time > 5:
                # remove the request from the queue
                del self.queue[req_id]
                raise Exception("Timeout")
        reply = self.queue[req_id]
        op = reply.get("op")
        d = reply.get("d")
        rmsg = d.get("message")
        if op == OPCode.ERROR.value:
            raise Exception(rmsg)
        return rmsg

    async def make_api_request(self, action: OPCode, data={}):
        req_id = str(uuid.uuid4())
        self.queue[req_id] = None
        payload = {"op": action.value, "d": data, "req_id": req_id}
        await self.websocket.send(json.dumps(payload))
        res = await self.get_response(req_id)
        return res
