import time

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app import auth
from app.main import create_app
from app.settings import Settings


def make(tmp_path, user="mogie", password="secret"):
    settings = Settings(data_dir=tmp_path, admin_username=user, admin_password=password)
    return TestClient(create_app(settings)), settings


def login(client, user="mogie", password="secret"):
    return client.post("/api/login", json={"username": user, "password": password})


def test_page_is_served(tmp_path):
    client, _ = make(tmp_path)
    r = client.get("/")
    assert r.status_code == 200
    assert "Foundry VTT MCP &amp; Rest Relay" in r.text


def test_session_says_not_configured_without_login(tmp_path):
    client, _ = make(tmp_path, user="", password="")
    body = client.get("/api/session").json()
    assert body["configured"] is False
    assert body["loggedIn"] is False


def test_login_refused_when_not_configured(tmp_path):
    client, _ = make(tmp_path, user="", password="")
    r = login(client)
    assert r.status_code == 403
    assert "Configuration" in r.json()["detail"]


def test_wrong_password_rejected(tmp_path):
    client, _ = make(tmp_path)
    assert login(client, password="nope").status_code == 401


def test_status_needs_login(tmp_path):
    client, _ = make(tmp_path)
    assert client.get("/api/status").status_code == 401
    assert client.get("/api/connect").status_code == 401
    assert client.post("/api/ping").status_code == 401


def test_login_then_status(tmp_path):
    client, _ = make(tmp_path)
    assert login(client).status_code == 200
    assert client.get("/api/session").json()["loggedIn"] is True
    s = client.get("/api/status").json()
    assert s["relay"] == "up"
    assert s["clients"] == []


