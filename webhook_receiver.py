import os
import json
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
PORT = int(os.environ.get("PORT", 5000))


def load_or_create_secret(env_var, file_name, length=32):
    """
    Load a secret from an environment variable. If not set, fall back to a
    local file (auto-generated on first run) so local dev works without any
    setup. The env var always takes priority (used in production/Render).
    """
    env_val = os.environ.get(env_var)
    if env_val:
        return env_val

    path = os.path.join(BASE_DIR, file_name)
    if os.path.exists(path):
        with open(path, "r") as f:
            val = f.read().strip()
            if val:
                return val

    val = secrets.token_urlsafe(length)
    with open(path, "w") as f:
        f.write(val)
    return val


CLIENT_ID = os.environ.get("CLIENT_ID", "demo-client-id")
CLIENT_SECRET = load_or_create_secret("CLIENT_SECRET", ".client_secret")
JWT_SECRET_KEY = load_or_create_secret("JWT_SECRET_KEY", ".jwt_secret_key")
TOKEN_EXPIRES_IN = int(os.environ.get("TOKEN_EXPIRES_IN", "3600"))


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def verify_basic_auth(req):
    auth = req.authorization
    if auth is None or auth.type != "basic":
        return False
    valid_id = hmac.compare_digest(auth.username or "", CLIENT_ID)
    valid_secret = hmac.compare_digest(auth.password or "", CLIENT_SECRET)
    return valid_id and valid_secret


def generate_bearer_token(client_id):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": client_id,
        "iat": now,
        "exp": now + timedelta(seconds=TOKEN_EXPIRES_IN),
        "scope": "webhook:receive",
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def verify_bearer_token(req):
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[len("Bearer "):]
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def print_received(req, method_label):
    content_type = req.content_type or ""
    try:
        payload = req.get_json(force=True, silent=True)
    except Exception:
        payload = None

    print(flush=True)
    print("=" * 60, flush=True)
    log(f"WEBHOOK RECEIVED [{method_label}]")
    print(f"  Method      : {req.method}", flush=True)
    print(f"  Content-Type: {content_type}", flush=True)
    print(flush=True)
    print("  --- Body (JSON) ---", flush=True)
    if payload is not None:
        print(json.dumps(payload, indent=2, ensure_ascii=False), flush=True)
    else:
        raw = req.get_data(as_text=True)
        print(f"  (raw) {raw[:2000]}", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)
    return payload


@app.route("/oauth/token", methods=["POST"])
def issue_token():
    """
    Issues a Bearer token. The ONLY way to get a token is to POST here with
    valid HTTP Basic credentials (client_id / client_secret).
    """
    if not verify_basic_auth(request):
        log("TOKEN REQUEST REJECTED - invalid client_id/secret")
        resp = jsonify({
            "error": "invalid_client",
            "error_description": "Invalid client_id or client_secret",
        })
        resp.status_code = 401
        resp.headers["WWW-Authenticate"] = 'Basic realm="oauth/token"'
        return resp

    token = generate_bearer_token(CLIENT_ID)
    log(f"TOKEN ISSUED for client_id={CLIENT_ID}")
    return jsonify({
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": TOKEN_EXPIRES_IN,
    }), 200


@app.route("/webhook/basic", methods=["POST"])
def webhook_basic():
    if not verify_basic_auth(request):
        log("UNAUTHORIZED (basic) - invalid or missing credentials")
        resp = jsonify({"error": "Unauthorized"})
        resp.status_code = 401
        resp.headers["WWW-Authenticate"] = 'Basic realm="webhook"'
        return resp

    print_received(request, "BASIC")
    return jsonify({
        "status": "received",
        "auth_method": "basic",
        "message": "Webhook received and authenticated via HTTP Basic Authentication",
        "received_at": datetime.now(timezone.utc).isoformat(),
    }), 200


@app.route("/webhook/bearer", methods=["POST"])
def webhook_bearer():
    token_payload = verify_bearer_token(request)
    if token_payload is None:
        log("UNAUTHORIZED (bearer) - invalid, expired, or missing token")
        resp = jsonify({"error": "Unauthorized"})
        resp.status_code = 401
        resp.headers["WWW-Authenticate"] = 'Bearer realm="webhook"'
        return resp

    print_received(request, "BEARER")
    return jsonify({
        "status": "received",
        "auth_method": "bearer",
        "message": "Webhook received and authenticated via Bearer token",
        "token_subject": token_payload.get("sub"),
        "received_at": datetime.now(timezone.utc).isoformat(),
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    client_secret_source = "env var" if os.environ.get("CLIENT_SECRET") else ".client_secret (auto-generated)"
    jwt_secret_source = "env var" if os.environ.get("JWT_SECRET_KEY") else ".jwt_secret_key (auto-generated)"
    public_url = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{PORT}")

    print(flush=True)
    print("=" * 60, flush=True)
    print("  Webhook Dinamico - Basic + Bearer Auth Receiver", flush=True)
    print(f"  Port              : {PORT}", flush=True)
    print(f"  Token endpoint    : {public_url}/oauth/token", flush=True)
    print(f"  Basic webhook     : {public_url}/webhook/basic", flush=True)
    print(f"  Bearer webhook    : {public_url}/webhook/bearer", flush=True)
    print(f"  Client ID         : {CLIENT_ID}", flush=True)
    print(f"  Client secret     : {CLIENT_SECRET}", flush=True)
    print(f"  Client secret src : {client_secret_source}", flush=True)
    print(f"  JWT secret src    : {jwt_secret_source}", flush=True)
    print(f"  Token expires in  : {TOKEN_EXPIRES_IN}s", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
