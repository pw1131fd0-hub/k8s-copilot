# 🦞 Lobster K8s Copilot - Product Requirements Document (PRD)

> **版本**: 1.0.0  
> **最後更新**: 2026-03-07  
> **狀態**: APPROVED

---

## 1. 產品願景與核心痛點 (Why)

### 1.1 產品願景

**Lobster K8s Copilot** 是一個智能 Kubernetes 運維助手，旨在降低 K8s 配置錯誤率、加速故障排查、並確保多環境配置一致性。透過 AI 驅動的診斷與 YAML 掃描，讓 DevOps/SRE 團隊能更專注於價值創造而非重複性排查工作。

### 1.2 核心痛點

| 痛點 | 影響 | Lobster 解決方案 |
|------|------|-----------------|
| **K8s YAML 設定容易出錯** | 缺 resource limits 導致 OOM、權限過大造成安全風險、probe 未設造成服務不穩定 | YAML 掃描器：部署前自動偵測 anti-pattern |
| **Pod 故障排查耗時** | CrashLoopBackOff / OOM / ImagePullBackOff 需要手動查看 logs、events、describe 輸出 | AI 故障診斷：自動分析根因 + 給出修復建議 |
| **多環境設定容易飄移** | dev/staging/prod YAML 差異未被發現，導致「在我本地可以跑」問題 | 多環境 Diff：比對差異、標出潛在風險 |
| **診斷經驗難以積累** | 過去排查過的問題沒有記錄，相同問題重複排查 | 診斷歷史：記錄過去診斷結果，支援搜尋回顧 |
| **缺乏即時監控視野** | 需要切換多個工具查看叢集狀態 | Dashboard：即時顯示 Pod 狀態、告警、掃描結果 |

---

## 2. 目標用戶畫像與使用場景

### 2.1 目標用戶

| 角色 | 描述 | 主要需求 |
|------|------|---------|
| **DevOps Engineer** | 負責 CI/CD 流程、部署自動化、環境管理 | 快速驗證 YAML、部署前攔截問題 |
| **SRE (Site Reliability Engineer)** | 負責系統可靠性、故障排查、on-call | 快速診斷 Pod 故障、減少 MTTR |
| **後端工程師** | 開發應用程式、撰寫 K8s 配置 | 確保 YAML 符合最佳實踐 |

### 2.2 User Stories

#### US-001: YAML 掃描預防問題
> **作為** DevOps Engineer  
> **我想要** 在部署前掃描我的 K8s YAML 配置  
> **以便** 在問題進入生產環境前及時發現並修正

**驗收標準 (Acceptance Criteria):**
- [ ] 可上傳或貼上 YAML 內容
- [ ] 系統自動檢測 anti-pattern（resource limits、privileged、probes 等）
- [ ] 每個問題顯示嚴重程度（ERROR/WARNING/INFO）
- [ ] 提供 AI 生成的修復建議
- [ ] 掃描結果在 3 秒內返回

#### US-002: AI 故障診斷
> **作為** SRE  
> **我想要** 一鍵診斷故障 Pod  
> **以便** 快速定位根因並獲取修復方案，減少 MTTR

**驗收標準 (Acceptance Criteria):**
- [ ] 可選擇任意 Pod 進行診斷
- [ ] 自動收集 Pod describe、logs、events
- [ ] AI 分析返回：root cause、detailed analysis、remediation
- [ ] 支援 CrashLoopBackOff、OOM、ImagePullBackOff 等常見錯誤類型
- [ ] 診斷結果在 30 秒內返回

#### US-003: 多環境 YAML Diff
> **作為** DevOps Engineer  
> **我想要** 比對 dev/staging/prod 的 YAML 差異  
> **以便** 確保環境一致性，避免配置飄移

**驗收標準 (Acceptance Criteria):**
- [ ] 可選擇兩份 YAML 進行比對
- [ ] 以視覺化方式顯示差異（新增/刪除/修改）
- [ ] 標出可能造成風險的差異
- [ ] Diff 結果在 2 秒內返回

#### US-004: 診斷歷史回顧
> **作為** SRE  
> **我想要** 查看過去的診斷記錄  
> **以便** 追蹤問題趨勢、避免重複排查

**驗收標準 (Acceptance Criteria):**
- [ ] 列出所有歷史診斷記錄
- [ ] 支援按 Pod 名稱、namespace、時間範圍搜尋
- [ ] 可查看每筆記錄的完整診斷結果
- [ ] 診斷記錄永久保存

#### US-005: Dashboard 概覽
> **作為** 後端工程師  
> **我想要** 即時看到叢集 Pod 狀態  
> **以便** 快速了解服務健康狀況

**驗收標準 (Acceptance Criteria):**
- [ ] 顯示所有 Pod 列表及其狀態
- [ ] 區分 Running/Succeeded 與異常狀態
- [ ] 顯示叢集連線狀態
- [ ] 支援手動刷新
- [ ] 頁面載入時間 < 2 秒

