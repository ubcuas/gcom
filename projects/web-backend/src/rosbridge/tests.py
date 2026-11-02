import asyncio
import json
from unittest.mock import patch

from django.test import AsyncClient, SimpleTestCase
from websockets.asyncio.server import serve

from .client import RosbridgeClient, RosbridgeError, RosbridgeTimeout


class FakeRosbridge:
    """Minimal rosbridge server: records call_service messages and answers via `responder`."""

    def __init__(self, responder):
        self.responder = responder
        self.calls = []

    async def _handler(self, ws):
        async for raw in ws:
            message = json.loads(raw)
            self.calls.append(message)
            reply = self.responder(message)
            if reply is not None:
                await ws.send(json.dumps({"op": "service_response", "id": message["id"], **reply}))

    async def __aenter__(self):
        self._server = await serve(self._handler, "127.0.0.1", 0)
        port = self._server.sockets[0].getsockname()[1]
        self.url = f"ws://127.0.0.1:{port}"
        return self

    async def __aexit__(self, *exc):
        self._server.close()
        await self._server.wait_closed()


def ok(message="done"):
    return lambda _msg: {"result": True, "values": {"success": True, "message": message}}


class RosbridgeClientTest(SimpleTestCase):
    async def test_call_returns_values_and_reuses_connection(self):
        async with FakeRosbridge(ok()) as server:
            client = RosbridgeClient(server.url)
            first = await client.call_service("/a", {"x": 1})
            ws = client._ws
            await client.call_service("/b")
            self.assertIs(client._ws, ws)
        self.assertEqual(first, {"success": True, "message": "done"})
        self.assertEqual([c["service"] for c in server.calls], ["/a", "/b"])
        self.assertEqual(server.calls[0]["args"], {"x": 1})

    async def test_concurrent_calls_matched_by_id(self):
        async with FakeRosbridge(
            lambda m: {"result": True, "values": {"service": m["service"]}}
        ) as server:
            client = RosbridgeClient(server.url)
            results = await asyncio.gather(*(client.call_service(f"/s{i}") for i in range(5)))
        self.assertEqual([r["service"] for r in results], [f"/s{i}" for i in range(5)])

    async def test_rosbridge_failure_raises(self):
        async with FakeRosbridge(lambda _m: {"result": False, "values": "no such service"}) as server:
            with self.assertRaisesRegex(RosbridgeError, "no such service"):
                await RosbridgeClient(server.url).call_service("/missing")

    async def test_timeout(self):
        async with FakeRosbridge(lambda _m: None) as server:
            with self.assertRaises(RosbridgeTimeout):
                await RosbridgeClient(server.url).call_service("/slow", timeout=0.2)

    async def test_unreachable(self):
        with self.assertRaisesRegex(RosbridgeError, "cannot connect"):
            await RosbridgeClient("ws://127.0.0.1:1").call_service("/x")

    async def test_reconnects_after_server_restart(self):
        async with FakeRosbridge(ok()) as server:
            client = RosbridgeClient(server.url)
            await client.call_service("/a")
        # Server gone: the reader notices the close and the next call fails to reconnect.
        await asyncio.sleep(0.05)
        self.assertIsNone(client._ws)
        async with FakeRosbridge(ok("again")) as server2:
            client.url = server2.url
            self.assertEqual((await client.call_service("/a"))["message"], "again")


class RosbridgeEndpointTest(SimpleTestCase):
    async def _post(self, server, path, body=None):
        with patch("rosbridge.views.get_client", return_value=RosbridgeClient(server.url)):
            return await AsyncClient().post(
                f"/api/rosbridge/{path}", json.dumps(body or {}), content_type="application/json"
            )

    async def test_endpoints_map_to_services(self):
        cases = [
            ("prepare_takeoff", {"altitude": 10}, "takeoff", {"takeoff_altitude": 10.0, "waypoints": []}),
            ("set_mode", {"mode": "guided"}, "set_mode", {"mode": "GUIDED"}),
            ("arm", {"arm": True}, "arm", {"data": True}),
            ("start_mission", None, "start_mission", {}),
            ("rtl", None, "land", {}),
        ]
        for path, body, service, args in cases:
            async with FakeRosbridge(ok()) as server:
                response = await self._post(server, path, body)
            with self.subTest(path=path):
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"success": True, "message": "done"})
                self.assertEqual(server.calls[0]["service"], f"/flight_commander/{service}")
                self.assertEqual(server.calls[0]["args"], args)

    async def test_service_reported_failure_is_502(self):
        async with FakeRosbridge(
            lambda _m: {"result": True, "values": {"success": False, "message": "not armed"}}
        ) as server:
            response = await self._post(server, "start_mission")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["message"], "not armed")

    async def test_invalid_input_is_400(self):
        async with FakeRosbridge(ok()) as server:
            for path, body in [("prepare_takeoff", {"altitude": 0}), ("set_mode", {}), ("arm", {"arm": "yes"})]:
                with self.subTest(path=path):
                    self.assertEqual((await self._post(server, path, body)).status_code, 400)
        self.assertEqual(server.calls, [])

    async def test_unreachable_is_503(self):
        with patch("rosbridge.views.get_client", return_value=RosbridgeClient("ws://127.0.0.1:1")):
            response = await AsyncClient().post("/api/rosbridge/rtl")
        self.assertEqual(response.status_code, 503)
