# CTF Strategy Radar

**周大福海外市场战略情报 Agent**

面向珠宝集团海外业务团队的每日市场战略雷达。系统基于上传的企业调研材料和公开信息线索，自动构建海外市场知识图谱，生成多位企业专家 Agent，围绕机会、风险、竞品、产品、渠道、合规和供应链进行会商，最终输出可追问、可复现、可用于管理层快速判断的战略简报。

> 当前版本是赛题 MVP：第一阶段不接入企业内部系统，只基于上传材料、公开信息结构和 Mock/LLM 推理演示完整工作流。

---

## 项目故事

周大福正在从以大中华区为核心的珠宝零售集团，走向全球化珠宝品牌。它的海外市场虽然门店数量还不大，但战略重要性正在上升：东南亚是现有阵地，日韩和北美需要持续验证品牌认知，中东和澳洲是潜在新增长市场。

企业真实决策中，管理层每天并不只需要“预测一个价格”，而是需要快速知道：

- 哪些海外市场发生了值得关注的变化
- 这些变化对周大福是机会、风险还是待观察事项
- 哪些部门需要行动：管理层、海外运营、产品、品牌、公关、供应链、合规法务
- 结论来自哪里，可信度如何
- 是否需要升级为管理层预警

因此，本项目将原本的通用多智能体预测引擎改造成 **周大福海外市场战略情报 Agent**。它更像一个“每天早上给企业管理层交付简报的智能分析层”，而不是单纯聊天机器人。

---

## 核心能力

### 1. 上传企业资料

支持上传 `.txt`、`.md`、`.pdf` 作为种子材料，例如：

- 周大福海外市场调研报告
- 竞品调研材料
- 行业报告摘要
- 市场进入分析
- 政策和合规资料

### 2. 构建海外市场知识图谱

系统会从材料中抽取：

- 市场：东南亚、日韩、北美、中东、澳洲
- 品牌与竞品：周大福、Cartier、Tiffany、Bvlgari、周生生、六福等
- 产品：传承系列、Hearts On Fire、MONOLOGUE、SOINLOVE、D-ONE 定制
- 风险：金价、汇率、贵金属认证、AML、数据隐私、供应链、ESG、舆情
- 渠道：机场店、高端购物中心、电商平台、旅游零售

### 3. 生成企业专家 Agent

MVP 默认围绕以下职能视角生成 Agent：

| Agent | 关注点 |
|---|---|
| 东南亚区域市场 Agent | 新加坡、马来西亚、泰国、旅游零售、华人消费 |
| 日韩市场 Agent | 日本、韩国、年轻客群、设计审美、K 金和钻石 |
| 北美市场 Agent | 美国、加拿大、华人市场、高端商圈 |
| 中东与澳洲新市场 Agent | 迪拜、多哈、澳大利亚、市场进入优先级 |
| 金价与汇率风险 Agent | 国际金价、汇率、本地定价、毛利影响 |
| 竞品情报 Agent | Cartier、Tiffany、Bvlgari、周生生、六福、本土品牌 |
| 产品与文化趋势 Agent | 古法黄金、婚嫁珠宝、D-ONE、Hearts On Fire、文化本地化 |
| 渠道与电商平台 Agent | 机场店、购物中心、Shopee、Lazada、Rakuten、Qoo10 |
| 合规与监管 Agent | 贵金属认证、AML/KYC、广告法、数据隐私、消费者保护 |
| 供应链风险 Agent | 钻石来源、T MARK、物流、供应商、ESG |
| 品牌声誉与舆情 Agent | 社媒舆情、产品评价、服务投诉、代言人风险 |
| 战略简报总控 Agent | 汇总判断、生成管理层简报和部门行动清单 |

### 4. 多 Agent 情报会商

系统会让不同专家 Agent 进行多轮会商。每轮会商关注：

- 市场变化
- 机会/风险/待观察分类
- 业务影响
- 建议负责部门
- 是否需要补充来源验证
- 是否需要升级为管理层预警

### 5. 输出每日战略简报

最终报告结构固定为：

```md
# 周大福海外市场每日战略简报

## 今日总览
## 高优先级预警
## 各区域市场变化
## 竞品动态
## 产品与消费者趋势
## 渠道与电商机会
## 合规与供应链风险
## 建议行动清单
## 信息来源与可信度
```

### 6. 追问验证

简报生成后，可以继续追问：

- 为什么中东市场优先级升高？
- 哪些竞品动作最值得关注？
- 金价上涨对产品组合有什么影响？
- 今天哪些部门需要行动？
- 这个结论的可信度如何？
- 东南亚市场应该先开店还是先做电商试水？

