import json
from unittest.mock import Mock, patch

import requests
from django.test import Client, SimpleTestCase, override_settings


def acms_reply(status=200, body=None, text=None):
    response = Mock(status_code=status, text=text if text is not None else json.dumps(body))
    response.json.side_effect = (lambda: body) if body is not None else ValueError("not json")
    return response


@override_settings(ACMS_COMMANDS_URL="http://acms:8091/")
class AcmsCommandsTest(SimpleTestCase):
    def _post(self, path, body=None, reply=None, error=None):
        with patch("acms_commands.views.requests.post") as post:
            post.return_value = reply or acms_reply(body={"success": True, "message": "done"})
            post.side_effect = error
            response = Client().post(
                f"/api/acms/{path}", json.dumps(body) if body is not None else "", content_type="application/json"
            )
        return response, post

    def test_endpoints_forward_body_to_acms(self):
        cases = [
            ("prepare_takeoff", {"altitude": 10}),
            ("add_route", {"waypoints": [{"latitude": 49.1, "longitude": -123.1, "altitude": 30}], "append": True}),
            ("set_mode", {"mode": "guided"}),
            ("arm", {"arm": True}),
            ("start_mission", None),
            ("rtl", None),
        ]
        for path, body in cases:
            with self.subTest(path=path):
                response, post = self._post(path, body)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"success": True, "message": "done"})
                self.assertEqual(post.call_args.args[0], f"http://acms:8091/{path}")
                sent = post.call_args.kwargs["data"]
                self.assertEqual(json.loads(sent) if sent else None, body)

    def test_acms_status_and_message_relayed(self):
        for status in (400, 502, 503, 504):
            with self.subTest(status=status):
                reply = acms_reply(status, {"success": False, "message": "not armed"})
                response, _ = self._post("start_mission", reply=reply)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json(), {"success": False, "message": "not armed"})

    def test_unreachable_is_503(self):
        response, _ = self._post("rtl", error=requests.ConnectionError("refused"))
        self.assertEqual(response.status_code, 503)
        self.assertIn("cannot reach ACMS", response.json()["message"])

    def test_timeout_is_504(self):
        response, _ = self._post("rtl", error=requests.ReadTimeout())
        self.assertEqual(response.status_code, 504)

    def test_non_json_reply_is_502(self):
        response, _ = self._post("rtl", reply=acms_reply(500, text="Internal Server Error"))
        self.assertEqual(response.status_code, 502)
        self.assertFalse(response.json()["success"])

    def test_get_not_allowed(self):
        self.assertEqual(Client().get("/api/acms/rtl").status_code, 405)
