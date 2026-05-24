# GoldTo 部署说明
## 项目架构
GoldTo/
├── package.json              # npm scripts（dev/setup/test）
├── .env.example              # 环境变量模板
├── docker-compose.yml        # Docker 一键部署
├── frontend/
│   └── index.html            # 完整 SPA（38KB，Retro-Futuristic 风格）
│       ├── 仿真配置面板
│       ├── 实时推演流（Round Feed）
│       ├── 知识图谱 SVG 可视化
│       ├── Markdown 预测报告渲染
│       └── 深度对话（Agent + ReportAgent）
└── backend/
    ├── app.py                # Flask REST API（11 个路由）
    ├── agents/
    │   ├── agent.py          # 8 种智能体原型 + 个性化记忆
    │   └── simulation.py     # 多线程仿真引擎（5阶段流水线）
    ├── graph/
    │   └── knowledge_graph.py # GraphRAG 知识图谱（NetworkX）
    ├── utils/
    │   └── llm_client.py     # OpenAI 兼容 LLM 客户端 + Mock 模式
    └── memory/               # 预留 Zep Cloud 接口
    
## 环境要求
- Node.js 18+
- Python 3.11/3.12
- （可选）uv 包管理器

## 快速启动

```bash
# 1. 复制环境变量
cp .env.example .env
# 编辑 .env，填入 LLM_API_KEY 等

# 2. 安装依赖
npm run setup:all

# 3. 启动
npm run dev
```

## 访问地址
- 前端：http://localhost:3000
- 后端 API：http://localhost:5001

## Mock 模式
未填写 LLM_API_KEY 时，系统自动进入 Mock 模式，使用内置模拟数据，可完整体验所有功能。

## API Keys 获取
- **LLM（推荐阿里百炼）**：https://bailian.console.aliyun.com/
  - 模型：qwen-plus
  - BASE_URL：https://dashscope.aliyuncs.com/compatible-mode/v1
- **也支持**：OpenAI / DeepSeek / Moonshot 等任意 OpenAI 兼容接口
- **Zep Cloud（可选）**：https://app.getzep.com/ （免费额度足够使用）
