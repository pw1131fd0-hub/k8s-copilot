# 🦞 Lobster K8s Copilot - 系統架構文件 (SA)

> **文件版本**: 1.0.0  
> **最後更新**: 2026-03-07  
> **狀態**: ✅ APPROVED

---

## 1. 系統概述

**Lobster K8s Copilot** 是一款 AI 驅動的 Kubernetes 運維助手平台，結合靜態 YAML 分析與智能 Pod 故障診斷。系統採用**微服務架構**設計：

- **Backend** (FastAPI): Kubernetes API 整合 + Pod 診斷 + YAML 掃描
- **AI Engine** (FastAPI): 多供應商 LLM 路由 (本地 Ollama → 雲端 OpenAI/Gemini)
- **Frontend** (React): 互動式 Dashboard，含 Monaco 編輯器與即時診斷
- **Database** (SQLAlchemy/SQLite/PostgreSQL): 審計追蹤與歷史記錄持久化

---

## 2. 系統架構圖

```mermaid
graph TB
    subgraph "User Layer"
        Browser[🌐 Browser]
    end

    subgraph "Frontend Container"
        React[⚛️ React SPA<br/>Port 3000]
        Nginx[📦 Nginx<br/>Static Hosting]
    end

    subgraph "Backend Container"
        FastAPI[🚀 FastAPI<br/>Port 8000]
        PodCtrl[Pod Controller]
        DiagCtrl[Diagnose Controller]
        YamlCtrl[YAML Controller]
        PodSvc[Pod Service]
        DiagSvc[Diagnose Service]
        YamlSvc[YAML Service]
        DiagRepo[Diagnose Repository]
    end

    subgraph "AI Engine Container"
        AIServer[🧠 FastAPI<br/>Port 8001]
        Diagnoser[AI Diagnoser]
        OllamaAdapter[Ollama Analyzer]
        OpenAIAdapter[OpenAI Analyzer]
        GeminiAdapter[Gemini Analyzer]
    end

    subgraph "External Services"
        K8sAPI[☸️ Kubernetes API]
        Ollama[🦙 Ollama<br/>Port 11434]
        OpenAI[☁️ OpenAI API]
        Gemini[☁️ Gemini API]
    end

    subgraph "Data Layer"
        SQLite[(🗄️ SQLite/PostgreSQL)]
    end

    Browser --> React
    React --> Nginx
    Nginx --> FastAPI

    FastAPI --> PodCtrl
    FastAPI --> DiagCtrl
    FastAPI --> YamlCtrl

    PodCtrl --> PodSvc
    DiagCtrl --> DiagSvc
    YamlCtrl --> YamlSvc

    PodSvc --> K8sAPI
    DiagSvc --> PodSvc
    DiagSvc --> AIServer
    DiagSvc --> DiagRepo
    YamlSvc --> AIServer

    DiagRepo --> SQLite

    AIServer --> Diagnoser
    Diagnoser --> OllamaAdapter
    Diagnoser --> OpenAIAdapter
    Diagnoser --> GeminiAdapter

    OllamaAdapter -.-> Ollama
    OpenAIAdapter -.-> OpenAI
    GeminiAdapter -.-> Gemini

    style Browser fill:#1E293B,stroke:#E85D4C,color:#F1F5F9
    style React fill:#1E293B,stroke:#3B82F6,color:#F1F5F9
    style FastAPI fill:#1E293B,stroke:#22C55E,color:#F1F5F9
    style AIServer fill:#1E293B,stroke:#F59E0B,color:#F1F5F9
    style SQLite fill:#1E293B,stroke:#94A3B8,color:#F1F5F9
```

---

## 3. 元件職責

### 3.1 Frontend (React SPA)

| 元件 | 職責 | 技術 |
|------|------|------|
| **App.jsx** | 路由與全域佈局 | React Router v6 |
| **DashboardPage** | 叢集狀態總覽、Pod 列表 | Tailwind CSS |
| **DiagnosePage** | AI 診斷結果展示 | React Markdown |
| **YamlScannerPage** | YAML 編輯與掃描 | Monaco Editor |
| **YamlDiffPage** | 多環境 YAML 差異比對 | DeepDiff 視覺化 |
| **HistoryPage** | 診斷歷史查詢 | 分頁 + 搜尋 |
| **useK8sData** | K8s 資料 Hook | Axios + 30s 自動刷新 |

### 3.2 Backend (FastAPI)

