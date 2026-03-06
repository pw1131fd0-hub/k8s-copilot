# 🦞 Lobster K8s Copilot - 系統詳細設計文件 (SD)

## 1. 詳細組件設計 (Component Design)

### 1.1 YAML Master (YAML 管理模組)
- **YAML Scanner**: 掃描 YAML 文件，透過 Regex 或 kube-linter 執行規則匹配。
  - **核心規則**: 缺少 CPU/Memory Limit、Privileged 權限、Root User、Liveness/Readiness Probe。
- **YAML Pre-flight (Go)**:
  - 調用 `kubectl auth can-i` 與 `kubectl apply --dry-run=server` 預檢驗 YAML。
- **Diffing Engine**: 使用 `DeepDiff` (Python) 執行 YAML 配置對比。

### 1.2 AI Diagnoser (AI 診斷模組)
- **Event Watcher (Go)**:
  - 偵測 Pod 狀態變更事件，若狀態為 `CrashLoopBackOff`, `OOMKilled`, `ImagePullBackOff` 等則觸發診斷。
- **Context Collector (Python)**:
  - 調用 Go Controller API 獲取 `kubectl describe pod <name>` 與 `kubectl logs <name> --tail=100`。
- **AI Prompt Engine**:
  - 封裝 K8s 錯誤日誌至 AI Prompt Template。
  - **Template**:
    ```text
    Role: K8s SRE Expert.
    Task: Diagnose the pod error.
    Context: {Describe Output}, {Recent Logs}.
    Output: Structural root cause analysis and remediation command.
    ```

### 1.3 Backend API (FastAPI)
- **架構模式**: Controller-Service-Repository 模式。
- **Endpoint 列表**:
  - `GET /v1/cluster/pods`: 獲取 Pod 列表與狀態。
  - `POST /v1/diagnose/{pod_name}`: 觸發 AI 診斷。
  - `POST /v1/yaml/scan`: 執行 YAML 掃描。

### 1.4 Frontend (React)
- **組件劃分**:
  - `PodList.js`: 顯示 Pod 的狀態圖標 (Red/Green/Yellow)。
  - `DiagnosePanel.js`: 側邊欄顯示 AI 分析出的 Markdown 報告。
  - `YAMLCodeEditor.js`: 集成 Monaco Editor，標註錯誤行號。

## 2. 資料庫 Schema (Database Schema)

### 2.1 Table: `projects`
- `id`: UUID (PK)
- `name`: String
- `k8s_context`: String

### 2.2 Table: `diagnose_history`
- `id`: UUID (PK)
- `pod_name`: String
- `namespace`: String
- `error_type`: String
- `ai_analysis`: Text (JSON)
- `created_at`: Timestamp

## 3. 序列圖 (Sequence Diagram) - 故障診斷流程
1. **User** -> **Frontend**: 點擊「Diagnose」按鈕。
2. **Frontend** -> **FastAPI**: 調用 `POST /diagnose/{pod_name}`。
3. **FastAPI** -> **Go Controller**: 調用 `GetPodContext(pod_name)`。
4. **Go Controller** -> **K8s API**: 獲取 Logs & Describe。
5. **Go Controller** -> **FastAPI**: 返回結構化上下文。
6. **FastAPI** -> **LLM (OpenAI/Ollama)**: 發送 Prompt 並獲取回覆。
7. **FastAPI** -> **Frontend**: 返回 AI 診斷報告。

## 4. 安全與容錯機制 (Security & Fault Tolerance)
- **Rate Limiting**: 限制每分鐘 AI 診斷請求次數，防止 API 額度超支。
- **Sensitive Data Masking**: 使用 Regex 去除 Pod 環境變數中的 `PASSWORD`, `SECRET`, `TOKEN` 關鍵字。

---
*文件建立日期：2026-03-06*
*撰寫者：Senior Architect (Lobster Team)*