---

## 3. 功能需求清單 (優先級分級)

### P0 - 核心功能 (MVP 必備)

| ID | 功能 | 描述 | 驗收標準 |
|----|------|------|---------|
| F-001 | YAML 掃描器 | 偵測 K8s YAML anti-pattern | 檢測 ≥8 種 anti-pattern；每項含嚴重級別 |
| F-002 | AI 故障診斷 | 分析 Pod 故障並給出修復建議 | 支援 CrashLoopBackOff/OOM/ImagePullBackOff |
| F-003 | Pod 列表 | 顯示叢集所有 Pod | 顯示 name/namespace/status/IP |
| F-004 | 叢集連線狀態 | 顯示後端是否可連接 K8s API | 實時顯示 connected/disconnected |
| F-005 | AI 修復建議 | YAML 掃描結果附帶 AI 建議 | 每次掃描返回 ai_suggestions |

### P1 - 重要功能 (第二迭代)

| ID | 功能 | 描述 | 驗收標準 |
|----|------|------|---------|
| F-006 | 多環境 YAML Diff | 比對兩份 YAML 差異 | 顯示 added/removed/changed 欄位 |
| F-007 | 診斷歷史記錄 | 持久化存儲診斷結果 | 診斷後自動存入資料庫 |
| F-008 | 歷史記錄查詢 | 支援搜尋歷史診斷 | 按 pod_name/namespace 過濾 |
| F-009 | YAML 編輯器 | 前端 YAML 編輯器 | 語法高亮、即時掃描 |

### P2 - 增強功能 (未來迭代)

| ID | 功能 | 描述 | 驗收標準 |
|----|------|------|---------|
| F-010 | 告警通知 | 異常 Pod 告警 | 支援 Slack/Email/Webhook |
| F-011 | 自訂掃描規則 | 用戶可新增自訂 anti-pattern | YAML 規則定義格式 |
| F-012 | 團隊協作 | 多用戶、權限管理 | RBAC 支援 |
| F-013 | CI/CD 整合 | 與 GitHub Actions/GitLab CI 整合 | CLI 掃描指令 |
| F-014 | 報表匯出 | 匯出診斷報告 | PDF/CSV 格式 |

---

## 4. 非功能需求 (NFR)

### 4.1 效能 (Performance)

| 指標 | 目標 | 量測方式 |
|------|------|---------|
| YAML 掃描回應時間 | < 3 秒 (p95) | API response time |
| AI 診斷回應時間 | < 30 秒 (p95) | API response time |
| YAML Diff 回應時間 | < 2 秒 (p95) | API response time |
| Dashboard 首次載入 | < 2 秒 (p95) | Page load time |
| 並發用戶支援 | ≥ 50 同時在線 | Load testing |
| YAML 最大大小 | 512 KB | Validation |

### 4.2 安全 (Security)

| 要求 | 實作方式 |
|------|---------|
| API 認證 | 可選 API Key (X-API-Key / Bearer token) |
| CORS 控制 | 白名單制，預設不允許跨域 |
| 安全標頭 | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy, HSTS |
| 敏感資料遮罩 | 日誌和 AI prompt 中自動遮罩密碼/金鑰 |
| 輸入驗證 | Pydantic schema 驗證，K8s 命名規則檢查 |
| Rate Limiting | 防止 API 濫用 |
| 依賴掃描 | 定期檢查 CVE |

### 4.3 可用性 (Availability)

| 指標 | 目標 |
|------|------|
| 系統可用性 | 99.5% uptime |
| 容錯機制 | AI 服務降級時回傳空建議，不影響核心功能 |
| 健康檢查 | 所有服務提供 /health endpoint |

### 4.4 擴展性 (Scalability)

| 面向 | 設計 |
|------|------|
| 水平擴展 | 無狀態 API 服務，支援多副本 |
| AI 模型切換 | Local-first (Ollama) → 雲端 fallback (OpenAI/Gemini) |
| 資料庫 | SQLite 單機 → PostgreSQL 遷移路徑 (Alembic) |

### 4.5 可維護性 (Maintainability)

| 要求 | 實作方式 |
|------|---------|
| 日誌格式 | 結構化 JSON 日誌 |
| 監控指標 | Prometheus-ready endpoints |
| API 文件 | OpenAPI 3.0 (Swagger UI + ReDoc) |
| 測試覆蓋率 | ≥ 80% |

---

## 5. 技術限制與選型

### 5.1 技術棧

