"use strict";
// 사다리타기 C/S - Node.js + Express 서버 (세션 상태 서버 관리)
const express = require("express");
const path = require("path");
const crypto = require("crypto");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "..", "public")));

const sessions = new Map(); // sessionId -> state

function newState() {
  return { participants: [], goals: [], pLocked: false, gLocked: false };
}
function publicState(s) {
  return { participants: s.participants, goals: s.goals, pLocked: s.pLocked, gLocked: s.gLocked };
}
function getSession(req, res) {
  const s = sessions.get(req.params.id);
  if (!s) { res.status(404).json({ error: "세션을 찾을 수 없습니다." }); return null; }
  return s;
}

// 사다리 생성: cols 세로선, levels 레벨, 인접 충돌 없는 가로줄 + 결과 계산
function buildLadder(participants, goals) {
  const cols = participants.length;
  const levels = 8 + cols;
  const rungs = [];
  for (let lv = 0; lv < levels; lv++) {
    for (let c = 0; c < cols - 1; c++) {
      if (Math.random() < 0.4) {
        if (rungs.some(r => r.level === lv && (r.col === c - 1 || r.col === c + 1 || r.col === c))) continue;
        rungs.push({ level: lv, col: c });
      }
    }
  }
  rungs.sort((a, b) => a.level - b.level);
  const results = [];
  for (let start = 0; start < cols; start++) {
    let col = start;
    for (const r of rungs) {
      if (r.col === col) col++;
      else if (r.col === col - 1) col--;
    }
    results.push(col);
  }
  return { cols, levels, rungs, results };
}

// ----- API -----
app.post("/api/session", (req, res) => {
  const sessionId = crypto.randomBytes(3).toString("hex");
  sessions.set(sessionId, newState());
  res.json({ sessionId, server: "node", state: publicState(sessions.get(sessionId)) });
});

app.post("/api/session/:id/add", (req, res) => {
  const s = getSession(req, res); if (!s) return;
  const { kind, value } = req.body || {};
  const v = (value || "").trim();
  if (!v) return res.status(400).json({ error: "값이 비어 있습니다." });
  if (kind === "participant") { if (s.pLocked) return res.status(400).json({ error: "참여자는 확정되었습니다." }); s.participants.push(v); }
  else if (kind === "goal") { if (s.gLocked) return res.status(400).json({ error: "Goal은 확정되었습니다." }); s.goals.push(v); }
  else return res.status(400).json({ error: "kind 오류" });
  res.json({ state: publicState(s) });
});

app.post("/api/session/:id/remove", (req, res) => {
  const s = getSession(req, res); if (!s) return;
  const { kind, index } = req.body || {};
  const arr = kind === "participant" ? s.participants : kind === "goal" ? s.goals : null;
  const locked = kind === "participant" ? s.pLocked : s.gLocked;
  if (!arr) return res.status(400).json({ error: "kind 오류" });
  if (locked) return res.status(400).json({ error: "확정 후에는 삭제할 수 없습니다." });
  if (index >= 0 && index < arr.length) arr.splice(index, 1);
  res.json({ state: publicState(s) });
});

app.post("/api/session/:id/lock", (req, res) => {
  const s = getSession(req, res); if (!s) return;
  const { kind } = req.body || {};
  if (kind === "participant") { if (s.participants.length < 2) return res.status(400).json({ error: "참여자는 2명 이상이어야 합니다." }); s.pLocked = true; }
  else if (kind === "goal") { if (s.goals.length < 1) return res.status(400).json({ error: "Goal은 1개 이상이어야 합니다." }); s.gLocked = true; }
  else return res.status(400).json({ error: "kind 오류" });
  res.json({ state: publicState(s) });
});

app.post("/api/session/:id/start", (req, res) => {
  const s = getSession(req, res); if (!s) return;
  if (!s.pLocked || !s.gLocked) return res.status(400).json({ error: "참여자와 Goal을 모두 '완료'하세요." });
  const ladder = buildLadder(s.participants, s.goals);
  s.ladder = ladder;
  res.json({ state: publicState(s), ladder });
});

app.post("/api/session/:id/reset", (req, res) => {
  const s = getSession(req, res); if (!s) return;
  sessions.set(req.params.id, newState());
  res.json({ state: publicState(sessions.get(req.params.id)) });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🪜 사다리타기(Node) → http://localhost:${PORT}`));
