#!/usr/bin/env bash
# GoldTo 一键安装脚本
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")" && pwd)"
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }

echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}   GoldTo 安装脚本                     ${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"

# ── 检查 Python ──────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    fail "未找到 python3，请先安装 Python 3.11+"
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ok "Python $PY_VER"

# ── 检查 Node ────────────────────────────────────────────
if ! command -v node &>/dev/null; then
    fail "未找到 node，请先安装 Node.js 14+"
fi
NODE_VER=$(node -v)
ok "Node.js $NODE_VER"

# ── 前端依赖 ─────────────────────────────────────────────
echo -e "\n${YELLOW}[1/3] 安装前端依赖...${NC}"
cd "$ROOT/frontend"
npm install --legacy-peer-deps
ok "前端依赖安装完成"

# ── 后端依赖 ─────────────────────────────────────────────
echo -e "\n${YELLOW}[2/3] 安装后端依赖...${NC}"
cd "$ROOT/backend"

if command -v uv &>/dev/null; then
    ok "使用 uv 安装"
    uv sync
else
    warn "未找到 uv，使用 pip 安装（推荐安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh）"
    pip3 install \
        fastapi uvicorn[standard] openai python-multipart python-dotenv \
        pydantic pydantic-settings sse-starlette networkx pypdf httpx aiofiles \
        --break-system-packages -q 2>/dev/null \
    || pip3 install \
        fastapi uvicorn openai python-multipart python-dotenv \
        pydantic pydantic-settings sse-starlette networkx pypdf httpx aiofiles \
        -q
fi
ok "后端依赖安装完成"

# ── 环境变量 ─────────────────────────────────────────────
echo -e "\n${YELLOW}[3/3] 配置环境变量...${NC}"
cd "$ROOT"
if [ ! -f ".env" ]; then
    cp .env.example .env
    ok ".env 已创建（Mock 模式，无需 API Key）"
else
    ok ".env 已存在，跳过"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo ""
echo -e "  启动项目:  ${GREEN}bash dev.sh${NC}"
echo -e "  配置 Key:  ${YELLOW}编辑 .env 填入 LLM_API_KEY（可选，不填用 Mock 模式）${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