| 層級 | 技術選擇 | 理由 |
|------|---------|------|
| **後端框架** | Python FastAPI | 高效能非同步、自動 OpenAPI 文件、類型安全 |
| **前端框架** | React 18 + Tailwind CSS | 組件化、深色主題友好、科技感 UI |
| **AI 模型** | Ollama (本地優先) → OpenAI/Gemini (雲端 fallback) | 資料隱私 + 彈性 |
| **資料庫** | SQLite (開發) → PostgreSQL (生產) | 簡單起步、易於遷移 |
| **ORM** | SQLAlchemy 2.0 + Alembic | 成熟穩定、遷移支援 |
| **K8s Client** | kubernetes-client/python | 官方維護 |
| **容器化** | Docker Compose | 本地開發、單機部署 |
| **部署** | Docker Compose / K8s (Helm) | 開發到生產一致性 |

### 5.2 系統需求

| 項目 | 最低需求 |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker | 20.10+ |
| RAM | 2GB (無 Ollama) / 8GB (含 Ollama) |
| 磁碟 | 1GB (不含 Ollama 模型) |

### 5.3 依賴限制

- **Ollama**: 可選，需要 GPU 以獲得最佳效能
- **OpenAI/Gemini API**: 需要有效 API Key
- **K8s Cluster**: 需要有效 kubeconfig 或執行於叢集內

---

## 6. 競品分析

| 產品 | 特點 | Lobster 差異化 |
|------|------|---------------|
| **Datree** | YAML 政策檢查 | Lobster 加入 AI 診斷 + 即時監控 |
| **Kube-score** | YAML 評分 | Lobster 提供修復建議 + 歷史追蹤 |
| **K9s** | 終端機 UI | Lobster 提供 Web UI + AI 分析 |
| **Lens** | 桌面 IDE | Lobster 更輕量、AI 驅動 |
| **Kubeshark** | 流量分析 | 不同定位，Lobster 聚焦配置+診斷 |

---

## 7. MVP 範圍與迭代路線圖

### 7.1 MVP (v1.0) - 當前版本

- [x] YAML 掃描器 (8+ anti-pattern rules)
- [x] AI 故障診斷 (CrashLoopBackOff/OOM/ImagePullBackOff)
- [x] 多環境 YAML Diff
- [x] 診斷歷史記錄
- [x] Dashboard (Pod 列表 + 叢集狀態)
- [x] Docker Compose 部署
- [x] Ollama/OpenAI/Gemini 多模型支援

### 7.2 v1.1 - 增強穩定性

- [ ] 完整測試覆蓋 (≥80%)
- [ ] 資安審計通過
- [ ] 效能優化
- [ ] 文件完善

### 7.3 v1.2 - 增強功能

- [ ] 告警通知 (Slack/Email)
- [ ] 自訂掃描規則
- [ ] CI/CD 整合

### 7.4 v2.0 - 企業版

- [ ] 多用戶 + RBAC
- [ ] PostgreSQL 支援
- [ ] Helm Chart
- [ ] 報表匯出

---

## 8. UI/UX 設計規範

### 8.1 色彩計畫

#### 深色主題 (主要)

| 用途 | 色彩名稱 | Hex Code | 範例 |
|------|---------|----------|------|
| 主色 (Primary) | Indigo | `#6366F1` | 按鈕、連結、active 狀態 |
| 輔色 (Secondary) | Slate | `#64748B` | 次要文字、邊框 |
| 背景色 (Background) | Slate-900 | `#0F172A` | 主背景 |
| 表面色 (Surface) | Slate-800 | `#1E293B` | 卡片、彈窗 |
| 文字主色 | White | `#FFFFFF` | 主要文字 |
| 文字次色 | Slate-300 | `#CBD5E1` | 次要文字 |
| 成功 (Success) | Green | `#22C55E` | Running 狀態 |
| 警告 (Warning) | Amber | `#F59E0B` | Warning 等級 |
| 錯誤 (Error) | Red | `#EF4444` | Error 等級、Unhealthy |
| 資訊 (Info) | Cyan | `#06B6D4` | Info 等級 |

#### 淺色主題 (備用)

| 用途 | 色彩名稱 | Hex Code |
|------|---------|----------|
| 背景色 | Slate-50 | `#F8FAFC` |
| 表面色 | White | `#FFFFFF` |
| 文字主色 | Slate-900 | `#0F172A` |
| 文字次色 | Slate-500 | `#64748B` |

### 8.2 字型選擇

| 用途 | 字型 | 備選 |
|------|------|------|
| UI 文字 | Inter | system-ui, -apple-system |
| 程式碼/YAML | JetBrains Mono | Fira Code, Consolas |
| 標題 | Inter Bold | - |

### 8.3 元件風格

| 元素 | 規範 |
|------|------|
| 圓角 (Border Radius) | Small: 4px, Medium: 8px, Large: 12px, XL: 16px |
| 陰影 (Shadow) | Subtle: `0 1px 2px rgba(0,0,0,0.05)`, Elevated: `0 4px 6px rgba(0,0,0,0.1)` |
| 間距 (Spacing) | 基於 4px 網格 (4, 8, 12, 16, 24, 32, 48) |
| 動畫 | 過渡時間 150-300ms, ease-in-out |
| 邊框 | 1px solid, 透明度 10-20% |

