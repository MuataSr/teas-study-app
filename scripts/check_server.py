#!/usr/bin/env python3
import urllib.request, json, sys

port = sys.argv[1] if len(sys.argv) > 1 else "8082"
try:
    req = urllib.request.Request(f"http://0.0.0.0:{port}/v1/models")
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
        print(f"OK: {data['data'][0]['id']}")
except Exception as e:
    print(f"ERROR: {e}")
