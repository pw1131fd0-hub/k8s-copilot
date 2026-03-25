# Lobster K8s Copilot — 部署指南

## 目錄

1. [前置需求](#前置需求)
2. [架構概覽](#架構概覽)
3. [Docker Compose 快速啟動](#docker-compose-快速啟動)
4. [Kubernetes 部署](#kubernetes-部署)
5. [環境變數參考](#環境變數參考)
6. [常見問題排除](#常見問題排除)

---

## 前置需求

### Docker Compose 部署

| 工具 | 最低版本 | 說明 |
|------|----------|------|
| Docker | 24.0+ | 容器執行環境 |
| Docker Compose | 2.20+ | 多容器編排 |
| kubeconfig | — | 存取 Kubernetes 叢集（選用） |

### Kubernetes 部署

| 工具 | 最低版本 | 說明 |
|------|----------|------|
| kubectl | 1.28+ | Kubernetes CLI |
| Kubernetes 叢集 | 1.28+ | EKS / GKE / AKS 或本地叢集 |
| nginx Ingress Controller | — | 處理外部流量路由 |
| 容器映像倉庫 | — | 用於儲存建置好的映像 |

---

## 架構概覽

本專案由三個微服務組成，透過內部網路互相通訊：

```
┌─────────────────────────────────────────────────────────┐
│                     外部流量                              │
│                        │                                 │
│              ┌─────────▼─────────┐                      │
│              │   nginx Ingress   │ :80 / :443            │
│              └────┬──────────┬───┘                      │
│                   │          │                           │
│         ┌─────────▼──┐  ┌───▼──────────┐               │
│         │  Frontend  │  │   Backend    │                │
│         │ React+nginx│  │   FastAPI    │                │
│         │   :80      │  │   :8000      │                │
│         └────────────┘  └──────┬───────┘               │
│                                │ AI_ENGINE_URL           │
│                         ┌──────▼───────┐                │
│                         │  AI Engine   │                │
│                         │   FastAPI    │                │
│                         │   :8001      │                │
│                         └──────────────┘                │
└─────────────────────────────────────────────────────────┘
```

### 服務說明

| 服務 | 職責 | 連接埠 |
|------|------|--------|
| **frontend** | React SPA，透過 nginx 提供服務，並代理 `/api/` 至 backend | 3000（外部）/ 80（內部）|
| **backend** | FastAPI REST API，處理 K8s 查詢與資料庫寫入 | 8000 |
| **ai-engine** | FastAPI 微服務，包裝 `AIDiagnoser`，提供 `/diagnose` 端點 | 8001 |

---

## Docker Compose 快速啟動

### 步驟一：設定環境變數

```bash
cp .env.example .env
# 編輯 .env，填入您的 AI API 金鑰
nano .env
```

至少需要設定以下其中一個 AI 提供者：

```bash
# OpenAI
OPENAI_API_KEY=sk-your-key-here

# 或 Google Gemini
GEMINI_API_KEY=your-gemini-key-here
```

### 步驟二：啟動所有服務

```bash
docker compose up --build -d
```

服務啟動順序：`ai-engine` → `backend`（等待 ai-engine 健康檢查通過）→ `frontend`

### 步驟三：驗證服務狀態

```bash
# 查看所有容器狀態
docker compose ps

# 查看日誌
docker compose logs -f

# 測試各服務健康狀態
curl http://localhost:8001/health   # AI Engine
curl http://localhost:8000/         # Backend
curl http://localhost:3000/         # Frontend
```

### 使用本地 LLM（Ollama）

若要啟用 Ollama 服務（本地 LLM），使用 `with-ollama` profile：

```bash
docker compose --profile with-ollama up --build -d

# 下載模型（首次使用）
docker exec lobster-ollama ollama pull llama3
```

### 停止服務

```bash
# 停止但保留資料
docker compose down

# 停止並刪除所有資料（含 volumes）
docker compose down -v
```

---

## Kubernetes 部署

### 步驟一：建置並推送映像

```bash
# 設定您的映像倉庫前綴
export REGISTRY=your-registry.example.com/lobster

# 建置映像
docker build -f backend/Dockerfile -t ${REGISTRY}/backend:latest .
docker build -f ai-engine/Dockerfile -t ${REGISTRY}/ai-engine:latest .
docker build -f frontend/Dockerfile -t ${REGISTRY}/frontend:latest .

# 推送映像
docker push ${REGISTRY}/backend:latest
docker push ${REGISTRY}/ai-engine:latest
docker push ${REGISTRY}/frontend:latest
```

### 步驟二：更新映像參考

編輯以下檔案，將 `lobster-k8s-copilot/` 前綴替換為您的實際映像倉庫路徑：

- `k8s/ai-engine-deployment.yaml`
- `k8s/backend-deployment.yaml`
- `k8s/frontend-deployment.yaml`

### 步驟三：設定 Secrets

```bash
# 建立 namespace
kubectl apply -f k8s/namespace.yaml

# 使用 base64 編碼您的 API 金鑰
OPENAI_KEY_B64=$(echo -n "sk-your-key" | base64)
GEMINI_KEY_B64=$(echo -n "your-gemini-key" | base64)

# 編輯 secret.yaml 填入編碼後的值，或直接使用 kubectl
kubectl create secret generic lobster-secrets \
  --namespace=lobster-k8s-copilot \
  --from-literal=OPENAI_API_KEY="sk-your-key" \
  --from-literal=GEMINI_API_KEY="your-gemini-key"
```

> **安全提示**：請勿將含有真實金鑰的 `k8s/secret.yaml` 提交至版本控制系統。

### 步驟四：套用所有 Manifests

```bash
# 套用 namespace 與設定
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 部署服務
kubectl apply -f k8s/ai-engine-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 設定 Ingress（需要先確認網域）
kubectl apply -f k8s/ingress.yaml
```

或一次套用所有檔案：

```bash
kubectl apply -f k8s/
```

### 步驟五：驗證部署狀態

```bash
# 查看所有資源
kubectl get all -n lobster-k8s-copilot

# 查看 Pod 狀態
kubectl get pods -n lobster-k8s-copilot -w

# 查看服務端點
kubectl get svc -n lobster-k8s-copilot

# 查看 Ingress
kubectl get ingress -n lobster-k8s-copilot
```

### 步驟六：設定 Ingress 網域

編輯 `k8s/ingress.yaml`，將 `lobster.example.com` 替換為您的實際網域：

```yaml
rules:
  - host: your-domain.example.com
```

### 啟用 TLS（選用）

若已安裝 cert-manager，取消 `k8s/ingress.yaml` 中以下註解：

```yaml
annotations:
  cert-manager.io/cluster-issuer: "letsencrypt-prod"
# ...
tls:
  - hosts:
      - your-domain.example.com
    secretName: lobster-tls-secret
```

---

## 環境變數參考

### AI Engine 服務

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `OPENAI_API_KEY` | — | OpenAI API 金鑰（與 Gemini 擇一必填）|
| `OPENAI_MODEL` | `gpt-4o` | 使用的 OpenAI 模型 |
| `GEMINI_API_KEY` | — | Google Gemini API 金鑰 |
| `GEMINI_MODEL` | `gemini-1.5-pro` | 使用的 Gemini 模型 |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama 服務位址 |
| `OLLAMA_MODEL` | `llama3` | 使用的 Ollama 模型 |

### Backend 服務

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite:///./lobster.db` | 資料庫連線字串 |
| `ALLOWED_ORIGINS` | `http://localhost:3000` | CORS 允許的來源 |
| `AI_ENGINE_URL` | `""` | AI Engine 服務位址（設定後啟用 HTTP 模式）|
| `KUBECONFIG` | `~/.kube/config` | kubeconfig 檔案路徑 |

### Frontend 服務

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `REACT_APP_API_URL` | `http://localhost:8000/api/v1` | Backend API 基礎 URL（建置時注入）|

---

## 常見問題排除

### AI Engine 無法啟動

**症狀**：`lobster-ai-engine` 容器持續重啟

**排查步驟**：
```bash
docker compose logs ai-engine
```

**常見原因**：
- 未設定任何 AI API 金鑰 → 在 `.env` 中至少設定一個
- 模型名稱錯誤 → 確認 `OPENAI_MODEL` 或 `GEMINI_MODEL` 的值

---

### Backend 無法連線至 AI Engine

**症狀**：診斷請求回傳 `AI Engine service call failed`

**排查步驟**：
```bash
# 確認 AI Engine 健康狀態
curl http://localhost:8001/health

# 查看 backend 日誌
docker compose logs backend
```

**常見原因**：
- `AI_ENGINE_URL` 設定錯誤 → Docker Compose 中應為 `http://ai-engine:8001`
- AI Engine 尚未通過健康檢查 → 等待約 20 秒後重試

---

### Frontend 無法連線至 Backend

**症狀**：瀏覽器 console 出現 CORS 錯誤或網路錯誤

**排查步驟**：
```bash
# 確認 backend 健康狀態
curl http://localhost:8000/

# 確認 ALLOWED_ORIGINS 設定
docker compose exec backend env | grep ALLOWED_ORIGINS
```

**常見原因**：
- `REACT_APP_API_URL` 指向錯誤的位址
- `ALLOWED_ORIGINS` 未包含 frontend 的來源 URL

---

### Kubernetes Pod 處於 Pending 狀態

**症狀**：`kubectl get pods` 顯示 Pod 為 `Pending`

**排查步驟**：
```bash
kubectl describe pod <pod-name> -n lobster-k8s-copilot
```

**常見原因**：
- 資源不足 → 調整 `resources.requests` 或增加節點
- PVC 無法綁定 → 確認 StorageClass 存在且有可用容量
- 映像無法拉取 → 確認映像倉庫路徑正確且有存取權限

---

### 資料庫遺失（SQLite）

**症狀**：重啟後歷史記錄消失

**說明**：
- **Docker Compose**：資料儲存在 `lobster-db` named volume，容器重啟不會遺失
- **Kubernetes**：資料儲存在 PVC，但多副本（`replicas: 2`）共用 SQLite 可能導致問題

**建議**：
- 生產環境建議改用 PostgreSQL，並更新 `DATABASE_URL`
- 若使用 SQLite，Kubernetes backend 的 `replicas` 應設為 `1`

---

### 查看完整日誌

```bash
# Docker Compose
docker compose logs --tail=100 -f [service-name]

# Kubernetes
kubectl logs -n lobster-k8s-copilot deployment/backend -f
kubectl logs -n lobster-k8s-copilot deployment/ai-engine -f
kubectl logs -n lobster-k8s-copilot deployment/frontend -f
```
