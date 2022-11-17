"""
 This file is part of the GetWVKeys project (https://github.com/GetWVKeys/getwvkeys)
 Copyright (C) 2022 Notaghost, Puyodead1 and GetWVKeys contributors 
 
 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published
 by the Free Software Foundation, version 3 of the License.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import ast
import asyncio
import json
import threading
import time
import uuid
from time import sleep

import pika
from pika import channel, spec

from getwvkeysbot.config import RABBIT_URI
from getwvkeysbot.utils import OPCode, logger


class RpcClient(object):
    """Asynchronous Rpc client."""

    internal_lock = threading.Lock()
    queue = {}

    def __init__(self, rpc_queue):
        logger.info("[RabbitMQ] Initializing RPC client")

        self.rpc_queue = rpc_queue
        self.connection = pika.BlockingConnection(parameters=pika.URLParameters(RABBIT_URI))
        self.channel = self.connection.channel()
        result = self.channel.queue_declare(queue=self.rpc_queue, exclusive=True)
        self.callback_queue = result.method.queue
        thread = threading.Thread(target=self._process_data_events)
        thread.setDaemon(True)
        thread.start()

    def _process_data_events(self):
        self.channel.basic_consume(self.callback_queue, on_message_callback=self._on_response, auto_ack=True)
        while True:
            with self.internal_lock:
                self.connection.process_data_events()
                sleep(0.1)

    def _on_response(self, ch: channel.Channel, method, props: spec.BasicProperties, body):
        self.queue[props.correlation_id] = body
        # TODO: process global incoming messages

    def send_request(self, payload):
        corr_id = str(uuid.uuid4())
        self.queue[corr_id] = None
        with self.internal_lock:
            self.channel.basic_publish(
                exchange="",
                routing_key="rpc_api_queue_development",
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=corr_id,
                ),
                body=payload,
            )
        return corr_id

    def publish_reply(self, ch: channel.Channel, props: spec.BasicProperties, payload):
        """
        Replies to the API queue
        """
        ch.basic_publish(exchange="", routing_key=props.reply_to, properties=pika.BasicProperties(correlation_id=props.correlation_id), body=str(payload))

    def publish_error(self, ch: channel.Channel, props: spec.BasicProperties, e):
        """
        Publishes an error response to the API queue
        """
        payload = {"op": -1, "d": {"error": True, "message": e}}
        self.publish_reply(ch, props, payload)

    def publish_response(self, ch: channel.Channel, props: spec.BasicProperties, msg=None):
        """
        Publishes a response to the API queue
        """
        payload = {"op": OPCode.REPLY.value, "d": {"error": False, "message": msg}}
        self.publish_reply(ch, props, payload)

    async def get_response(self, corr_id):
        """Get the response from the queue."""
        start_time = time.time()
        while self.queue[corr_id] is None:
            await asyncio.sleep(0.1)
            now = time.time()
            # timeout after 5 seconds
            if now - start_time > 5:
                raise Exception("Timeout")
        msg = self.queue[corr_id]
        msg = msg.decode("utf-8")
        logger.info("[RabbitMQ] Got response: %s", msg)
        data = ast.literal_eval(msg)
        op = data.get("op")
        d = data.get("d")
        rmsg = d.get("message")
        if op == OPCode.ERROR.value:
            raise Exception(rmsg)
        return rmsg

    async def publish_packet(self, op: OPCode, data: dict = {}):
        payload = {"op": op.value, "d": data}
        corr_id = self.send_request(json.dumps(payload))
        res = await self.get_response(corr_id)
        return res
