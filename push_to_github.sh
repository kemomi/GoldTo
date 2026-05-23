#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════
# GoldTo — 上传到 GitHub dev 分支脚本
# 用法: bash push_to_github.sh [your-github-token]
# ═══════════════════════════════════════════════════════════
set -e

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $*${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $*${NC}"; }
info() { echo -e "${CYAN}➜  $*${NC}"; }
fail() { echo -e "${RED}❌ $*${NC}"; exit 1; }

REPO="kemomi/GoldTo"
BRANCH="dev"
PAGES_BRANCH="gh-pages"

echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  GoldTo GitHub 上传脚本                   ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"

# ── 获取 Token ──────────────────────────────────────────────
TOKEN="${1:-$GITHUB_TOKEN}"
if [ -z "$TOKEN" ]; then
  echo -e "${YELLOW}请输入 GitHub Personal Access Token (需要 repo 权限):${NC}"
  read -rs TOKEN
  echo
fi
[ -z "$TOKEN" ] && fail "未提供 Token，退出"

ROOT="$(cd "$(dirname "$0")" && pwd)"
API="https://api.github.com"

# ── 验证 Token ──────────────────────────────────────────────
info "验证 GitHub Token..."
USER=$(curl -sf -H "Authorization: token $TOKEN" "$API/user" | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])" 2>/dev/null)
[ -z "$USER" ] && fail "Token 无效或无权限"
ok "已登录为 $USER"

# ── 检查 git ────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
  fail "未找到 git，请先安装"
fi

# ── 配置 git ────────────────────────────────────────────────
cd "$ROOT"
git config user.name "$USER" 2>/dev/null || true
git config user.email "$USER@users.noreply.github.com" 2>/dev/null || true

REMOTE_URL="https://${TOKEN}@github.com/${REPO}.git"

# ── 初始化 git（如果还没有）──────────────────────────────────
if [ ! -d ".git" ]; then
  info "初始化 git 仓库..."
  git init
  git remote add origin "$REMOTE_URL"
  ok "git 初始化完成"
else
  # 更新 remote URL（含 token）
  git remote set-url origin "$REMOTE_URL" 2>/dev/null || git remote add origin "$REMOTE_URL"
  ok "远程仓库已配置"
fi

# ── 拉取最新 main ────────────────────────────────────────────
info "拉取远程 main 分支..."
git fetch origin main --depth=1 2>/dev/null || warn "拉取 main 失败（可能是空仓库，继续...）"

# ── 创建 / 切换到 fix 分支 ───────────────────────────────────
info "切换到 dev 分支..."
if git ls-remote --exit-code origin "$BRANCH" &>/dev/null; then
  # 远程已有 fix 分支
  git fetch origin "$BRANCH" --depth=1 2>/dev/null || true
  git checkout -B "$BRANCH" "origin/$BRANCH" 2>/dev/null \
    || git checkout -B "$BRANCH" 2>/dev/null \
    || git checkout "$BRANCH" 2>/dev/null
  ok "已切换到已有的 dev 分支"
else
  # 从 main 创建 fix 分支
  git checkout -B "$BRANCH" "origin/main" 2>/dev/null \
    || git checkout -B "$BRANCH" 2>/dev/null
  ok "已创建新的 fix 分支"
fi

# ── 检查 .gitignore ──────────────────────────────────────────
if [ ! -f ".gitignore" ]; then
  cat > .gitignore << 'IGNORE'
__pycache__/
*.pyc
*.pyo
.env
!.env.example
node_modules/
frontend/dist/
backend/.venv/
backend/uploads/
.DS_Store
*.egg-info/
.pytest_cache/
IGNORE
  ok ".gitignore 已创建"
fi

# ── Stage 所有修复文件 ───────────────────────────────────────
info "暂存修复文件..."
git add dev.sh setup.sh package.json .env.example \
  backend/utils/mock_client.py \
  backend/agents/simulation_engine.py \
  backend/config.py \
  backend/main.py \
  docs/index.html \
  README.md 2>/dev/null || true

# 也 add 其他核心文件（如果有变动）
git add backend/ frontend/ docker-compose.yml 2>/dev/null || true

CHANGED=$(git diff --cached --name-only | wc -l | tr -d ' ')
info "已暂存 $CHANGED 个文件"

if [ "$CHANGED" -eq 0 ]; then
  warn "没有变更需要提交（文件已是最新状态）"
else
  git commit -m "fix: 修复 concurrently 兼容性问题，添加 Mock 离线模式

- 新增 dev.sh：替代 concurrently，兼容 Node 12+（解决 ?? 语法错误）
- 新增 setup.sh：一键安装脚本，自动检测 uv/pip
- 新增 backend/utils/mock_client.py：完整 Mock LLM 客户端
  - 支持知识图谱、人设生成、智能体互动、报告生成等全部接口
  - 无需 API Key 即可完整运行
- backend/agents/simulation_engine.py：_get_llm() 自动选择真实/Mock 客户端
- backend/config.py：添加 is_mock 属性，识别占位符 Key
- backend/main.py：/health 接口显示 LLM 模式
- docs/index.html：GitHub Pages 演示页面
- package.json：移除 concurrently 依赖

Fixes: #concurrently-syntax-error #no-api-key-crash"
  ok "提交成功"
fi

# ── Push fix 分支 ────────────────────────────────────────────
info "推送 dev 分支到 GitHub..."
git push origin "$BRANCH" --force-with-lease 2>&1 | tail -3
ok "dev 分支已推送 → https://github.com/$REPO/tree/$BRANCH"

# ── 处理 GitHub Pages (gh-pages 分支) ───────────────────────
echo ""
info "配置 GitHub Pages 演示页面..."

# 将 docs/index.html 部署到 gh-pages 分支
TMPDIR=$(mktemp -d)
cp "$ROOT/docs/index.html" "$TMPDIR/"

# 切换到 gh-pages（或新建）
git fetch origin "$PAGES_BRANCH" --depth=1 2>/dev/null || true
if git ls-remote --exit-code origin "$PAGES_BRANCH" &>/dev/null; then
  git checkout -B "$PAGES_BRANCH" "origin/$PAGES_BRANCH" 2>/dev/null || git checkout -B "$PAGES_BRANCH"
else
  git checkout --orphan "$PAGES_BRANCH"
  git rm -rf . --quiet 2>/dev/null || true
fi

# 放入演示页面
cp "$TMPDIR/index.html" .
git add index.html
git diff --cached --quiet 2>/dev/null || \
  git commit -m "docs: 更新 GitHub Pages 演示页面"
git push origin "$PAGES_BRANCH" --force 2>&1 | tail -3
rm -rf "$TMPDIR"
ok "GitHub Pages 已部署 → https://${REPO%/*}.github.io/${REPO#*/}/"

# ── 切回 fix 分支 ────────────────────────────────────────────
git checkout "$BRANCH" --quiet 2>/dev/null || true

echo ""
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ 全部完成！${NC}"
echo ""
echo -e "  Fix 分支:  ${CYAN}https://github.com/$REPO/tree/$BRANCH${NC}"
echo -e "  演示页面:  ${CYAN}https://${REPO%/*}.github.io/${REPO#*/}/${NC}"
echo -e "  提交PR:    ${CYAN}https://github.com/$REPO/compare/$BRANCH${NC}"
echo -e "${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}💡 若 GitHub Pages 未立即生效，请前往仓库 Settings → Pages"
echo -e "   将 Source 设置为 gh-pages 分支，等待约 1-2 分钟${NC}"
