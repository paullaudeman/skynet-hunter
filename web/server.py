#!/usr/bin/env python3
"""Phase-2 dev server ~ streams the live engine to the web HUD over SSE.

Serves web/ statically AND an /events endpoint that runs the hunt and streams each
engine event as Server-Sent Events. Stdlib only (no deps). Open the printed URL and
the HUD renders the actual engine, not the bundled JS tape ~ same renderer, a real
event source. The deterministic engine needs no API key; swapping in the live
orchestrator (real Claude) is the same StreamUI adapter, untouched.

    uv run python web/server.py                 # http://localhost:8000/?live  (deterministic)
    # add ANTHROPIC_API_KEY (.env), then open .../?live&engine=claude for real Claude agents
    PORT=9000 SPEED=0.5 uv run python web/server.py
"""
from __future__ import annotations

import json
import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

WEB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(WEB)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from skynet import scenario, simulate                  # noqa: E402
from skynet.cli import DEFAULT_CONFIG, load_config      # noqa: E402
from skynet.stream import StreamUI                       # noqa: E402
from skynet.units import build_units                     # noqa: E402

PORT = int(os.environ.get("PORT", "8000"))
SPEED = float(os.environ.get("SPEED", "1.0"))


def run_hunt(emit, scenario_name: str = "john-connor", engine: str = "sim") -> None:
    config = load_config(DEFAULT_CONFIG)
    max_cycles = config["mission"]["max_cycles"]
    if scenario_name not in scenario.SCENARIO_CHOICES:
        scenario_name = "john-connor"
    sc = scenario.build_scenario(scenario_name)
    units = build_units(config)

    if engine == "claude":
        from skynet.cli import load_dotenv
        load_dotenv()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            emit({"type": "note", "text": "no ANTHROPIC_API_KEY ~ running the deterministic engine instead"})
        else:
            import anthropic
            from skynet.orchestrator import Skynet
            ui = StreamUI(emit, speed=0.0)  # real API latency paces the stream
            ui.boot()
            client = anthropic.Anthropic()
            try:
                Skynet(client, units, sc.database(), ui, sc.target_name,
                       max_cycles, profile=sc.profile).run()
            except Exception as e:  # a refusal / API error ~ degrade, don't hang the stream
                emit({"type": "note", "text": f"live run ended ~ {type(e).__name__}: {e}"})
            return

    ui = StreamUI(emit, speed=SPEED)
    simulate.run_simulation(units, sc, ui, max_cycles)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet

    def do_GET(self):
        if urlparse(self.path).path == "/events":
            return self._sse()
        return super().do_GET()

    def _sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        def emit(ev: dict):
            self.wfile.write(f"data: {json.dumps(ev)}\n\n".encode())
            self.wfile.flush()

        q = parse_qs(urlparse(self.path).query)
        scen = q.get("scenario", ["john-connor"])[0]
        engine = q.get("engine", ["sim"])[0]
        try:
            run_hunt(emit, scen, engine)
            emit({"type": "end"})
        except (BrokenPipeError, ConnectionResetError):
            pass  # client navigated away mid-stream


def main() -> None:
    handler = partial(Handler, directory=WEB)
    httpd = ThreadingHTTPServer(("", PORT), handler)
    url = f"http://localhost:{PORT}/?live"
    print("skynet hunter ~ phase-2 stream server")
    print(f"  open   {url}")
    print("  engine: deterministic (no key) · Ctrl-C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
