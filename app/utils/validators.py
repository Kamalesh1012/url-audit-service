"""Standalone validators, kept separate from the pydantic models so
they're reusable (and independently testable) wherever a raw URL needs
checking."""

_BLOCKED_EXACT = {"localhost", "0.0.0.0"}
_BLOCKED_PREFIXES = ("127.", "10.", "192.168.", "169.254.", "172.16.", "172.17.",
                     "172.18.", "172.19.", "172.2", "172.3")


def is_blocked_host(host: str) -> bool:
    """Basic SSRF guardrail: reject loopback / private / link-local hosts."""
    host = (host or "").lower()
    if host in _BLOCKED_EXACT:
        return True
    return host.startswith(_BLOCKED_PREFIXES)
