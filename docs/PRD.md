# 🦞 Lobster K8s Copilot - 產品需求文件 (PRD)

## 1. 文件資訊
| 項目 | 內容 |
|------|------|
| 文件版本 | 1.0.0 |
| 建立日期 | 2026-03-07 |
| 撰寫者 | Senior PM (Lobster Team) |
| 狀態 | Approved |

---

## 2. 產品概述

### 2.1 產品願景
**Lobster K8s Copilot** 是一款 AI 驅動的 Kubernetes YAML 管理與智能診斷工具，旨在簡化 DevOps 團隊的日常運維工作，透過自動化分析與 AI 輔助，大幅降低 K8s 故障排查時間並提升 YAML 配置的安全性與規範性。

### 2.2 核心價值主張
1. **K8s YAML 管理** — 靜態分析 YAML 配置，自動偵測反模式與安全漏洞
2. **AI 診斷** — 自動分析 Pod 故障，產生人類可讀的根因分析與修復建議

### 2.3 目標用戶
| 用戶類型 | 使用場景 |
|----------|----------|
| DevOps 工程師 | 日常 K8s 運維、故障排查、YAML 審查 |
| SRE 團隊 | 事故響應、根因分析、Postmortem |
| 平台工程師 | 制定 YAML 規範、預部署檢查 |

---

## 3. 功能需求 (Functional Requirements)

### 3.1 YAML 智能管理器 (YAML Master)

#### FR-001: YAML 靜態掃描
- **描述**：對用戶提交的 YAML 進行安全性與最佳實踐檢查
- **驗收標準**：
  - 偵測缺少 Resource Limits/Requests
  - 偵測 Privileged Container 設定
  - 偵測 runAsRoot / runAsNonRoot 問題
  - 偵測缺少 Health Probes (liveness/readiness)
  - 偵測 latest 標籤使用
- **優先級**：P0 (Must Have)

#### FR-002: YAML 多環境差異比較
- **描述**：比較兩份 YAML（如 staging vs production）的差異
- **驗收標準**：
  - 使用 DeepDiff 演算法計算結構差異
  - 返回新增、刪除、修改的欄位清單
  - 支援 JSON 格式輸出
- **優先級**：P1 (Should Have)

### 3.2 AI 故障診斷引擎 (AI Diagnoser)

#### FR-003: Pod 狀態監控
- **描述**：列出叢集中所有 Pod 及其狀態
- **驗收標準**：
  - 顯示 Pod 名稱、Namespace、Status、IP
  - 顯示 Pod Conditions
  - 支援分頁查詢
- **優先級**：P0 (Must Have)

#### FR-004: AI 故障診斷
- **描述**：對指定 Pod 進行 AI 驅動的故障分析
- **驗收標準**：
  - 自動擷取 Pod Logs 與 Events
  - 識別故障類型（CrashLoopBackOff, OOMKilled, ImagePullBackOff 等）
  - 產生根因分析（Root Cause）
  - 產生修復建議（Remediation）
  - 支援多模型：Ollama（本地優先）→ OpenAI/Gemini（雲端備援）
- **優先級**：P0 (Must Have)

#### FR-005: 診斷歷史記錄
- **描述**：儲存並查詢歷史診斷結果
- **驗收標準**：
  - 持久化儲存診斷記錄至資料庫
  - 支援依 Pod 名稱與時間範圍查詢
  - 返回完整診斷內容
- **優先級**：P1 (Should Have)

### 3.3 資料安全 (Data Security)

#### FR-006: 敏感資料脫敏
- **描述**：傳送至 AI 前自動遮蔽敏感資訊
- **驗收標準**：
  - 過濾包含 AUTH, PASS, TOKEN, KEY, SECRET 的環境變數
  - 遮蔽 base64 編碼的 Secret 內容
  - 遮蔽 Bearer Token / API Key
- **優先級**：P0 (Must Have)

---

## 4. 非功能需求 (Non-Functional Requirements)

### NFR-001: 效能
- API 響應時間 p95 < 500ms（不含 AI 推論時間）
- 支援同時處理 50 個並發請求
- YAML 掃描處理時間 < 1s（< 100KB 檔案）

### NFR-002: 可用性
- Web UI 響應式設計，支援桌面與平板
- 錯誤訊息使用繁體中文顯示
- API 返回標準化 JSON 錯誤格式

### NFR-003: 安全性
- 支援 HTTPS / TLS 1.3
- 實作 Rate Limiting 防止濫用
- CORS 白名單控制跨域請求
- 可選 API Key 認證機制
- Security Headers（X-Frame-Options, CSP 等）

### NFR-004: 可維護性
- 程式碼測試覆蓋率 > 70%
- 遵循 PEP8 / ESLint 規範
- 提供 OpenAPI/Swagger 文件

### NFR-005: 部署
- 支援 Docker Compose 單機部署
- 支援 Kubernetes Helm Chart 部署
- 環境變數配置，無硬編碼密鑰

---

## 5. 系統架構概覽

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│   Dashboard │ YAML Editor │ Pod Monitor │ Diagnose Panel   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│   Controllers → Services → Repositories                     │
│   ┌─────────────┬─────────────┬─────────────┐              │
│   │ Pod API     │ Diagnose API│ YAML API    │              │
│   └─────────────┴─────────────┴─────────────┘              │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐     ┌─────────────────┐     ┌─────────────┐
│ K8s Cluster │     │   AI Engine     │     │  Database   │
│   (API)     │     │ Ollama/OpenAI   │     │  SQLite/PG  │
└─────────────┘     └─────────────────┘     └─────────────┘
```

---

## 6. API 端點規格

| Method | Endpoint | 功能 |
|--------|----------|------|
| GET | `/api/v1/cluster/pods` | 列出所有 Pod |
| GET | `/api/v1/cluster/status` | 叢集連線狀態 |
| POST | `/api/v1/diagnose/{pod_name}` | AI 診斷 Pod |
| GET | `/api/v1/diagnose/history` | 診斷歷史 |
| POST | `/api/v1/yaml/scan` | YAML 靜態掃描 |
| POST | `/api/v1/yaml/diff` | YAML 差異比較 |

---

## 7. 里程碑與交付物

| 階段 | 交付物 | 狀態 |
|------|--------|------|
| M1: PRD | 產品需求文件 | ✅ 完成 |
| M2: SA/SD | 系統架構與詳細設計 | ✅ 完成 |
| M3: MVP | Backend + Frontend + AI Engine | ✅ 完成 |
| M4: Testing | 單元測試 + 整合測試 | ✅ 完成 |
| M5: Security | 資安審計與修復 | ✅ 完成 |
| M6: Deployment | Docker Compose / K8s 部署 | ✅ 完成 |

---

## 8. 風險與緩解措施

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| AI API 費用超支 | 高 | Local-first 策略，優先使用 Ollama |
| K8s API 權限不足 | 中 | 提供 RBAC 範本，降權執行 |
| YAML 解析漏洞 | 高 | 使用 safe_load，限制檔案大小 |

---

## 9. 附錄

### 9.1 術語表
| 術語 | 定義 |
|------|------|
| CrashLoopBackOff | Pod 反覆重啟失敗的狀態 |
| OOMKilled | 因記憶體不足被 Kernel 終止 |
| ImagePullBackOff | 無法拉取容器映像 |
| Probe | K8s 健康檢查機制 |

---

*文件結束*
