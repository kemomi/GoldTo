"""GoldTo Backend – Flask REST API."""
import os, sys, json, threading
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

# ── path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── env ─────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv          # stdlib-compatible shim below
try:
    load_dotenv(ROOT.parent / ".env")
except Exception:
    pass   # dotenv not installed – use OS env

app = Flask(__name__, static_folder=str(ROOT.parent / "frontend"), static_url_path="")

# ── CORS ────────────────────────────────────────────────────────────────────
@app.after_request
def cors(resp):
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return resp

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path and (ROOT.parent / "frontend" / path).exists():
        return send_from_directory(ROOT.parent / "frontend", path)
    return send_from_directory(ROOT.parent / "frontend", "index.html")

# ── lazy imports (avoid circular) ───────────────────────────────────────────
def _get_sim_module():
    from agents.simulation import create_simulation, get_simulation, latest_simulation
    return create_simulation, get_simulation, latest_simulation

# ════════════════════════════════════════════════════════════════════════════
# API routes
# ════════════════════════════════════════════════════════════════════════════

# ── health ──────────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    from utils.llm_client import llm
    return jsonify({"ok": True, "llm_mode": "real" if not llm._mock else "mock",
                    "model": llm.model})

# ── simulation ──────────────────────────────────────────────────────────────
@app.route("/api/simulate", methods=["POST", "OPTIONS"])
def start_simulation():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    data          = request.get_json(force=True)
    seed_text     = data.get("seed_text", "").strip()
    target        = data.get("prediction_target", "预测黄金价格走势").strip()
    agent_count   = min(int(data.get("agent_count", 20)), 50)
    num_rounds    = min(int(data.get("num_rounds", 10)), 40)

    if not seed_text:
        return jsonify({"error": "seed_text is required"}), 400

    create_simulation, _, _ = _get_sim_module()
    sim = create_simulation()
    sim.start(seed_text, target, agent_count, num_rounds)
    return jsonify({"sim_id": sim.id, "message": "仿真已启动"})

@app.route("/api/simulation/<sim_id>")
def simulation_state(sim_id):
    _, get_simulation, _ = _get_sim_module()
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "not found"}), 404
    return jsonify(sim.get_state())

@app.route("/api/simulation/<sim_id>/agents")
def simulation_agents(sim_id):
    _, get_simulation, _ = _get_sim_module()
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "not found"}), 404
    return jsonify(sim.get_agents())

@app.route("/api/simulation/<sim_id>/graph")
def simulation_graph(sim_id):
    _, get_simulation, _ = _get_sim_module()
    sim = get_simulation(sim_id)
    if not sim or not sim.graph:
        return jsonify({"nodes": [], "edges": []})
    return jsonify(sim.graph.to_dict())

# ── chat ─────────────────────────────────────────────────────────────────────
@app.route("/api/simulation/<sim_id>/agent/<agent_id>/chat", methods=["POST","OPTIONS"])
def agent_chat(sim_id, agent_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200
    _, get_simulation, _ = _get_sim_module()
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "not found"}), 404
    msg  = request.get_json(force=True).get("message", "")
    resp = sim.chat_with_agent(agent_id, msg)
    return jsonify({"response": resp})

@app.route("/api/simulation/<sim_id>/report/chat", methods=["POST","OPTIONS"])
def report_chat(sim_id):
    if request.method == "OPTIONS":
        return jsonify({}), 200
    _, get_simulation, _ = _get_sim_module()
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "not found"}), 404
    msg  = request.get_json(force=True).get("message", "")
    resp = sim.chat_with_report_agent(msg)
    return jsonify({"response": resp})

# ── latest convenience (no sim_id) ──────────────────────────────────────────
@app.route("/api/latest")
def latest():
    _, _, latest_simulation = _get_sim_module()
    sim = latest_simulation()
    if not sim:
        return jsonify({"error": "no simulation"}), 404
    return jsonify(sim.get_state())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"🚀 GoldTo Backend running on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
