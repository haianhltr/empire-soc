#!/usr/bin/env python3
"""
capture_ws_cdp.py
-----------------
Attach to a running Chrome instance via the Chrome DevTools Protocol (CDP),
enable the Network domain, and print WebSocket frames in real time.

USAGE (examples):
    # Basic (Chrome must be started with --remote-debugging-port=9222)
    python capture_ws_cdp.py

    # Pick a specific tab by title substring
    python capture_ws_cdp.py --match-title "CSGO" 

    # Pick by URL substring and only show a specific socket URL pattern
    python capture_ws_cdp.py --match-url "example.com" --only-socket-contains "/trade"

    # Save everything to a JSONL file
    python capture_ws_cdp.py --save ws_dump.jsonl

Start Chrome on Windows with your real profile:
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^
      --remote-debugging-port=9222 ^
      --user-data-dir="C:\\Users\\haian\\AppData\\Local\\Google\\Chrome\\User Data" ^
      --profile-directory="Default"
"""

import argparse
import base64
import json
import sys
import time
from datetime import datetime
from typing import Optional, Dict

import requests
from websocket import create_connection, WebSocketException

DEFAULT_DEVTOOLS = "http://127.0.0.1:{port}/json"


def pick_target_ws_url(port: int, match_title: Optional[str], match_url: Optional[str]) -> Optional[str]:
    """Return the CDP websocket debugger URL for a tab that matches title/url substrings."""
    info_url = DEFAULT_DEVTOOLS.format(port=port)
    tabs = requests.get(info_url, timeout=5).json()
    # Prefer page targets (type = 'page')
    def score(t):
        s = 0
        if t.get("type") == "page":
            s += 2
        title = (t.get("title") or "").lower()
        url = (t.get("url") or "").lower()
        if match_title and match_title.lower() in title:
            s += 3
        if match_url and match_url.lower() in url:
            s += 3
        return s

    tabs_sorted = sorted(tabs, key=score, reverse=True)
    if not tabs_sorted:
        return None

    # If user provided a filter, ensure top result actually matched
    top = tabs_sorted[0]
    if match_title or match_url:
        title = (top.get("title") or "").lower()
        url = (top.get("url") or "").lower()
        ok_title = (not match_title) or (match_title.lower() in title)
        ok_url = (not match_url) or (match_url.lower() in url)
        if not (ok_title and ok_url):
            return None

    return top.get("webSocketDebuggerUrl")