---

## 系统工作流

```text
上传调研材料 / 公开资料
        |
        v
构建海外市场知识图谱
        |
        v
生成企业专家 Agent
        |
        v
多轮战略情报会商
        |
        v
战略简报总控 Agent 汇总
        |
        v
输出每日海外市场战略简报
        |
        v
用户追问、验证、下载报告
```

---

## 快速复现

### 环境要求

| 工具 | 推荐版本 |
|---|---|
| Python | 3.11 - 3.12 |
| Node.js | 18+ |
| uv | 最新版 |
| npm | 随 Node.js 安装 |

### 1. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

如果没有 API Key，可以不填，系统会自动进入 Mock 模式，仍可完整体验流程。

如果使用阿里百炼 / 通义千问：

```env
LLM_API_KEY=你的_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus
```

可选长期记忆：

```env
ZEP_API_KEY=
```

### 2. 安装依赖

```bash
npm run setup:all
```

该命令会安装：

- 前端 React/Vite 依赖
- 后端 FastAPI/Python 依赖

如果你的环境不能执行 Bash 脚本，也可以分开安装：

```bash
cd frontend
npm install
```

```bash
cd backend
uv sync
```

### 3. 启动项目

一键启动：

```bash
npm run dev
```

或分开启动：

```bash
npm run backend
```

```bash
npm run frontend
```

默认地址：

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost:3001 |
| 后端 | http://localhost:5001 |
| API 文档 | http://localhost:5001/docs |

---

## 页面复现流程

如果需要接入 WorldMonitor，请先单独启动：

```bash
cd C:\Users\TYF07\worldmonitor
npm run dev
```

WorldMonitor 默认运行在：

```text
http://localhost:3000
```

本项目前端为了避开 WorldMonitor，默认运行在：

```text
http://localhost:3001
```

### Step 1：进入首页

打开：

```text
http://localhost:3001
```

首页名称应显示：

```text
CTF Strategy Radar
```

页面定位为：

```text
周大福海外市场 · 战略情报雷达
```

### Step 2：上传调研报告

上传你的调研报告，例如：

```text
C:\Users\TYF07\Downloads\report.md
```

支持 `.txt`、`.md`、`.pdf`。

### Step 3：填写情报任务

推荐填写：

```text
生成周大福今日海外市场战略简报，覆盖东南亚、日韩、北美、中东与澳洲。
```

也可以使用首页快捷任务：

- 每日简报
- 新市场进入
- 产品组合
- 合规预警

### Step 4：设置会商参数

点击高级设置，可调整：

- 会商轮次：建议 Demo 用 5-20
- 专家 Agent 数量：建议 10-12

真实 LLM 模式下，轮次和 Agent 越多，耗时和成本越高。

### Step 5：启动战略情报会商

点击：

```text
启动战略情报会商
```

系统会依次执行：

1. 构建海外市场知识图谱
2. 生成企业专家 Agent
3. 执行多轮战略情报会商
4. 生成战略简报

### Step 6：查看专家 Agent

会商完成后进入“专家 Agent”页面，可查看：

- 每个 Agent 的职责
- 当前机会/风险判断
- 专业领域
- 最新洞察
- 会商记录

### Step 7：查看战略简报

进入“战略简报”页面，可查看：

- 今日总览
- 高优先级预警
- 区域市场变化
- 竞品动态
- 产品与消费者趋势
- 渠道与电商机会
- 合规与供应链风险
- 部门行动清单
- 信息来源与可信度

也可以点击“下载报告”，导出 Markdown 文件。

### Step 8：追问验证

进入“追问验证”页面，可以问：

```text
为什么中东市场优先级升高？
```

```text
哪些竞品动作最值得关注？
```

```text
金价上涨对产品组合有什么影响？
```

```text
今天哪些部门需要行动？
```

系统会基于已生成的简报和专家会商记录回答。

### 可选：从 WorldMonitor 导入情报

在侧边栏点击：

```text
WM 情报筛选
```

流程：

1. 确认 WorldMonitor 正在 `http://localhost:3000` 运行。
2. 点击“拉取并筛选”。
3. 系统会读取 `full`、`finance`、`commodity` 三个 WorldMonitor digest。
4. 筛选 Agent 会保留与周大福海外市场相关的信息，分为“高优先级”“待观察”“低相关”。
5. 人工勾选要保留的情报。
6. 点击“用已审核情报启动会商”。
7. 系统会自动创建 GoldTo 会话，并进入会商控制台。