| 層級 | 元件 | 職責 |
|------|------|------|
| **Controller** | `pod_controller.py` | 處理 Pod 相關 HTTP 請求 |
| **Controller** | `diagnose_controller.py` | 處理 AI 診斷相關 HTTP 請求 |
| **Controller** | `yaml_controller.py` | 處理 YAML 掃描/差異 HTTP 請求 |
| **Service** | `PodService` | Kubernetes API 互動、Pod 資訊收集 |
| **Service** | `DiagnoseService` | 協調診斷流程、敏感資料遮蔽 |
| **Service** | `YamlService` | YAML 解析、規則檢查、AI 建議 |
| **Repository** | `DiagnoseRepository` | 診斷歷史資料存取抽象 |
| **Middleware** | `SecurityHeadersMiddleware` | 安全標頭 (HSTS, CSP, X-Frame-Options) |
| **Middleware** | `APIKeyAuthMiddleware` | 可選 API Key 驗證 |

### 3.3 AI Engine

| 元件 | 職責 |
|------|------|
| **AIDiagnoser** | 多供應商路由、Fallback 邏輯 |
| **OllamaAnalyzer** | 本地 Ollama 模型呼叫 |
| **OpenAIAnalyzer** | OpenAI GPT 系列呼叫 |
| **GeminiAnalyzer** | Google Gemini 呼叫 |
| **Prompt Templates** | K8s 專用提示詞模板 |

---

## 4. 資料流

### 4.1 Pod 診斷流程

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend
    participant K8s as K8s API
    participant AI as AI Engine
    participant DB as Database

    U->>FE: 點擊 "Diagnose" 按鈕
    FE->>BE: POST /api/v1/diagnose/{pod_name}
    BE->>K8s: read_namespaced_pod()
    K8s-->>BE: Pod 詳細資訊
    BE->>K8s: list_namespaced_event()
    K8s-->>BE: Pod 相關事件
    BE->>K8s: read_namespaced_pod_log()
    K8s-->>BE: 容器日誌
    BE->>BE: mask_sensitive_data()
    BE->>AI: POST /diagnose (context)
    AI->>AI: 選擇 Provider (Ollama→OpenAI→Gemini)
    AI-->>BE: {root_cause, remediation, model_used}
    BE->>DB: INSERT diagnose_history
    BE-->>FE: DiagnoseResponse
    FE-->>U: 顯示診斷結果面板
```

### 4.2 YAML 掃描流程

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend
    participant AI as AI Engine

    U->>FE: 貼上 YAML 內容
    FE->>BE: POST /api/v1/yaml/scan
    BE->>BE: yaml.safe_load_all()
    BE->>BE: 執行 8 條內建規則檢查
    alt 發現問題
        BE->>AI: POST /suggest (issues context)
        AI-->>BE: AI 修復建議 (markdown)
    end
    BE-->>FE: YamlScanResponse
    FE-->>U: 顯示問題清單 + AI 建議
```

### 4.3 YAML Diff 流程

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Frontend
    participant BE as Backend

    U->>FE: 輸入兩份 YAML
    FE->>BE: POST /api/v1/yaml/diff
    BE->>BE: yaml.safe_load() 兩份
    BE->>BE: DeepDiff(doc_a, doc_b)
    BE-->>FE: Structured diff dict
    FE-->>U: 顯示變更卡片 (✏️ ➕ ➖)
```

---

## 5. 部署架構

### 5.1 Docker Compose 部署

```mermaid
graph TB
    subgraph "Docker Network: lobster-network"
        Frontend[frontend<br/>:3000]
        Backend[backend<br/>:8000]
        AIEngine[ai-engine<br/>:8001]
        Ollama[ollama<br/>:11434<br/>(optional)]
    end

    subgraph "Volumes"
        DB[(lobster-db)]
        OllamaData[(ollama-data)]
    end

    subgraph "External"
        Host[Host Machine]
        K8sCluster[K8s Cluster]
        CloudAI[OpenAI/Gemini]
    end

    Host -->|:3000| Frontend
    Host -->|:8000| Backend
    Frontend --> Backend
    Backend --> AIEngine
    Backend --> K8sCluster
    Backend --> DB
    AIEngine --> Ollama
    AIEngine -.-> CloudAI
    Ollama --> OllamaData
```

### 5.2 服務依賴關係

| 服務 | 依賴 | 健康檢查 |
|------|------|----------|
| **backend** | ai-engine (healthy) | `curl http://localhost:8000/` |
| **frontend** | backend (healthy) | Port 80 listening |
| **ai-engine** | (無) | `curl http://localhost:8001/health` |
| **ollama** | (無) | Port 11434 listening |

### 5.3 容器配置