def pretty_ts(chrome_ts: Optional[float] = None) -> str:
    """Human-readable timestamp. If chrome_ts is provided (seconds), include it."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
    if chrome_ts is not None:
        return f"{now} (chrome_ts={chrome_ts:.6f})"
    return now


def shorten(s: str, n: int = 300) -> str:
    if s is None:
        return ""
    if len(s) <= n:
        return s
    return s[:n] + f"... <{len(s)-n} more>"


def main():
    ap = argparse.ArgumentParser(description="Capture WebSocket frames via Chrome DevTools Protocol.")
    ap.add_argument("--port", type=int, default=9222, help="Remote debugging port (default: 9222)")
    ap.add_argument("--match-title", type=str, default=None, help="Pick tab whose TITLE contains this substring")
    ap.add_argument("--match-url", type=str, default=None, help="Pick tab whose URL contains this substring")
    ap.add_argument("--only-socket-contains", type=str, default=None,
                    help="Only print frames for WebSocket URLs containing this substring")
    ap.add_argument("--save", type=str, default=None, help="Path to JSONL file to save events")
    ap.add_argument("--show-sent", action="store_true", help="Also print frames sent from browser -> server")
    args = ap.parse_args()

    # 1) Find the target tab's CDP websocket URL
    try:
        ws_debug_url = pick_target_ws_url(args.port, args.match_title, args.match_url)
    except Exception as e:
        print(f"[ERROR] Could not query DevTools at http://127.0.0.1:{args.port}/json : {e}")
        sys.exit(1)

    if not ws_debug_url:
        print("[ERROR] No matching Chrome tab found. "
              "Make sure Chrome is running with --remote-debugging-port "
              "and open the page that has the WebSocket.")
        sys.exit(2)

    print(f"[INFO] Connecting to CDP: {ws_debug_url}")

    # 2) Connect to CDP and enable Network domain
    try:
        cdp = create_connection(ws_debug_url, timeout=10)
    except Exception as e:
        print(f"[ERROR] Could not connect to CDP websocket: {e}")
        sys.exit(3)

    id_counter = [1]

    def send(method, params=None):
        msg = {"id": id_counter[0], "method": method}
        if params:
            msg["params"] = params
        cdp.send(json.dumps(msg))
        id_counter[0] += 1

    # map requestId -> websocket URL
    ws_url_by_req: Dict[str, str] = {}

    # open file if saving
    f_out = None
    if args.save:
        f_out = open(args.save, "a", encoding="utf-8")
        print(f"[INFO] Saving events to {args.save} (JSONL)")

    # Enable Network events so we get websocket events
    send("Network.enable", {})

    print("[INFO] Listening for WebSocket events... (Ctrl+C to exit)")
    try:
        while True:
            raw = cdp.recv()
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            method = msg.get("method")
            params = msg.get("params", {})

            if not method:
                # likely a response to a command; ignore
                continue

            # Track creation and URL mapping
            if method == "Network.webSocketCreated":
                req_id = params.get("requestId")
                url = params.get("url")
                if req_id:
                    ws_url_by_req[req_id] = url or ""
                print(f"[CREATE] {pretty_ts()}  requestId={req_id}  url={url}")

            # Socket closed
            elif method == "Network.webSocketClosed":
                req_id = params.get("requestId")
                url = ws_url_by_req.get(req_id, "")
                print(f"[CLOSE]  {pretty_ts()}  requestId={req_id}  url={url}")

            # Handshake info (optional)
            elif method == "Network.webSocketWillSendHandshakeRequest":
                req_id = params.get("requestId")
                url = ws_url_by_req.get(req_id, params.get("request", {}).get("url", ""))
                print(f"[HS OUT] {pretty_ts()}  requestId={req_id}  url={url}")

            elif method == "Network.webSocketHandshakeResponseReceived":
                req_id = params.get("requestId")
                url = ws_url_by_req.get(req_id, "")
                status = params.get("response", {}).get("status")
                print(f"[HS IN ] {pretty_ts()}  requestId={req_id}  url={url}  status={status}")

            # Incoming frame (server -> browser)
            elif method == "Network.webSocketFrameReceived":
                req_id = params.get("requestId")
                frame = params.get("response", {}) or {}
                opcode = frame.get("opcode")
                payload = frame.get("payloadData")
                url = ws_url_by_req.get(req_id, "")

                if args.only_socket_contains and args.only_socket_contains not in (url or ""):
                    # skip unrelated sockets
                    continue

                event = {
                    "dir": "recv",
                    "t": pretty_ts(params.get("timestamp")),
                    "requestId": req_id,
                    "url": url,
                    "opcode": opcode,
                    "payload": payload,
                }

                # Print nicely
                if opcode == 1:  # text
                    print(f"[RECV] {event['t']}  url={url}  len={len(payload) if payload else 0}")
                    print(shorten(payload))
                elif opcode == 2:  # binary
                    try:
                        # CDP generally stores binary as base64 in payloadData for some events.
                        raw_bytes = base64.b64decode(payload)
                        preview = raw_bytes[:24].hex()
                        print(f"[RECV] {event['t']}  url={url}  BINARY len={len(raw_bytes)}  hex={preview}...")
                    except Exception:
                        # Sometimes payload may already be text or non-base64; just show summary
                        print(f"[RECV] {event['t']}  url={url}  BINARY(len?={len(payload) if payload else 0})")
                else:
                    print(f"[RECV] {event['t']}  url={url}  opcode={opcode}  len={len(payload) if payload else 0}")

                if f_out:
                    f_out.write(json.dumps(event) + "\n")
                    f_out.flush()

            # Outgoing frame (browser -> server)
            elif method == "Network.webSocketFrameSent":
                req_id = params.get("requestId")
                frame = params.get("response", {}) or {}
                opcode = frame.get("opcode")
                payload = frame.get("payloadData")
                url = ws_url_by_req.get(req_id, "")

                if args.only_socket_contains and args.only_socket_contains not in (url or ""):
                    continue

                if not args.show_sent:
                    continue

                event = {
                    "dir": "send",
                    "t": pretty_ts(params.get("timestamp")),
                    "requestId": req_id,
                    "url": url,
                    "opcode": opcode,
                    "payload": payload,
                }

                if opcode == 1:  # text
                    print(f"[SENT] {event['t']}  url={url}  len={len(payload) if payload else 0}")
                    print(shorten(payload))
                elif opcode == 2:  # binary
                    try:
                        raw_bytes = base64.b64decode(payload)
                        preview = raw_bytes[:24].hex()
                        print(f"[SENT] {event['t']}  url={url}  BINARY len={len(raw_bytes)}  hex={preview}...")
                    except Exception:
                        print(f"[SENT] {event['t']}  url={url}  BINARY(len?={len(payload) if payload else 0})")
                else:
                    print(f"[SENT] {event['t']}  url={url}  opcode={opcode}  len={len(payload) if payload else 0}")

                if f_out:
                    f_out.write(json.dumps(event) + "\n")
                    f_out.flush()

            # Error event
            elif method == "Network.webSocketFrameError":
                req_id = params.get("requestId")
                url = ws_url_by_req.get(req_id, "")
                err_msg = params.get("errorMessage", "")
                print(f"[ERROR]  {pretty_ts()}  requestId={req_id}  url={url}  msg={err_msg}")

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user. Exiting...")
    except WebSocketException as e:
        print(f"[ERROR] WebSocket error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if f_out:
            f_out.close()
            print(f"[INFO] Saved events to {args.save}")
        try:
            cdp.close()
        except:
            pass


if __name__ == "__main__":
    main()

