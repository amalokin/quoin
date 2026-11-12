"""The request handler: a request in, a response out."""


def handle(request: dict) -> dict:
    """Answer one request.

    A request is a dict with a "method" and a "path"; the response is a dict with a "status" and a "body". The one
    route is the health probe, GET /health. Any other request is a 404.
    """
    if request.get("method") == "GET" and request.get("path") == "/health":
        return {"status": 200, "body": {"ok": True}}
    return {"status": 404, "body": {"error": "not found"}}