| 服務 | Port | Image | 資源限制 (建議) |
|------|------|-------|-----------------|
| frontend | 3000:80 | lobster-k8s-copilot/frontend | 128MB RAM |
| backend | 8000:8000 | lobster-k8s-copilot/backend | 512MB RAM |
| ai-engine | 8001:8001 | lobster-k8s-copilot/ai-engine | 256MB RAM |
| ollama | 11434:11434 | ollama/ollama | 4GB+ RAM (依模型) |

---

## 6. 第三方依賴

### 6.1 後端依賴

| 套件 | 版本 | 用途 |
|------|------|------|
| fastapi | ≥0.109.0 | Web 框架 |
| uvicorn | ≥0.27.0 | ASGI 伺服器 |
| kubernetes | ≥29.0.0 | K8s API 客戶端 |
| pydantic | ≥2.6.0 | 資料驗證 |
| sqlalchemy | ≥2.0.0 | ORM |
| alembic | ≥1.13.0 | 資料庫遷移 |
| httpx | ≥0.26.0 | 非同步 HTTP 客戶端 |
| openai | ≥1.12.0 | OpenAI API |
| google-genai | ≥1.0.0 | Gemini API |
| pyyaml | ≥6.0.1 | YAML 解析 |
| deepdiff | ≥6.7.0 | 物件差異比對 |
| slowapi | ≥0.1.9 | 速率限制 |

### 6.2 前端依賴

| 套件 | 版本 | 用途 |
|------|------|------|
| react | 18.2.0 | UI 框架 |
| react-router-dom | 6.22.0 | 路由 |
| axios | 1.6.0 | HTTP 客戶端 |
| @monaco-editor/react | 4.6.0 | YAML 編輯器 |
| react-markdown | 9.0.1 | Markdown 渲染 |
| tailwindcss | 3.4.0 | CSS 框架 |

### 6.3 外部服務

| 服務 | 用途 | 必要性 |
|------|------|--------|
| Kubernetes API | Pod 狀態、日誌、事件 | **必要** |
| Ollama | 本地 LLM 推論 | 三選一 |
| OpenAI API | 雲端 GPT 模型 | 三選一 |
| Google Gemini API | 雲端 Gemini 模型 | 三選一 |

---

## 7. 安全架構

### 7.1 認證與授權

```mermaid
flowchart LR
    Request[HTTP Request] --> Middleware{API Key<br/>Middleware}
    Middleware -->|No LOBSTER_API_KEY set| Public[Public Access<br/>⚠️ Warning logged]
    Middleware -->|Key set| AuthCheck{Check<br/>Authorization/X-API-Key}
    AuthCheck -->|Valid| Proceed[Continue to Router]
    AuthCheck -->|Invalid| Reject[401 Unauthorized]
    
    style Public fill:#F59E0B,stroke:#0F172A
    style Reject fill:#EF4444,stroke:#0F172A
```

### 7.2 安全防護層

| 層級 | 防護措施 |
|------|----------|
| **傳輸層** | HSTS (HTTPS 環境) |
| **應用層** | Security Headers (X-Frame-Options, CSP, XSS Protection) |
| **API 層** | 可選 API Key 驗證、速率限制 |
| **資料層** | 敏感資料遮蔽 (密碼、Token、API Key) |
| **輸入層** | Pydantic Schema 驗證、YAML 大小限制 (512KB) |

### 7.3 敏感資料處理

傳送至 LLM 前自動遮蔽：
- 密碼 (`password=...`, `passwd=...`)
- Token (`token=...`, `bearer ...`)
- API Key (`api_key=...`, `apiKey=...`)
- AWS 憑證 (`AKIA...`, `aws_secret_access_key=...`)
- SSH 金鑰 (`-----BEGIN PRIVATE KEY-----`)
- 資料庫連線字串 (`postgres://user:pass@host`)

---

## 8. 效能設計

### 8.1 超時配置

| 操作 | 超時 | 目的 |
|------|------|------|
| K8s Pod 列表 | 30s | 防止慢速 API 卡住 |
| K8s Pod 讀取 | 15s | 單一物件取得 |
| K8s 日誌取得 | 20s | 日誌串流 |
| AI Engine (HTTP) | 120s | LLM 推論時間 |
| Ollama 可用性檢查 | 3s | 快速健康檢查 |
| 前端 Axios 請求 | 30s | 請求超時 |

### 8.2 快取策略

| 層級 | 策略 |
|------|------|
| **AI Engine** | 模組級單例 (`_diagnoser`)，避免重複 Ollama 可用性檢查 |
| **Frontend** | 30 秒自動刷新 (可配置) |
| **Database** | 索引優化 (`pod_name`, `created_at`) |

### 8.3 擴展性考量

