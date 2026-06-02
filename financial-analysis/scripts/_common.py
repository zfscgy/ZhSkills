# -*- coding: utf-8 -*-
"""Shared helpers for the financial-data CLI scripts.

Network handling baked in from testing the skill:
- Windows often exposes a local cross-border proxy with an ``https://`` scheme
  (e.g. ``https://127.0.0.1:10808``). That both triggers urllib3's
  ``check_hostname requires server_hostname`` error and breaks *domestic*
  (China) endpoints, which should not be tunnelled abroad. We normalise the
  scheme to ``http://`` and try a DIRECT connection first for domestic data,
  falling back to the system proxy (and vice-versa for overseas data).
- stdout is forced to UTF-8 so Chinese output is not garbled on Windows.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# --------------------------------------------------------------------------- #
# proxy / network mode handling
# --------------------------------------------------------------------------- #
def _normalise(proxy):
    """Rewrite https:// -> http:// for loopback proxies (the common local case)."""
    if proxy and proxy.startswith("https://"):
        host = proxy[len("https://"):]
        if host.startswith(("127.0.0.1", "localhost", "::1")):
            return "http://" + host
    return proxy


def system_proxy():
    sp = urllib.request.getproxies()
    return _normalise(sp.get("https") or sp.get("http"))


def _apply_env(mode):
    """Configure proxy env vars so libraries (akshare, yfinance) follow the mode.
    mode is 'direct', a proxy URL, or None (leave env as-is)."""
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY", "no_proxy"):
        os.environ.pop(key, None)
    if mode == "direct":
        os.environ["NO_PROXY"] = "*"
        os.environ["no_proxy"] = "*"
    elif mode:
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
            os.environ[key] = mode


def network_modes(proxy=None, no_proxy=False, prefer="direct"):
    """Ordered list of network modes to try.
    prefer='direct' for domestic (China) data; prefer='proxy' for overseas."""
    if proxy:
        return [_normalise(proxy)]
    if no_proxy:
        return ["direct"]
    sp = system_proxy()
    if not sp:
        return ["direct"]
    return ["direct", sp] if prefer == "direct" else [sp, "direct"]


def _session_for_mode(mode, headers=None):
    import requests
    from requests.adapters import HTTPAdapter
    try:
        from urllib3.util.retry import Retry
    except Exception:  # pragma: no cover
        from requests.packages.urllib3.util.retry import Retry

    session = requests.Session()
    session.trust_env = False
    session.proxies = {} if mode == "direct" else {"http": mode, "https": mode}
    retry = Retry(total=4, backoff_factor=0.8,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET", "POST"])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    if headers:
        session.headers.update(headers)
    return session


def retry_call(fn, tries=3, delay=1.5):
    """Retry a callable on transient connection/proxy errors."""
    last = None
    for attempt in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt < tries - 1:
                time.sleep(delay * (attempt + 1))
    raise last


def run_lib(fn, proxy=None, no_proxy=False, prefer="direct", tries=3, delay=1.5):
    """Run a library call (akshare/yfinance) across network modes with fallback.
    Sets proxy env vars per mode so the library picks them up."""
    last = None
    for mode in network_modes(proxy, no_proxy, prefer):
        _apply_env(mode)
        try:
            return retry_call(fn, tries=tries, delay=delay)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def run_requests(fn, headers=None, proxy=None, no_proxy=False, prefer="direct"):
    """Run fn(session) across network modes with fallback. fn receives a configured
    requests.Session and should raise on failure to trigger the next mode."""
    last = None
    for mode in network_modes(proxy, no_proxy, prefer):
        _apply_env(mode)
        session = _session_for_mode(mode, headers)
        try:
            return fn(session)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


# --------------------------------------------------------------------------- #
# CLI / output helpers
# --------------------------------------------------------------------------- #
def base_parser(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--format", choices=["json", "csv"], default="json",
                   help="输出格式，默认 json")
    p.add_argument("--proxy", default=None,
                   help="强制使用该代理，如 http://127.0.0.1:10808")
    p.add_argument("--no-proxy", action="store_true", help="强制直连，不走任何代理")
    p.add_argument("--limit", type=int, default=None, help="最多输出多少行")
    return p


def emit(rows, fmt, columns=None):
    """Print a list of dicts as JSON or CSV to stdout."""
    if isinstance(rows, dict):
        rows = [rows]
    if fmt == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
        return
    if not rows:
        return
    cols = columns or list(rows[0].keys())
    writer = csv.DictWriter(sys.stdout, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)


def fail(msg, code=1):
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(code)
