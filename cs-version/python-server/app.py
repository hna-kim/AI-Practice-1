# -*- coding: utf-8 -*-
"""사다리타기 C/S - Python + Flask 서버 (세션 상태 서버 관리)"""
import os
import secrets
import random
from flask import Flask, request, jsonify, send_from_directory

PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "..", "public")
app = Flask(__name__, static_folder=None)

sessions = {}  # sessionId -> state dict


def new_state():
    return {"participants": [], "goals": [], "pLocked": False, "gLocked": False}


def public_state(s):
    return {"participants": s["participants"], "goals": s["goals"],
            "pLocked": s["pLocked"], "gLocked": s["gLocked"]}


def get_session(sid):
    return sessions.get(sid)


def build_ladder(participants, goals):
    cols = len(participants)
    levels = 8 + cols
    rungs = []
    for lv in range(levels):
        for c in range(cols - 1):
            if random.random() < 0.4:
                if any(r["level"] == lv and r["col"] in (c - 1, c, c + 1) for r in rungs):
                    continue
                rungs.append({"level": lv, "col": c})
    rungs.sort(key=lambda r: r["level"])
    results = []
    for start in range(cols):
        col = start
        for r in rungs:
            if r["col"] == col:
                col += 1
            elif r["col"] == col - 1:
                col -= 1
        results.append(col)
    return {"cols": cols, "levels": levels, "rungs": rungs, "results": results}


# ----- 정적 파일 -----
@app.route("/")
def index():
    return send_from_directory(PUBLIC_DIR, "index.html")


@app.route("/<path:fname>")
def static_files(fname):
    return send_from_directory(PUBLIC_DIR, fname)


# ----- API -----
@app.route("/api/session", methods=["POST"])
def create_session():
    sid = secrets.token_hex(3)
    sessions[sid] = new_state()
    return jsonify(sessionId=sid, server="python", state=public_state(sessions[sid]))


@app.route("/api/session/<sid>/add", methods=["POST"])
def add(sid):
    s = get_session(sid)
    if s is None:
        return jsonify(error="세션을 찾을 수 없습니다."), 404
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    value = (body.get("value") or "").strip()
    if not value:
        return jsonify(error="값이 비어 있습니다."), 400
    if kind == "participant":
        if s["pLocked"]:
            return jsonify(error="참여자는 확정되었습니다."), 400
        s["participants"].append(value)
    elif kind == "goal":
        if s["gLocked"]:
            return jsonify(error="Goal은 확정되었습니다."), 400
        s["goals"].append(value)
    else:
        return jsonify(error="kind 오류"), 400
    return jsonify(state=public_state(s))


@app.route("/api/session/<sid>/remove", methods=["POST"])
def remove(sid):
    s = get_session(sid)
    if s is None:
        return jsonify(error="세션을 찾을 수 없습니다."), 404
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    index = body.get("index")
    if kind == "participant":
        arr, locked = s["participants"], s["pLocked"]
    elif kind == "goal":
        arr, locked = s["goals"], s["gLocked"]
    else:
        return jsonify(error="kind 오류"), 400
    if locked:
        return jsonify(error="확정 후에는 삭제할 수 없습니다."), 400
    if isinstance(index, int) and 0 <= index < len(arr):
        arr.pop(index)
    return jsonify(state=public_state(s))


@app.route("/api/session/<sid>/lock", methods=["POST"])
def lock(sid):
    s = get_session(sid)
    if s is None:
        return jsonify(error="세션을 찾을 수 없습니다."), 404
    body = request.get_json(silent=True) or {}
    kind = body.get("kind")
    if kind == "participant":
        if len(s["participants"]) < 2:
            return jsonify(error="참여자는 2명 이상이어야 합니다."), 400
        s["pLocked"] = True
    elif kind == "goal":
        if len(s["goals"]) < 1:
            return jsonify(error="Goal은 1개 이상이어야 합니다."), 400
        s["gLocked"] = True
    else:
        return jsonify(error="kind 오류"), 400
    return jsonify(state=public_state(s))


@app.route("/api/session/<sid>/start", methods=["POST"])
def start(sid):
    s = get_session(sid)
    if s is None:
        return jsonify(error="세션을 찾을 수 없습니다."), 404
    if not s["pLocked"] or not s["gLocked"]:
        return jsonify(error="참여자와 Goal을 모두 '완료'하세요."), 400
    ladder = build_ladder(s["participants"], s["goals"])
    s["ladder"] = ladder
    return jsonify(state=public_state(s), ladder=ladder)


@app.route("/api/session/<sid>/reset", methods=["POST"])
def reset(sid):
    if sid not in sessions:
        return jsonify(error="세션을 찾을 수 없습니다."), 404
    sessions[sid] = new_state()
    return jsonify(state=public_state(sessions[sid]))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🪜 사다리타기(Python) → http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
