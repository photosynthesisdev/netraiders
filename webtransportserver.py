#!/usr/bin/env python3

# Based off of Googles WebtransportServer in Chromium Docs.

"""
An example WebTransport over HTTP/3 server based on the aioquic library.
Processes incoming streams and datagrams, and
replies with the ASCII-encoded length of the data sent in bytes.
Example use:
  python3 webtransport_server.py certificate.pem certificate.key
Example use from JavaScript:
  let transport = new WebTransport("https://localhost:4433/counter");
  await transport.ready;
  let stream = await transport.createBidirectionalStream();
  let encoder = new TextEncoder();
  let writer = stream.writable.getWriter();
  await writer.write(encoder.encode("Hello, world!"))
  writer.close();
  console.log(await new Response(stream.readable).text());
This will output "13" (the length of "Hello, world!") into the console.
"""

import argparse
import asyncio
import logging
from collections import defaultdict
from typing import Dict, Optional

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import H3Event, HeadersReceived, WebTransportStreamDataReceived, DatagramReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.connection import stream_is_unidirectional
from aioquic.quic.events import ProtocolNegotiated, StreamReset, QuicEvent

import json

BIND_ADDRESS = 'dilate.ai'
BIND_PORT = 4433
logger = logging.getLogger(__name__)

class CounterHandler:

    def __init__(self, session_id, http: H3Connection) -> None:
        self._session_id = session_id
        self._http = http
        self._counters = defaultdict(int)
        self._iterator = 0

    def h3_event_received(self, event: H3Event) -> None:
        if isinstance(event, DatagramReceived):
            # logic here for processing new player inputs
            #received_data = json.loads(event.data)
            self._iterator += 1
            payload = str(f"ACK: {self._iterator}").encode('ascii')
            self._http.send_datagram(self._session_id, payload)

    def stream_closed(self, stream_id: int) -> None:
        try:
            del self._counters[stream_id]
        except KeyError:
            pass


# WebTransportProtocol handles the beginning of a WebTransport connection: it
# responses to an extended CONNECT method request, and routes the transport
# events to a relevant handler (in this example, CounterHandler).
class WebTransportProtocol(QuicConnectionProtocol):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._http: Optional[H3Connection] = None
        self._handler: Optional[CounterHandler] = None

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, ProtocolNegotiated):
            self._http = H3Connection(self._quic, enable_webtransport=True)
        elif isinstance(event, StreamReset) and self._handler is not None:
            # Streams in QUIC can be closed in two ways: normal (FIN) and
            # abnormal (resets).  FIN is handled by the handler; the code
            # below handles the resets.
            self._handler.stream_closed(event.stream_id)

        if self._http is not None:
            for h3_event in self._http.handle_event(event):
                self._h3_event_received(h3_event)

    def _h3_event_received(self, event: H3Event) -> None:
        if isinstance(event, HeadersReceived):
            headers = {}
            for header, value in event.headers:
                headers[header] = value
            if (headers.get(b":method") == b"CONNECT" and
                    headers.get(b":protocol") == b"webtransport"):
                self._handshake_webtransport(event.stream_id, headers)
            else:
                self._send_response(event.stream_id, 400, end_stream=True)

        if self._handler:
            self._handler.h3_event_received(event)

    def _handshake_webtransport(self,
                                stream_id: int,
                                request_headers: Dict[bytes, bytes]) -> None:
        authority = request_headers.get(b":authority")
        path = request_headers.get(b":path")
        if authority is None or path is None:
            # `:authority` and `:path` must be provided.
            self._send_response(stream_id, 400, end_stream=True)
            return
        if path == b"/counter":
            assert(self._handler is None)
            self._handler = CounterHandler(stream_id, self._http)
            self._send_response(stream_id, 200)
        else:
            self._send_response(stream_id, 404, end_stream=True)

    def _send_response(self,
                       stream_id: int,
                       status_code: int,
                       end_stream=False) -> None:
        headers = [(b":status", str(status_code).encode())]
        if status_code == 200:
            headers.append((b"sec-webtransport-http3-draft", b"draft02"))
        self._http.send_headers(
            stream_id=stream_id, headers=headers, end_stream=end_stream)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('certificate')
    parser.add_argument('key')
    args = parser.parse_args()

    configuration = QuicConfiguration(
        alpn_protocols=H3_ALPN,
        is_client=False,
        max_datagram_frame_size=65536,
    )
    configuration.load_cert_chain(args.certificate, args.key)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        serve(
            BIND_ADDRESS,
            BIND_PORT,
            configuration=configuration,
            create_protocol=WebTransportProtocol,
        )
    )
    try:
        print(
            "Listening on https://{}:{}".format(BIND_ADDRESS, BIND_PORT))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
