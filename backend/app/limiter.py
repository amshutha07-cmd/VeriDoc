from slowapi import Limiter
from starlette.requests import Request


def client_ip(request: Request) -> str:
    """Cloud Run sits behind Google's proxy, so read the forwarded address.
    The last entry is the one Google adds; earlier entries can be written by the caller."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip)
