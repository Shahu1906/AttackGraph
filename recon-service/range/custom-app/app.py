"""
AttackGraphX Lab — Custom Flask Application
============================================
This is an INTENTIONALLY WEAK application created SOLELY for the
AttackGraphX controlled cybersecurity laboratory.

DO NOT deploy this in any real environment.
This application exists only to provide an HTTP service target for
authorized Nmap scanning within the isolated attackgraphx-net Docker network.
"""

from flask import Flask, request, jsonify

app = Flask(__name__)

# ─── Lab-only fake credentials (not real, not used for anything) ───────────
LAB_USER = "labuser"
LAB_PASS = "labpass123"


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "app": "AttackGraphX Custom Lab App",
        "version": "1.0.0",
        "description": "Controlled lab target for authorized scanning only.",
        "endpoints": ["/", "/login", "/status"],
    })


@app.route("/login", methods=["POST"])
def login():
    """
    Intentionally weak login endpoint — accepts credentials in plain JSON.
    Exists only so that Nmap service detection can identify this as an HTTP
    service with a Flask/Werkzeug banner.
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if username == LAB_USER and password == LAB_PASS:
        return jsonify({"status": "ok", "message": "Lab login accepted"}), 200
    return jsonify({"status": "fail", "message": "Invalid credentials"}), 401


@app.route("/status", methods=["GET"])
def status():
    return jsonify({
        "status": "running",
        "service": "custom-flask-app",
        "network": "attackgraphx-net",
    })


if __name__ == "__main__":
    # Bind to all interfaces inside the container
    app.run(host="0.0.0.0", port=5000, debug=False)
