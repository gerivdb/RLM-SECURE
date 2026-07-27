from flask import Flask, jsonify, request
import os
import requests
from datetime import datetime, timezone

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 8797))
KIX_BASE_URL = os.environ.get("KIX_BASE_URL", "http://localhost:8800")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "rlm-secure", "port": PORT}), 200


@app.get("/metrics")
def metrics():
    return jsonify({
        "service": "rlm-secure",
        "port": PORT,
        "checks": 0,
        "passed": 0,
        "failed": 0,
        "timestamp": _utcnow(),
    }), 200


@app.post("/vote")
def vote():
    data = request.get_json(silent=True) or {}
    choice = data.get("choice")
    if not choice:
        return jsonify({"error": "missing choice"}), 400
    return jsonify({"choice": choice, "count": 1}), 200


@app.post("/validate")
def validate():
    data = request.get_json(silent=True) or {}
    target = data.get("target")
    if not target:
        return jsonify({"error": "missing target"}), 400

    findings = []
    if "http://" in target:
        findings.append({"level": "warn", "message": "plaintext http detected"})
    if "@" in target:
        findings.append({"level": "warn", "message": "possible credential in url"})

    status = "pass" if not findings else "flagged"
    return jsonify({
        "id": f"validate-{abs(hash(target + _utcnow()))}",
        "target": target,
        "status": status,
        "findings": findings,
        "timestamp": _utcnow(),
    }), 200


@app.get("/status")
def status():
    return jsonify({"service": "rlm-secure", "port": PORT, "mode": "standby"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
