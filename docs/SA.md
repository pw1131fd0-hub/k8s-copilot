# 🦞 Lobster K8s Copilot - 系統架構設計文件 (SA)

## 1. 系統概述 (System Overview)
Lobster K8s Copilot 是一個分散式的 K8s 輔助系統。其架構設計旨在將 K8s 原生通訊與 AI 模型推理分離，提供高效且可擴展的 K8s YAML 管理與故障診斷功能。

## 2. 系統架構圖 (System Architecture)
- **Frontend Layer**: React + Tailwind CSS (SPA)
- **API Layer**: FastAPI (Python) - 負責業務邏輯、LLM 封裝、使用者授權。
- **K8s Controller Layer**: Go (client-go) - 高效處理與 K8s API Server 的通訊 (In-cluster/Out-of-cluster)。
- **AI Engine Layer**: OpenAI, Gemini (Public API) 或 Ollama (Local API)。
- **Database Layer**: PostgreSQL (存儲專案配置、YAML 歷史記錄、AI 診斷日誌)。

## 3. 模組職責分配 (Module Responsibilities)

### 3.1 Backend (Python FastAPI)
- **API Endpoints**: 提供 RESTful API 予前端。
- **LLM Prompt Manager**: 負責將 K8s context (Logs, Events, Describe) 組合為高品質 Prompt。
- **Safety Layer**: 過濾 K8s secret/sensitive data，避免隱私外洩。

### 3.2 K8s Service (Go client-go)
- **Cluster Watcher**: 監控 Pod 狀態變更 (Pending, Failed, CrashLoopBackOff)。
- **Resource Collector**: 收集故障 Pod 的 `describe`, `logs`, `events`。
- **YAML Linter**: 調用 `kube-linter` 或自定義 Go 邏輯偵測 Anti-pattern。

### 3.3 Frontend (React)
- **Dashboard**: 可視化 K8s 叢集健康度。
- **AI Chat/Log Interface**: 顯示診斷對話與日誌上下文。
- **YAML Editor**: 整合 Monaco Editor，即時顯示 YAML 掃描警告。

## 4. 關鍵技術決策 (Key Technical Decisions)
- **語言選擇**: 
  - **Python**: 因其成熟的 AI/LLM 生態系，作為主 API 與 AI 邏輯。
  - **Go**: 因其與 Kubernetes 的原生相容性，負責高效能的 K8s 原生操作。
- **AI 整合**: 支援 Ollama (Local)，提供給隱私敏感的企業內部使用。
- **通訊協議**: API 層使用 RESTful，若需即時狀態更新則使用 WebSocket。

## 5. 擴展性與維護性 (Scalability & Maintainability)
- **插件系統**: AI Diagnoser 採用介面化設計，易於串接新的 LLM 模型。
- **環境適配**: 支援多叢集管理 (Multi-cluster context switching)。

---
*文件建立日期：2026-03-06*
*撰寫者：Senior Architect (Lobster Team)*