### 8.4 RWD 斷點

| 名稱 | 寬度 | 用途 |
|------|------|------|
| Mobile | < 640px | 單欄佈局 |
| Tablet | 640px - 1024px | 雙欄佈局 |
| Desktop | 1024px - 1440px | 標準佈局 |
| Wide | > 1440px | 寬螢幕佈局 |

### 8.5 深色/淺色模式

- **預設**: 深色主題 (符合終端機使用者偏好)
- **切換**: 系統偏好優先，支援手動切換
- **儲存**: LocalStorage 持久化用戶偏好

---

## 9. 成功指標 (KPI)

### 9.1 產品指標

| 指標 | 目標 | 量測方式 |
|------|------|---------|
| 日活用戶 (DAU) | ≥ 50 | Analytics |
| YAML 掃描次數/日 | ≥ 100 | API logs |
| AI 診斷次數/日 | ≥ 30 | Database |
| 平均診斷準確率 | ≥ 80% | 用戶回饋 |
| 平均故障排查時間 (MTTR) 降低 | ≥ 30% | 用戶調查 |

### 9.2 技術指標

| 指標 | 目標 | 量測方式 |
|------|------|---------|
| API 成功率 | ≥ 99% | Monitoring |
| p95 回應時間 | < 5s | APM |
| 測試覆蓋率 | ≥ 80% | CI |
| 安全漏洞 (High/Critical) | 0 | Security scan |

---

## 10. 現有程式碼評估與重構需求

### 10.1 符合項目 ✅

| 功能 | 現有實作 | 符合度 |
|------|---------|--------|
| YAML 掃描器 | `backend/services/yaml_service.py` - 8 條 anti-pattern 規則 | 100% |
| AI 故障診斷 | `backend/services/diagnose_service.py` + `ai_engine/diagnoser.py` | 100% |
| 多模型支援 | Ollama/OpenAI/Gemini 完整實作 | 100% |
| 多環境 Diff | `yaml_service.diff()` 使用 DeepDiff | 100% |
| 診斷歷史 | `DiagnoseHistory` ORM model + DB 持久化 | 100% |
| Dashboard | React Dashboard + PodList + YAMLCodeEditor | 100% |
| 安全標頭 | SecurityHeadersMiddleware 完整實作 | 100% |
| API 認證 | APIKeyAuthMiddleware 可選認證 | 100% |
| Rate Limiting | slowapi 整合 | 100% |

### 10.2 待改進項目 🔧

| 項目 | 現況 | 建議改進 |
|------|------|---------|
| 前端深色主題 | 目前是淺色主題 | 實作深色主題切換 |
| 歷史記錄查詢 API | 有 Model 但缺少 API endpoint | 新增 GET /api/v1/diagnose/history |
| 測試覆蓋率 | 部分測試 | 提升至 80%+ |
| 前端 YAML Diff UI | 後端有 API，前端未整合 | 新增 Diff 視覺化元件 |

### 10.3 不需重構項目

- 後端架構 (Controller → Service → Repository 分層) ✅
- AI Engine 微服務架構 ✅
- Docker Compose 配置 ✅
- 資料庫 Schema ✅

---

## 附錄 A: Anti-Pattern Rules 清單

| Rule ID | 嚴重性 | 說明 |
|---------|--------|------|
| `no-resource-limits` | ERROR | Container 未設定 CPU/Memory limits |
| `no-resource-requests` | WARNING | Container 未設定 resource requests |
| `privileged-container` | ERROR | Container 以 privileged mode 運行 |
| `run-as-root` | ERROR | Container 可能以 root 運行 |
| `no-liveness-probe` | WARNING | 未設定 livenessProbe |
| `no-readiness-probe` | WARNING | 未設定 readinessProbe |
| `latest-image-tag` | WARNING | 使用 latest tag |
| `ingress-nginx-deprecation` | ERROR | 使用即將淘汰的 ingress-nginx |

---

## 附錄 B: API Endpoints 總覽

| Method | Path | 描述 |
|--------|------|------|
| GET | `/` | 健康檢查 |
| GET | `/api/v1/cluster/status` | 叢集連線狀態 |
| GET | `/api/v1/cluster/pods` | 列出所有 Pod |
| POST | `/api/v1/diagnose/{pod_name}` | AI 診斷 Pod |
| GET | `/api/v1/diagnose/history` | 查詢診斷歷史 |
| POST | `/api/v1/yaml/scan` | YAML 掃描 |
| POST | `/api/v1/yaml/diff` | YAML Diff |

---

*Document End*
