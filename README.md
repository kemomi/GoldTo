<div align="center">

# GoldTo

**简洁通用的群体智能引擎，预测黄金、石油等价格走势**

*A Simple and Universal Swarm Intelligence Engine — Predicting Anything*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![Node](https://img.shields.io/badge/Node.js-18%2B-green?logo=node.js)](https://nodejs.org)
[![License](https://img.shields.io/badge/License-MIT-orange)](LICENSE)
[![Mock Mode](https://img.shields.io/badge/Mock%20Mode-支持无Key体验-yellow)](#mock-模式)

[在线 Demo](https://kemomi.github.io/GoldTo/) · [快速开始](#-快速开始) · [工作原理](#-工作原理) · [API 文档](#-api-文档)

</div>

---

## ⚡ 项目概述

**GoldTo** 是一款基于多智能体技术的新一代 AI 预测引擎。

你只需输入**种子材料**（突发新闻、政策草案、金融信号、财报数据，甚至一段小说故事），系统将自动：

1. **构建知识图谱** — 从种子文本中提取实体与关系，形成 GraphRAG 知识网络
2. **生成智能体群组** — 创建具备独立人格、长期记忆与行为逻辑的角色（机构投资者、央行官员、散户、分析师…）
3. **运行平行仿真** — 在数字沙盘中让智能体自由博弈、相互影响、产生涌现
4. **输出预测报告** — 由 ReportAgent 综合所有仿真数据，生成带置信区间的预测结论
5. **支持深度对话** — 与任意智能体或 ReportAgent 展开对话，深入追问

> **让未来在数字沙盘中预演，助决策在百战模拟后胜出。**

---

## 🖼️ 系统截图

> 界面采用 Retro-Futuristic 指挥台风格，深空黑 + 黄金信号 + 青色轨迹配色。

| 区域 | 内容 |
|------|------|
| **左侧面板** | 仿真配置、情绪实况仪表盘、进度条 |
| **中央主区** | 实时推演流 / 知识图谱 / 预测报告 / 深度对话（Tab 切换） |
| **右侧面板** | 智能体群组列表，点击任意角色进入对话 |

---

## 🔄 工作原理

```
种子材料（新闻/报告/故事）
        │
        ▼
┌─────────────────────┐
│  1. 图谱构建         │  GraphRAG 抽取实体关系，注入个体记忆
│     KnowledgeGraph  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  2. 智能体生成       │  8 种原型角色，按影响力权重分配
│     AgentFactory    │  每个智能体有独立人格、短期+长期记忆
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  3. 多轮仿真         │  每轮：世界事件注入 → 智能体感知反应
│     SimulationLoop  │  → 情绪传染（社会涌现）→ 状态更新
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  4. 报告生成         │  ReportAgent 全知视角分析涌现行为
│     ReportAgent     │  输出带概率区间的预测结论
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  5. 深度互动         │  与任意智能体 / ReportAgent 对话
│     ChatInterface   │  「上帝视角」动态注入变量
└─────────────────────┘
```

### 8 种智能体原型

| 原型 | 影响力 | 核心特征 |
|------|--------|----------|
| 央行官员 | 95% | 稳定优先、货币工具、信号博弈 |
| 政策制定者 | 90% | 保守、系统性思维、信息滞后 |
| 机构投资者 | 85% | 理性、数据驱动、长线思维 |
| 对冲基金经理 | 80% | 逆向思维、高杠杆、短期博弈 |
| 地缘政治分析师 | 65% | 风险感知、历史类比 |
| 媒体分析师 | 60% | 叙事驱动、放大效应 |
| 大宗商品交易员 | 55% | 技术分析、供需敏感 |
| 散户交易者 | 30% | 情绪化、跟风、贪婪/恐惧 |

---

## 🚀 快速开始

### 前置要求

| 工具 | 版本 | 检查命令 |
|------|------|----------|
| Node.js | ≥ 18 | `node -v` |
| Python | 3.11 ~ 3.12 | `python3 --version` |
| uv | 最新版 | `uv --version` |

> **安装 uv**：`curl -LsSf https://astral.sh/uv/install.sh | sh`

---

### 方式一：源码部署（推荐）

**第 1 步：克隆项目**

```bash
git clone https://github.com/kemomi/GoldTo.git
cd GoldTo
```

**第 2 步：配置环境变量**

```bash
cp .env.example .env
```

编辑 `.env`，填入你的 API Keys（不填则自动进入 [Mock 模式](#mock-模式)）：

```env
# LLM API（支持任意 OpenAI 兼容接口）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus

# Zep Cloud 长期记忆（可选）
ZEP_API_KEY=
```

**第 3 步：安装依赖**

```bash
npm run setup:all
```

这条命令会自动安装：前端 npm 依赖 + 后端 Python 依赖（通过 uv 创建虚拟环境）。

**第 4 步：启动**

```bash
npm run dev
```

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:3000 |
| 后端 API | http://localhost:5001 |

也可单独启动：

```bash
npm run backend    # 仅后端
npm run frontend   # 仅前端
```

---

### 方式二：Docker 部署

```bash
# 1. 配置环境变量
cp .env.example .env   # 编辑填入 Keys

# 2. 一键启动
docker compose up -d
```

- 前端映射端口：`3000`
- 后端映射端口：`5001`

---

### Mock 模式

<<<<<<< HEAD
```bash
cd ~/GoldTo

# 解压覆盖修复文件
tar -xzf GoldTo-fix.tar.gz

# 安装前端依赖（只需做一次）
cd frontend && npm install --legacy-peer-deps && cd ..

# 启动（无需任何 API Key）
bash dev.sh
```

=======
>>>>>>> kemomi/main
**不填写 API Key 也可以完整体验所有功能。**

当 `LLM_API_KEY` 为空或为占位符时，系统自动切换到 Mock 模式：
- 知识图谱返回预置的财经实体网络
- 智能体根据角色类型返回差异化的模拟反应
- ReportAgent 生成含情景概率表的完整报告
- 所有对话接口正常响应

健康检查接口会标注当前模式：

```json
{ "ok": true, "llm_mode": "mock", "model": "qwen-plus" }
```

---

## 🔑 API Keys 获取

### LLM（必须二选一）

**选项 A：阿里百炼（推荐，国内稳定）**
- 注册：https://bailian.console.aliyun.com/
- 推荐模型：`qwen-plus`（成本低、效果好）
- BASE_URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- 注意：单次完整仿真（50 智能体 × 40 轮）约消耗 5-10 元额度，建议先用 20 智能体 × 10 轮试跑

**选项 B：其他兼容接口**

| 平台 | BASE_URL |
|------|----------|
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| Moonshot | `https://api.moonshot.cn/v1` |
| Groq | `https://api.groq.com/openai/v1` |

### Zep Cloud（可选）

用于智能体的持久化长期记忆，未配置时退化为进程内内存存储。

- 注册：https://app.getzep.com/
- 免费额度足够日常使用

---

## 📁 项目结构

```
GoldTo/
├── package.json               # 根 npm 脚本（dev / setup / build）
├── .env.example               # 环境变量模板
├── docker-compose.yml         # Docker 编排配置
│
├── frontend/                  # 前端（纯 HTML + Vanilla JS）
│   └── index.html             # 单文件 SPA，Retro-Futuristic 风格
│       ├── 仿真配置面板
│       ├── 实时推演流（Round Feed + 涌现检测）
│       ├── SVG 知识图谱可视化
│       ├── Markdown 报告渲染
│       └── 多目标对话界面
│
└── backend/                   # 后端（Flask REST API）
    ├── app.py                 # 主入口，11 个 API 路由
    ├── agents/
    │   ├── agent.py           # 智能体核心：人格、记忆、感知-反应循环
    │   └── simulation.py      # 仿真引擎：5 阶段流水线 + 涌现检测
    ├── graph/
    │   └── knowledge_graph.py # GraphRAG：实体抽取 + NetworkX 图构建
    ├── memory/
    │   └── zep_memory.py      # 记忆管理：Zep Cloud / 内存双模式
    └── utils/
        └── llm_client.py      # LLM 客户端：真实调用 + Mock 模式
```

---

## 📡 API 文档

### `GET /api/health`

检查服务状态与 LLM 模式。

```json
{ "ok": true, "llm_mode": "real", "model": "qwen-plus" }
```

---

### `POST /api/simulate`

启动一次仿真。返回 `sim_id` 用于后续轮询。

**请求体：**

```json
{
  "seed_text": "美联储3月FOMC维持利率不变，黄金现货突破2380美元...",
  "prediction_target": "预测未来6周国际黄金价格走势",
  "agent_count": 20,
  "num_rounds": 10
}
```

| 字段 | 类型 | 默认 | 限制 |
|------|------|------|------|
| `seed_text` | string | 必填 | — |
| `prediction_target` | string | `"预测黄金价格走势"` | — |
| `agent_count` | int | 20 | 最大 50 |
| `num_rounds` | int | 10 | 最大 40 |

**响应：**

```json
{ "sim_id": "cf252b12", "message": "仿真已启动" }
```

---

### `GET /api/simulation/{sim_id}`

获取仿真状态（轮询直到 `status == "done"`）。

```json
{
  "id": "cf252b12",
  "status": "simulating",
  "progress": 68,
  "current_round": 6,
  "total_rounds": 10,
  "agent_count": 20,
  "rounds": [...],
  "sentiment_trend": [
    { "round": 5, "breakdown": {"看涨": 55, "中性": 25, "看跌": 20}, "dominant": "看涨" }
  ],
  "report": "## GoldTo 预测报告\n..."
}
```

**status 枚举：**`idle` → `building` → `simulating` → `done` / `error`

---

### `GET /api/simulation/{sim_id}/agents`

获取所有智能体当前状态。

```json
[
  {
    "id": "agent_000",
    "name": "杨娜",
    "label": "机构投资者",
    "sentiment": "看涨",
    "confidence": 0.78,
    "influence": 0.85,
    "latest_message": "央行购金信号明确，机构已低调建仓..."
  }
]
```

---

### `GET /api/simulation/{sim_id}/graph`

获取知识图谱节点与边，用于前端 SVG 可视化。

```json
{
  "nodes": [
    { "id": "e1", "label": "美联储", "type": "org", "description": "..." }
  ],
  "edges": [
    { "source": "e1", "target": "e2", "label": "负相关", "weight": 0.85 }
  ]
}
```

节点类型：`person` · `org` · `concept` · `event` · `price`

---

### `POST /api/simulation/{sim_id}/report/chat`

与 ReportAgent 对话（全知视角，可追问任何预测细节）。

```json
// 请求
{ "message": "这次模拟中最关键的涌现行为是什么？" }

// 响应
{ "response": "本次模拟最显著的涌现现象发生在第4轮..." }
```

---

### `POST /api/simulation/{sim_id}/agent/{agent_id}/chat`

与指定智能体对话（以其角色身份回答）。

```json
// 请求
{ "message": "你对当前黄金市场怎么看？" }

// 响应
{ "response": "作为机构投资者，我认为当前央行购金信号明确..." }
```

---

## ⚙️ 仿真参数调优

| 场景 | agent_count | num_rounds | 预计耗时（真实 LLM） |
|------|-------------|------------|----------------------|
| 快速试跑 | 10 | 5 | ~1 分钟 |
| 标准预测 | 20 | 15 | ~5 分钟 |
| 深度分析 | 40 | 30 | ~15 分钟 |
| 全量仿真 | 50 | 40 | ~30 分钟 |

> Mock 模式下所有配置均秒级完成。

---

## 🧩 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | 原生 HTML5 + CSS3 + Vanilla JS（零构建依赖） |
| 后端 | Python 3.11 · Flask · NetworkX · threading |
| LLM 接入 | 任意 OpenAI 兼容接口（requests 直调） |
| 知识图谱 | GraphRAG + NetworkX 有向图 |
| 智能体记忆 | 短期（滑动窗口）+ 长期（Zep Cloud / 内存） |
| 容器化 | Docker Compose（前端 nginx + 后端 Python）|
| 包管理 | uv（Python）· npm（Node）· concurrently |

---

## 🗺️ 路线图

- [x] 核心多智能体仿真引擎
- [x] GraphRAG 知识图谱构建
- [x] ReportAgent 预测报告生成
- [x] 智能体 / ReportAgent 深度对话
- [x] Mock 模式（无 Key 完整体验）
- [x] Docker 一键部署
- [ ] 文件上传（PDF / Word 种子材料）
- [ ] 实时 SSE 推流（无需前端轮询）
- [ ] 多仿真对比视图
- [ ] 智能体网络图（力导向布局）
- [ ] 预测结果历史存档

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'feat: add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 发起 Pull Request

---

## 📄 License

MIT License © 2025 GoldTo Contributors

---

<div align="center">

**如果这个项目对你有帮助，欢迎 Star ⭐**

</div>
# GoldTo
<<<<<<< HEAD
# GoldTo
# GoldTo
=======
>>>>>>> kemomi/main