---

## Mock 模式说明

当 `.env` 中 `LLM_API_KEY` 为空或为占位值时，系统自动进入 Mock 模式。

Mock 模式会生成一套贴合周大福海外市场的模拟结果，包括：

- 周大福海外市场知识图谱
- 企业专家 Agent 人设
- 会商对话
- 每日战略简报
- 追问回答

这适合答辩、演示和无 API Key 环境下复现完整流程。

---

## API 概览

### 创建会话

```http
POST /api/sessions
```

返回：

```json
{
  "session_id": "abcd1234",
  "status": "idle"
}
```

### 上传材料

```http
POST /api/sessions/{session_id}/upload
```

表单字段：

| 字段 | 说明 |
|---|---|
| file | 上传的 `.txt` / `.md` / `.pdf` 文件 |
| prediction_goal | 情报任务描述 |
| rounds | 会商轮次 |
| agents_count | 专家 Agent 数量 |

### 启动会商

```http
POST /api/sessions/{session_id}/simulate
```

### 监听实时进度

```http
GET /api/sessions/{session_id}/stream
```

使用 SSE 推送：

- 知识图谱构建状态
- 专家 Agent 生成状态
- 会商互动记录
- 简报生成完成事件

### 获取战略简报

```http
GET /api/sessions/{session_id}/report
```

### 获取专家 Agent

```http
GET /api/sessions/{session_id}/agents
```

### 获取知识图谱

```http
GET /api/sessions/{session_id}/graph
```

### 追问验证

```http
POST /api/sessions/{session_id}/chat
```

请求：

```json
{
  "message": "金价上涨对产品组合有什么影响？",
  "agent_id": null
}
```

如果想和某个具体专家 Agent 对话，把 `agent_id` 设置为对应 Agent ID。

---

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | React 18, Vite, Tailwind CSS, lucide-react |
| 后端 | FastAPI, Python 3.11+, SSE |
| LLM | OpenAI-compatible API，默认支持阿里百炼通义千问 |
| 图谱 | NetworkX |
| 文件解析 | 文本 / Markdown / PDF |
| 记忆 | Zep Cloud 可选；未配置时使用内存模式 |
| 部署 | Docker Compose / 本地开发 |

---

## 项目结构

```text
.
├── backend
│   ├── main.py                  # FastAPI 入口
│   ├── api/routes.py             # 会话、上传、SSE、报告、聊天 API
│   ├── agents
│   │   ├── simulation_engine.py  # 当前主流程编排
│   │   ├── persona_agent.py      # 企业专家 Agent 生成与会商
│   │   └── report_agent.py       # 战略简报生成与追问
│   ├── graph/graph_builder.py    # 海外市场知识图谱构建
│   ├── memory/zep_memory.py      # 记忆管理
│   └── utils/mock_client.py      # 无 API Key 的周大福 Demo Mock
├── frontend
│   ├── src/pages/HomePage.jsx     # 上传资料与启动会商
│   ├── src/pages/SimulatePage.jsx # 会商控制台
│   ├── src/pages/WorldPage.jsx    # 企业专家 Agent 和知识图谱
│   ├── src/pages/ReportPage.jsx   # 战略简报
│   └── src/pages/ChatPage.jsx     # 追问验证
├── .env.example
├── package.json
└── README.md
```

---

## 当前版本边界

已实现：

- 上传企业调研材料
- 构建海外市场知识图谱
- 生成企业专家 Agent
- 多轮情报会商
- 输出周大福海外市场战略简报
- 追问验证
- Mock 模式完整演示

暂未接入：

- 实时网页抓取
- 企业内部 SAP / CRM / D-ONE / T MARK 数据
- 真实金价、汇率、社媒和电商 API
- 用户权限和企业级审计
- 报告自动定时推送

后续可扩展为：

- 每日 08:00 自动生成海外市场简报
- 按角色分发不同版本：管理层、海外运营、产品、品牌、合规、供应链
- 接入公开新闻、监管公告、社媒、电商评论、金价汇率
- 与企业内部销售、库存、客户和供应链数据联动

---

## 推荐 Demo 话术

本项目不是让 AI 直接替企业决策，而是让 AI 成为企业现有数据系统和公开信息之间的智能分析层。

它的价值在于：

- 把分散的海外信息转成统一结构
- 把新闻、竞品、社媒、合规和供应链信号变成业务语言
- 告诉团队今天该看什么、谁该处理、为什么重要
- 给管理层提供可追问、可验证、可行动的每日战略简报
