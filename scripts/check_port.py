#!/usr/bin/env python3
"""Quick check if llama-server is running on port 8082."""
import urllib.request, json, sys

for port in [8082, 8081]:
    try:
        req = urllib.request.Request(f'http://localhost:{port}/v1/models')
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        print(f"Port {port}: {data['data'][0]['id']}")
    except Exception as e:
        print(f"Port {port}: {e}")
