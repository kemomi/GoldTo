#!/usr/bin/env bash
# GoldTo 启动脚本 — 替代 concurrently，兼容任意 Node/Bash 版本
set -e

BLUE='\033[0;36m'
MAGENTA='\033[0;35m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   GoldTo · 群体智能预测引擎  启动中   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"

# ── 清理函数 ────────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo -e "\n${RED}[GoldTo] 正在关闭服务...${NC}"
    [ -n "$BACKEND_PID" ]  && kill "$BACKEND_PID"  2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null
    wait 2>/dev/null
    echo -e "${GREEN}[GoldTo] 已安全退出${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ── 启动后端 ─────────────────────────────────────────────
echo -e "${BLUE}[BACKEND] 启动 FastAPI 后端 → http://localhost:5001${NC}"
cd "$ROOT/backend"

if command -v uv &>/dev/null; then
    uv run uvicorn main:app --host 0.0.0.0 --port 5001 --reload 2>&1 \
        | sed "s/^/${BLUE}[BACKEND]${NC} /" &
else
    # uv 不存在时回退到系统 python
    python3 -m uvicorn main:app --host 0.0.0.0 --port 5001 --reload 2>&1 \
        | sed "s/^/${BLUE}[BACKEND]${NC} /" &
fi
BACKEND_PID=$!

# 等后端就绪
sleep 2

# ── 启动前端 ─────────────────────────────────────────────
echo -e "${MAGENTA}[FRONTEND] 启动 Vite 前端 → http://localhost:3000${NC}"
cd "$ROOT/frontend"
npm run dev 2>&1 | sed "s/^/${MAGENTA}[FRONTEND]${NC} /" &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}[GoldTo] 服务已启动${NC}"
echo -e "  前端: ${GREEN}http://localhost:3000${NC}"
echo -e "  后端: ${GREEN}http://localhost:5001${NC}  (API 文档: /docs)"
echo -e "  按 ${RED}Ctrl+C${NC} 停止所有服务"
echo ""

# 等待子进程
wait
