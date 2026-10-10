"""The live Anthropic client, with a tap on the last raw reply.

A commander refusal can arrive two ways. Either the reply is clean and
`messages.parse` hands back `parsed_output=None` with `stop_reason == "refusal"`,
or the refusal lands mid-answer and the SDK raises while parsing the cut-off
JSON. In the second case the SDK never returns the reply, so the orchestrator
could not tell a refusal from any other parse failure.

The tap fixes that: an httpx response hook keeps the last /v1/messages body on
`client.last_reply`, so `Skynet.decide()` can read `stop_reason`,
`stop_details.category` and `usage` even when parsing failed. Same idea as the
benchmark's RecordingClient (bench/run_bench.py), kept small for product code.
"""

from __future__ import annotations

from typing import Any


def make_client(**kwargs: Any):
    """An `anthropic.Anthropic` whose last /v1/messages reply body is on `.last_reply`."""
    import anthropic
    import httpx

    client: Any = None

    def hook(resp: httpx.Response) -> None:
        if resp.request.url.path.endswith("/messages"):
            resp.read()
            try:
                client.last_reply = resp.json()
            except Exception:
                client.last_reply = None

    transport = kwargs.pop("transport", None)  # tests pass an httpx.MockTransport
    http_client = httpx.Client(event_hooks={"response": [hook]}, timeout=600, transport=transport)
    client = anthropic.Anthropic(http_client=http_client, **kwargs)
    client.last_reply = None
    return client
