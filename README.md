# Recall — AI 智能错题本

本地优先（local-first）的 AI 错题本 Web 应用。核心价值链路：**录入 → AI 识别归档 → SM-2 复习 → 数据分析**。
全本地存储（SQLite + 向量库），零云服务依赖，开箱即可运行（外部 AI/OCR 服务缺失时自动降级为本地 Mock）。

---

## 技术栈

| 层 | 选型 |
|----|------|
| 前端 | Vue 3 (Composition API) + Vite + TypeScript + Tailwind CSS + Element Plus + Pinia + ECharts |
| 后端 | FastAPI + SQLAlchemy 2.0 + SQLite (FTS5) + ChromaDB(可选) |
| AI / OCR | DeepSeek API（可选）+ PaddleOCR-VL（可选），缺失时 Mock 降级 |
| 导出 | Markdown（原生）/ PDF（WeasyPrint 可选，缺失降级为样式化 HTML） |

---

## 目录结构

```
代码开发/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── api/            # 路由层（notebooks/errors/review/chat/dashboard/export/upgrade）
│   │   ├── services/       # 业务逻辑（ocr/ai/sm2/vector/export/insight）
│   │   ├── models/         # SQLAlchemy ORM 模型
│   │   ├── schemas/        # Pydantic 请求/响应模型
│   │   ├── core/           # config / database / exceptions
│   │   └── main.py         # 应用入口（含生产期前端静态托管）
│   ├── tests/              # pytest 单元测试 / 集成测试
│   ├── smoke_test.py       # 一键全链路冒烟脚本
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Vue3 前端
│   └── src/                # pages / components / stores / api / styles
├── tests/test_cases/       # 各里程碑测试用例文档（M1–M6）
├── docker-compose.yml
└── README.md
```

---

## 运行环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10+ | 后端运行环境（推荐 3.12） |
| Node.js | 18+（推荐 22） | 前端构建 / 开发服务器 |
| npm | 随 Node 自带 | 安装前端依赖 |
| Docker（可选） | 任意较新版本 | 仅生产部署需要 |

---

## 快速开始（开发模式）

> 约定：以下命令在 **Windows PowerShell** 中执行；`backend/venv` 虚拟环境若已存在可跳过创建步骤。

### 1. 启动后端

```powershell
cd backend

# 首次需要：创建并安装依赖（如已存在 venv，直接跳到下一步）
python -m venv venv
venv/Scripts/python.exe -m pip install -r requirements.txt

# 启动（默认 MOCK_EXTERNAL=true，无需任何 API Key 即可完整体验）
venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

- API 文档（Swagger）：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/health （返回 `{"code":0,"message":"success","data":{"status":"ok"}}` 即正常）
- 升级新功能（如 M7）后**必须重启后端**，否则旧进程仍占用 8000、不包含新路由（见下方排错）。

### 2. 启动前端

```powershell
cd frontend

# 首次需要：安装依赖（如已装好可跳过）
npm install

# 启动开发服务器
npm run dev
```

启动后**务必打开终端里实际打印的地址**（见 `Local:` 一行）。正常情况下是 http://localhost:5173，
但若 5173 被占用，Vite 会**静默**改用 5174 / 5175 ……，**以终端显示为准**，不要凭记忆填 5173。

前端通过 Vite 代理把 `/api` 转发到后端 8000，录入 → 复习 → 对话 → 看板 → 导出整条链路可直接使用。

---

## 常见问题与故障排查

### Q1. `pip install -r requirements.txt` 报 `UnicodeDecodeError: 'gbk' codec`
`requirements.txt` 已改为**纯 ASCII**（避免 Windows 下 pip 用 GBK 解码报错）。若你后续编辑该文件，
**不要写入中文或 `—` 等非 ASCII 字符**，否则会复现此错误。

### Q2. `uvicorn` 启动报 `WinError 10013`（端口被占用）
说明 8000 已被占用（通常是你之前启动的后端还活着）。先结束占用进程再启动：

```powershell
# 查谁占了 8000
netstat -ano | findstr :8000
# 假设查到 PID 为 xxxx，结束它
taskkill /PID xxxx /F
# 重新启动后端
venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

### Q3. 前端页面一直打不开 / 空白
最常见原因是 **Vite 端口被占、服务实际跑在 5174**。请直接打开终端 `Local:` 那行显示的地址，
而不是手动输入 5173。若仍空白，按 **F12 → Console** 查看红色报错。