| 元件 | 擴展方式 |
|------|----------|
| Backend | 無狀態設計，可水平擴展 (Docker Compose scale / K8s HPA) |
| AI Engine | 獨立服務，可替換模型 |
| Database | 開發用 SQLite → 生產用 PostgreSQL |

---

## 9. 可用性設計

### 9.1 Fallback 機制

```mermaid
flowchart TD
    Start[AI 診斷請求] --> CheckOllama{Ollama<br/>可用?}
    CheckOllama -->|Yes| UseOllama[使用 Ollama]
    CheckOllama -->|No| CheckOpenAI{OpenAI<br/>API Key?}
    CheckOpenAI -->|Yes| UseOpenAI[使用 OpenAI]
    CheckOpenAI -->|No| CheckGemini{Gemini<br/>API Key?}
    CheckGemini -->|Yes| UseGemini[使用 Gemini]
    CheckGemini -->|No| Error[返回錯誤:<br/>"No AI provider configured"]
    
    UseOllama --> Success[返回診斷結果]
    UseOpenAI --> Success
    UseGemini --> Success
```

### 9.2 優雅降級

| 服務不可用 | 影響 | 降級行為 |
|------------|------|----------|
| K8s API | 無法取得 Pod 狀態 | 顯示連線錯誤，YAML 功能仍可用 |
| AI Engine | 無 AI 診斷/建議 | 僅顯示規則掃描結果，無 AI 建議 |
| Database | 無法保存歷史 | 診斷仍可執行，歷史功能暫停 |

---

## 10. 監控與可觀測性

### 10.1 健康檢查端點

| 服務 | 端點 | 預期回應 |
|------|------|----------|
| Backend | `GET /` | `{"status": "running", "version": "1.0.0"}` |
| AI Engine | `GET /health` | `{"status": "healthy"}` |

### 10.2 日誌配置

| 等級 | 用途 |
|------|------|
| `DEBUG` | K8s API 錯誤、AI 服務呼叫詳情 |
| `INFO` | 請求處理、診斷完成 |
| `WARNING` | K8s API 超時、缺少 AI Provider |
| `ERROR` | Pod 未找到、診斷失敗、DB 錯誤 |

---

## 11. 環境配置

### 11.1 環境變數

| 變數 | 說明 | 預設值 |
|------|------|--------|
| `DATABASE_URL` | 資料庫連線字串 | `sqlite:///./lobster.db` |
| `ALLOWED_ORIGINS` | CORS 允許來源 | 同源 |
| `LOBSTER_API_KEY` | API 認證金鑰 | (空，公開存取) |
| `AI_ENGINE_URL` | AI Engine HTTP 位址 | 本地 import |
| `OLLAMA_BASE_URL` | Ollama 服務位址 | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama 模型名稱 | `llama3` |
| `OPENAI_API_KEY` | OpenAI API 金鑰 | - |
| `OPENAI_MODEL` | OpenAI 模型 | `gpt-4o` |
| `GEMINI_API_KEY` | Gemini API 金鑰 | - |
| `GEMINI_MODEL` | Gemini 模型 | `gemini-2.0-flash` |
| `REACT_APP_API_URL` | 前端 API 位址 | `http://localhost:8000/api/v1` |

---

## 12. 技術限制

| 限制項目 | 說明 |
|----------|------|
| K8s 版本 | 支援 1.24+ (CoreV1 API) |
| 瀏覽器 | Chrome/Firefox/Edge 最新兩版本 |
| YAML 大小 | 單檔上限 512KB |
| 本地 AI | 需 Ollama 運行於配置位址 |
| 資料庫 | SQLite 適合單節點，生產建議 PostgreSQL |

---

## 附錄 A: 目錄結構

```
lobster-k8s-copilot/
├── backend/
│   ├── main.py              # FastAPI 入口點
│   ├── api/v1/router.py     # API 路由定義
│   ├── controllers/         # HTTP 請求處理
│   ├── services/            # 業務邏輯
│   ├── repositories/        # 資料存取
│   ├── models/              # ORM 模型 + Pydantic Schema
│   ├── database.py          # 資料庫連線
│   └── migrations/          # Alembic 遷移
├── ai_engine/
│   ├── main.py              # FastAPI 入口點
│   ├── diagnoser.py         # 多 Provider 路由
│   ├── analyzers/           # Provider 實作
│   └── prompts/             # 提示詞模板
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # 主應用
│   │   ├── pages/           # 頁面元件
│   │   ├── components/      # 共用元件
│   │   ├── hooks/           # Custom Hooks
│   │   └── services/        # API 客戶端
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml
├── docs/
│   ├── PRD.md
│   ├── SA.md                # 本文件
│   └── SD.md
└── tests/
```

---

*Document End*
