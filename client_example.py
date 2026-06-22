"""
Example client that exercises the full authentication flow against
webhook_receiver.py:

  1. Requests a Bearer token from /oauth/token using Basic auth
     (client_id + client_secret).
  2. Sends a sample webhook to /webhook/bearer using that token.
  3. Sends a sample webhook to /webhook/basic using Basic auth directly.
  4. Sends a request with wrong credentials to show the 401 responses.

Usage:
  python client_example.py \
      --base-url http://localhost:5000 \
      --client-id demo-client-id \
      --client-secret demo-client-secret
"""

import argparse
import json
import sys

import requests


def parse_args():
    parser = argparse.ArgumentParser(description="Test client for Webhook Dinamico")
    parser.add_argument("--base-url", default="http://localhost:5000")
    parser.add_argument("--client-id", default="demo-client-id")
    parser.add_argument("--client-secret", default="demo-client-secret")
    return parser.parse_args()


def print_response(label, resp):
    print(f"\n--- {label} ---")
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except ValueError:
        print(resp.text)


def main():
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    # 1. Request a Bearer token using Basic auth
    token_resp = requests.post(
        f"{base_url}/oauth/token",
        auth=(args.client_id, args.client_secret),
    )
    print_response("POST /oauth/token (valid credentials)", token_resp)

    if token_resp.status_code != 200:
        print("\nCould not obtain a token. Check --client-id / --client-secret.")
        sys.exit(1)

    access_token = token_resp.json()["access_token"]

    # 2. Send a webhook authenticated with the Bearer token
    bearer_resp = requests.post(
        f"{base_url}/webhook/bearer",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"event": "order.created", "order_id": 123, "source": "client_example.py"},
    )
    print_response("POST /webhook/bearer (valid token)", bearer_resp)

    # 3. Send a webhook authenticated with Basic auth
    basic_resp = requests.post(
        f"{base_url}/webhook/basic",
        auth=(args.client_id, args.client_secret),
        json={"event": "order.updated", "order_id": 123, "source": "client_example.py"},
    )
    print_response("POST /webhook/basic (valid credentials)", basic_resp)

    # 4. Negative test: wrong client secret
    bad_token_resp = requests.post(
        f"{base_url}/oauth/token",
        auth=(args.client_id, "wrong-secret"),
    )
    print_response("POST /oauth/token (invalid credentials)", bad_token_resp)

    # 5. Negative test: missing/garbage Bearer token
    bad_bearer_resp = requests.post(
        f"{base_url}/webhook/bearer",
        headers={"Authorization": "Bearer not-a-real-token"},
        json={"event": "should.fail"},
    )
    print_response("POST /webhook/bearer (invalid token)", bad_bearer_resp)

    print()


if __name__ == "__main__":
    main()