### Q4. 页面运行时报错（红字）：`Cannot destructure property 'slots' of 'undefined'`
这是 `lucide-vue-next` 图标库在 Vite **dev 预打包**下与 Vue 3.5 的兼容问题，已通过在
`frontend/vite.config.ts` 中 `optimizeDeps.exclude: ['lucide-vue-next']` 修复。
**若你本机是用旧依赖缓存跑的**，需清缓存重启：

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules\.vite
npm run dev
```

### Q5. 升级代码（如新增 M7 功能）后页面/接口没变化
两步都必须做：
1. **重启后端**：结束旧 uvicorn 进程（Q2），让新路由（如 `/api/upgrade/*`）生效。
2. **清前端缓存**：`Remove-Item -Recurse -Force node_modules\.vite` 后 `npm run dev`。

### Q6. 数据看板图表空白
图表容器在骨架屏（`loading`）之后才挂载，代码已改为「`loading=false` + `nextTick` 后再渲染图表」。
若刷新后仍是空白，多为该项数据本身为空（如尚未复习 → 复习趋势为空），去录入 / 复习几道错题再回看即可。

### Q7. 语音录入 / 语音讲解朗读无反应
二者依赖浏览器原生 API（Web Speech / SpeechSynthesis），**Chrome / Edge 桌面版支持最佳**。
不支持的浏览器页面已做降级提示；朗读功能离线可用，无需任何外部服务。

---

## 生产部署（Docker 一键启动）

```bash
# 在「代码开发」根目录执行
docker compose up --build
```

构建完成后访问 http://localhost:8000 —— FastAPI 会直接托管已构建的前端 `frontend/dist`（见 `app/main.py` 的静态挂载），无需单独部署前端。

数据库持久化在名为 `recall-data` 的卷中。

---

## Mock 模式（默认）

环境无 `DEEPSEEK_API_KEY` 时，`MOCK_EXTERNAL=true`，以下能力使用确定性的本地实现，保证 MVP 全链路可离线演示：

- OCR：返回示例数学题文本
- AI 归类 / 变体题 / 批改 / 对话：返回结构化 Mock 结果
- 向量检索：使用内存字典兜底（ChromaDB 可选）

接入真实能力：在 `backend/.env` 配置 `DEEPSEEK_API_KEY`，并安装 `chromadb` / `paddleocr` / `weasyprint`（参见 `requirements.txt` 可选依赖段）。

---

## 测试

### 后端（pytest）

```bash
cd backend
venv/Scripts/python.exe -m pytest tests -q
```

覆盖：SM-2 算法（答对/答错/间隔/EF 下限/掌握度边界）、核心 API（笔记本 CRUD、文本录入、编辑、导出、无待复习路径）。

### 全链路冒烟

```bash
cd backend
# 先启动 uvicorn，再另开终端：
venv/Scripts/python.exe smoke_test.py
```

依次验证：健康检查 → 建本 → 录入 → 列表/FTS5 搜索 → 复习 start/submit（SM-2 集成）→ 看板 → 知识图谱 → MD/PDF 导出。

### 前端（vitest）

```bash
cd frontend
npm test
```

---

## 里程碑

| 里程碑 | 内容 | 测试文档 |
|--------|------|----------|
| M1 脚手架 | 前后端可运行、Swagger、笔记本 CRUD | tests/test_cases/M1-脚手架-测试用例.md |
| M2 智能录入 | 图片 OCR + 拆分 + 文本录入 + FTS5 搜索 | M2-智能录入-测试用例.md |
| M3 复习闭环 | SM-2 + 变体题 + 批改 | M3-复习闭环-测试用例.md |
| M4 对话看板 | SSE 对话 + 图表 + 知识图谱 | M4-对话看板-测试用例.md |
| M5 导出打磨 | PDF/MD 导出 + 空状态 + 错误提示 + 响应式 | M5-导出打磨-测试用例.md |
| M6 测试部署 | pytest/vitest + Docker + 验收 | M6-测试部署-测试用例.md |
| M7 智能升级 | AI 语音讲解 + 考前冲刺 + 看板升级 + 去重聚类 + 薄弱预警 + 语音录入 + 学习小组 | M7-智能升级-测试用例.md |

---

## 说明

- 统一响应格式：`{ "code": 0, "message": "success", "data": ... }`，业务错误使用业务码（1xxx/2xxx/3xxx/4xxx/5xxx/9xxx），HTTP 状态恒为 200。
- PDF 导出在缺少 WeasyPrint 的环境会降级为「样式化 HTML」下载，文件名后缀为 `.html`，内容一致、中文不乱码。
