# 🦞 Lobster K8s Copilot

**AI-Powered Kubernetes YAML Management & Diagnostics Tool**

## 🎯 核心功能
1. **YAML 智能管理器 (YAML Master)**
   - YAML 配置分析與反模式偵測 (缺少 Resource Limits、Privileged Container、runAsRoot、缺少 Probe 等)
   - 多環境配置對比 (DeepDiff)
   - 部署前預檢驗

2. **AI 故障診斷引擎 (AI Diagnoser)**
   - 自動監控 Pod 狀態
   - 故障根因分析 (CrashLoopBackOff, OOM, ImagePullBackOff 等)
   - 多模型支援：Local-first (Ollama) → Cloud fallback (OpenAI / Gemini)
   - 自然語言診斷建議

## 🏗️ 技術棧
- **Backend**: Python FastAPI (Controller-Service-Repository 架構)
- **Frontend**: React + Tailwind CSS + Monaco Editor
- **AI**: OpenAI / Gemini API 或 Ollama (local)
- **Database**: SQLAlchemy (SQLite/PostgreSQL)

## 📁 目錄結構
```
lobster-k8s-copilot/
├── backend/
│   ├── main.py            # FastAPI app + middleware (Rate limiting, CORS)
│   ├── database.py        # SQLAlchemy connection & init
│   ├── utils.py           # Sensitive data masking
│   ├── models/            # Pydantic schemas + ORM models
│   ├── controllers/       # Route handlers (pod, diagnose, yaml)
│   ├── services/          # Business logic
│   └── repositories/      # Database access layer
├── ai-engine/             # LLM integration
│   ├── diagnoser.py       # Multi-model router (local-first)
│   ├── analyzers/         # OpenAI, Gemini, Ollama providers
│   └── prompts/           # Prompt templates
├── frontend/              # React dashboard
│   └── src/
│       ├── components/    # PodList, DiagnosePanel, YAMLCodeEditor
│       ├── pages/         # Dashboard
│       ├── hooks/         # useK8sData
│       └── utils/         # API client
├── tests/                 # Unit & integration tests (28 tests)
└── docs/                  # PRD, SA, SD, SYSTEM_FLOW
```

## 🚀 Quick Start

### Backend
```bash
# 設定環境變數
cp .env.example .env   # 填入 OPENAI_API_KEY 或啟動 Ollama

pip install -r backend/requirements.txt
cd backend && uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### 執行測試
```bash
python3 -m pytest tests/ -v
```

## 🔑 環境變數
| 變數 | 說明 | 預設值 |
|------|------|--------|
| `DATABASE_URL` | 資料庫連線字串 | `sqlite:///./lobster.db` |
| `OPENAI_API_KEY` | OpenAI API Key | — |
| `GEMINI_API_KEY` | Google Gemini API Key | — |
| `OLLAMA_BASE_URL` | Ollama 本地端點 | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama 使用的模型 | `llama3` |

## 📡 API Endpoints
| Method | Path | 說明 |
|--------|------|------|
| `GET` | `/api/v1/cluster/pods` | 列出所有 Pod 與狀態 |
| `GET` | `/api/v1/cluster/status` | 叢集連線狀態 |
| `POST` | `/api/v1/diagnose/{pod_name}` | AI 診斷指定 Pod |
| `GET` | `/api/v1/diagnose/history` | 歷史診斷記錄 |
| `POST` | `/api/v1/yaml/scan` | YAML 靜態掃描 |
| `POST` | `/api/v1/yaml/diff` | 兩份 YAML 差異比較 |

## 📜 License
MIT