def test_logout(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    client.post("/api/logout")
    assert client.get("/api/status").status_code == 401


def test_lockout_after_five_wrong_tries(tmp_path):
    client, _ = make(tmp_path)
    for _ in range(5):
        assert login(client, password="bad").status_code == 401
    assert login(client, password="bad").status_code == 429
    assert login(client).status_code == 429  # even the right password waits


def test_connect_info_builds_wss_behind_proxy(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    r = client.get("/api/connect", headers={"x-forwarded-proto": "https", "host": "relay.example.com"})
    body = r.json()
    assert body["url"] == "wss://relay.example.com/ws/module"
    assert body["key"].startswith("fga_")


def test_connect_info_keeps_path_prefix_behind_proxy(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    r = client.get("/api/connect", headers={"x-forwarded-proto": "https", "host": "vtt.example.com", "x-forwarded-prefix": "/relay"})
    assert r.json()["url"] == "wss://vtt.example.com/relay/ws/module"


def test_connect_info_from_the_sidebar_points_at_the_relay_port(tmp_path):
    client, settings = make(tmp_path)
    login(client)
    r = client.get("/api/connect", headers={"x-ingress-path": "/api/hassio_ingress/abc", "host": "ha.example.com:8123"})
    assert r.json()["url"] == f"ws://ha.example.com:{settings.port}/ws/module"


def test_page_uses_relative_api_paths():
    from app.main import STATIC
    html = (STATIC / "index.html").read_text(encoding="utf-8")
    assert 'api("/api/' not in html


def test_connect_key_is_stable_and_can_be_replaced(tmp_path):
    client, settings = make(tmp_path)
    login(client)
    first = client.get("/api/connect").json()["key"]
    again, _ = make(tmp_path)
    login(again)
    assert again.get("/api/connect").json()["key"] == first  # survives restart
    new = client.post("/api/connect/regenerate").json()["key"]
    assert new != first


def test_socket_rejects_wrong_key(tmp_path):
    client, _ = make(tmp_path)
    with client.websocket_connect("/ws/module?key=wrong") as ws:
        with pytest.raises(WebSocketDisconnect) as info:
            ws.receive_json()
    assert info.value.code == 4401


def test_socket_needs_hello_first(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    key = client.get("/api/connect").json()["key"]
    with client.websocket_connect(f"/ws/module?key={key}") as ws:
        ws.send_json({"type": "heartbeat"})
        with pytest.raises(WebSocketDisconnect) as info:
            ws.receive_json()
    assert info.value.code == 4400


def test_session_cookie_helpers():
    cookie = auth.make_session("s3", "mogie", now=1000)
    assert auth.read_session("s3", cookie, now=1001) == "mogie"
    assert auth.read_session("other", cookie, now=1001) is None
    assert auth.read_session("s3", cookie, now=1000 + auth.SESSION_SECONDS + 1) is None
    assert auth.read_session("s3", "junk") is None
    assert auth.read_session("s3", None) is None


# ----- many Foundry servers -----


def test_first_run_turns_old_key_into_main_connection(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    old = client.get("/api/connect").json()["key"]
    conns = client.get("/api/connections").json()["connections"]
    assert [c["name"] for c in conns] == ["Main"]
    assert conns[0]["key"] == old


def test_connections_need_login(tmp_path):
    client, _ = make(tmp_path)
    assert client.get("/api/connections").status_code == 401
    assert client.post("/api/connections", json={"name": "x"}).status_code == 401


def test_add_rename_regenerate_remove(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    made = client.post("/api/connections", json={"name": "Second server"}).json()
    assert made["key"].startswith("fga_") and made["url"].startswith("ws")
    assert client.post("/api/connections", json={"name": "second SERVER"}).status_code == 400  # same name
    assert client.post("/api/connections", json={"name": "  "}).status_code == 400
    renamed = client.patch(f"/api/connections/{made['id']}", json={"name": "Game night"}).json()
    assert renamed["name"] == "Game night"
    fresh = client.post(f"/api/connections/{made['id']}/regenerate").json()
    assert fresh["key"] != made["key"]
    assert client.delete(f"/api/connections/{made['id']}").status_code == 200
    assert client.delete(f"/api/connections/{made['id']}").status_code == 404
    assert [c["name"] for c in client.get("/api/connections").json()["connections"]] == ["Main"]


def test_connections_survive_restart(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    made = client.post("/api/connections", json={"name": "Second"}).json()
    again, _ = make(tmp_path)
    login(again)
    keys = {c["name"]: c["key"] for c in again.get("/api/connections").json()["connections"]}
    assert keys["Second"] == made["key"]


def test_each_key_only_opens_its_own_connection(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    main = client.get("/api/connections").json()["connections"][0]
    other = client.post("/api/connections", json={"name": "Other"}).json()
    with client.websocket_connect(f"/ws/module?key={main['key']}") as a, client.websocket_connect(f"/ws/module?key={other['key']}") as b:
        a.send_json({"type": "hello", "clientId": "one", "worldId": "w1", "worldTitle": "World One"})
        b.send_json({"type": "hello", "clientId": "two", "worldId": "w2", "worldTitle": "World Two"})
        assert a.receive_json()["type"] == "welcome"
        assert b.receive_json()["type"] == "welcome"
        cards = {c["name"]: c for c in client.get("/api/status").json()["connections"]}
        assert [x["clientId"] for x in cards["Main"]["clients"]] == ["one"]
        assert [x["clientId"] for x in cards["Other"]["clients"]] == ["two"]
        assert {c["connection"] for c in client.get("/api/status").json()["clients"]} == {"Main", "Other"}


def test_new_key_only_drops_that_connection(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    main = client.get("/api/connections").json()["connections"][0]
    other = client.post("/api/connections", json={"name": "Other"}).json()
    with client.websocket_connect(f"/ws/module?key={main['key']}") as a, client.websocket_connect(f"/ws/module?key={other['key']}") as b:
        a.send_json({"type": "hello", "clientId": "one"})
        b.send_json({"type": "hello", "clientId": "two"})
        a.receive_json(); b.receive_json()
        client.post(f"/api/connections/{other['id']}/regenerate")
        with pytest.raises(WebSocketDisconnect) as info:
            b.receive_json()
        assert info.value.code == 4401
        a.send_json({"type": "heartbeat"})
        assert a.receive_json()["type"] == "heartbeat"  # the other server is untouched


def test_removed_connection_key_stops_working(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    other = client.post("/api/connections", json={"name": "Other"}).json()
    client.delete(f"/api/connections/{other['id']}")
    with client.websocket_connect(f"/ws/module?key={other['key']}") as ws:
        with pytest.raises(WebSocketDisconnect) as info:
            ws.receive_json()
    assert info.value.code == 4401


def test_ping_can_target_one_connection(tmp_path):
    client, _ = make(tmp_path)
    login(client)
    r = client.post("/api/ping?connection_id=nope")
    assert r.status_code == 502 and "on that connection" in r.json()["detail"]
