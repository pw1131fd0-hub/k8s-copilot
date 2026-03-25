# 🦞 Lobster K8s Copilot - 產品需求文件 (PRD)

> **文件版本**: 1.0.0  
> **最後更新**: 2026-03-07  
> **狀態**: ✅ APPROVED

---

## 1. 產品願景與核心痛點 (Why)

### 1.1 產品願景

**Lobster K8s Copilot** 是一款智能 Kubernetes 運維助手，旨在透過 AI 技術降低 K8s 配置錯誤、加速故障診斷，並確保多環境配置一致性。我們的願景是讓 DevOps 團隊從繁瑣的 YAML 審查與故障排查中解放，專注於更高價值的架構設計與優化工作。

### 1.2 核心痛點

| 痛點 | 現狀 | 影響 |
|------|------|------|
| **YAML 配置錯誤** | K8s YAML 設定容易出錯（缺 resource limits、權限過大、probe 未設） | 導致生產環境 Pod 崩潰、資源爭搶、安全漏洞 |
| **故障排查耗時** | Pod 出現 CrashLoopBackOff、OOM、ImagePullBackOff 等錯誤時，需手動查閱日誌、事件、配置 | 平均故障恢復時間 (MTTR) 長達 30-60 分鐘 |
| **多環境配置飄移** | Dev/Staging/Prod 的 YAML 配置隨時間產生差異，難以追蹤 | 部署到生產環境時出現非預期行為 |
| **知識傳承困難** | 故障診斷經驗存在工程師腦中，新人無法快速學習 | 團隊依賴特定人員，造成單點故障風險 |

---

## 2. 目標用戶畫像與使用場景

### 2.1 目標用戶

| 角色 | 特徵 | 核心需求 |
|------|------|----------|
| **DevOps 工程師** | 負責 CI/CD 流程、K8s 叢集維運，每日部署 5-20 次 | 快速驗證 YAML、減少部署失敗率 |
| **SRE (Site Reliability Engineer)** | 負責生產環境穩定性、On-call 輪值 | 快速定位根因、縮短 MTTR |
| **後端工程師** | 需自行撰寫 K8s 配置、但對 K8s 最佳實踐不熟悉 | 獲得即時反饋、學習正確配置方式 |

### 2.2 使用者故事 (User Stories)

#### US-01: YAML 掃描與部署攔截
> **作為** DevOps 工程師  
> **我想要** 在部署前自動掃描 YAML 配置  
> **以便** 攔截缺少 resource limits、未設定 health probe、使用 root 權限等 anti-pattern  

**驗收標準**:
- [ ] 上傳 YAML 後 3 秒內返回掃描結果
- [ ] 標示問題嚴重度 (ERROR/WARNING/INFO)
- [ ] 顯示問題所在行號與修復建議
- [ ] 支援單檔案及多文件 YAML (用 `---` 分隔)

#### US-02: AI 故障診斷
> **作為** SRE  
> **我想要** 點擊異常 Pod 後獲得 AI 診斷分析  
> **以便** 快速了解 CrashLoopBackOff / OOM / ImagePullBackOff 的根因與修復方式

**驗收標準**:
- [ ] 自動識別錯誤類型
- [ ] 提供根因分析 (Root Cause Analysis)
- [ ] 提供具體修復步驟 (Remediation)
- [ ] 顯示使用的 AI 模型與信心度
- [ ] 診斷結果自動存入歷史記錄

#### US-03: 多環境 YAML Diff
> **作為** DevOps 工程師  
> **我想要** 比對 dev/staging/prod 環境的 YAML 差異  
> **以便** 識別潛在的配置飄移風險

**驗收標準**:
- [ ] 並排顯示兩份 YAML 的差異
- [ ] 高亮顯示新增、刪除、修改的行
- [ ] 標註潛在風險 (如 prod 缺少 replicas、resource limits 不一致)
- [ ] 支援複製差異片段

#### US-04: 診斷歷史查詢
> **作為** 新加入團隊的後端工程師  
> **我想要** 搜尋過去的診斷記錄  
> **以便** 學習常見問題的解決方式

**驗收標準**:
- [ ] 依 Pod 名稱、Namespace、錯誤類型篩選
- [ ] 依時間排序
- [ ] 點擊展開完整診斷內容
- [ ] 支援關鍵字全文搜尋

#### US-05: 即時叢集 Dashboard
> **作為** SRE  
> **我想要** 看到叢集 Pod 狀態總覽  
> **以便** 快速識別異常並採取行動

**驗收標準**:
- [ ] 顯示叢集連線狀態
- [ ] 統計 Total Pods / Healthy / Unhealthy 數量
- [ ] 顯示 K8s 叢集版本
- [ ] 自動刷新 (預設 30 秒) 或手動刷新
- [ ] 異常 Pod 以紅色高亮

---

## 3. 功能需求清單

### 3.1 P0 (MVP 必備功能)

| 功能 | 描述 | 驗收標準 |
|------|------|----------|
| **YAML 掃描器** | 偵測 anti-pattern (安全、效能、可靠性) | 覆蓋 15+ 條規則，3 秒內返回結果 |
| **AI 故障診斷** | 分析 CrashLoopBackOff / OOM / ImagePullBackOff | 準確率 > 80%，回應時間 < 10 秒 |
| **Pod 狀態列表** | 顯示所有 Pod 及其狀態 | 支援 Namespace 篩選、狀態篩選 |
| **診斷歷史** | 儲存與查詢過往診斷結果 | 支援分頁、搜尋、時間排序 |
| **多 AI 模型支援** | Ollama 本地 + OpenAI/Gemini 雲端 fallback | 自動 fallback 機制 |

### 3.2 P1 (重要功能)

| 功能 | 描述 | 驗收標準 |
|------|------|----------|
| **多環境 Diff** | 比對兩份 YAML 配置差異 | 高亮差異行、標註風險 |
| **YAML AI 建議** | 掃描後由 AI 提供改進建議 | 整合於掃描結果中 |
| **深色主題 UI** | 科技感深色介面 | 符合設計規範、支援主題切換 |
| **叢集狀態儀表板** | 統計數據、連線狀態、版本資訊 | 自動刷新、響應式設計 |

### 3.3 P2 (未來迭代)

| 功能 | 描述 |
|------|------|
| **Webhook 整合** | 接收 K8s Admission Webhook，部署前自動攔截 |
| **Slack/Teams 通知** | 診斷結果推送到團隊協作工具 |
| **多叢集支援** | 同時管理多個 K8s 叢集 |
| **RBAC 權限管理** | 細粒度存取控制 |
| **自訂掃描規則** | 使用者可新增/修改掃描規則 |

---

## 4. 非功能需求 (NFR)

### 4.1 效能

| 指標 | 目標值 |
|------|--------|
| YAML 掃描回應時間 | ≤ 3 秒 (單檔 100KB 以內) |
| AI 診斷回應時間 | ≤ 10 秒 (使用雲端模型) |
| 首頁載入時間 | ≤ 2 秒 (LCP) |
| API 並發處理量 | ≥ 50 req/s |
| 資料庫查詢效能 | ≤ 100ms (歷史記錄查詢) |

### 4.2 安全性

| 需求 | 說明 |
|------|------|
| API 輸入驗證 | 所有請求參數進行 schema 驗證、長度限制 |
| YAML 大小限制 | 單檔上限 512KB，防止 DoS |
| K8s 名稱驗證 | Namespace/Pod 名稱符合 DNS-subdomain 規範 |
| 敏感資料處理 | API Key 不記錄於日誌，不顯示於前端 |
| 依賴安全 | 無 CRITICAL/HIGH 等級漏洞 |
| OWASP Top 10 | 合規 (已通過 Security Audit) |

### 4.3 可用性

| 指標 | 目標值 |
|------|--------|
| 可用性 SLA | 99.5% (月度) |
| 錯誤容忍 | AI 模型不可用時自動 fallback |
| 優雅降級 | 叢集斷線時仍可使用 YAML 掃描/Diff 功能 |

### 4.4 擴展性

| 需求 | 說明 |
|------|------|
| 水平擴展 | 後端無狀態，可透過 Docker Compose scale 或 K8s HPA |
| 模組化架構 | AI 引擎獨立服務，可替換模型 |
| 資料庫遷移 | 使用 Alembic 管理 schema 變更 |

---

## 5. 技術選型與限制

### 5.1 技術棧

| 層級 | 技術 | 選型理由 |
|------|------|----------|
| **後端框架** | Python FastAPI | 非同步高效能、自動 OpenAPI 文件 |
| **前端框架** | React + Tailwind CSS | 元件化開發、快速 UI 迭代 |
| **AI 引擎** | Ollama (本地) + OpenAI/Gemini (雲端) | 靈活部署、成本控制 |
| **資料庫** | SQLite (開發) / PostgreSQL (生產) | 輕量開發、生產可擴展 |
| **ORM** | SQLAlchemy + Alembic | 類型安全、版本化遷移 |
| **部署** | Docker Compose | 簡化多服務編排 |
| **容器** | Docker | 環境一致性 |

### 5.2 技術限制

| 限制 | 說明 |
|------|------|
| K8s 版本 | 支援 1.24+ (CoreV1 API) |
| 瀏覽器支援 | Chrome/Firefox/Edge 最新兩個版本 |
| YAML 大小 | 單檔上限 512KB |
| 本地 AI | 需 Ollama 服務運行於 `localhost:11434` |

---

## 6. 競品分析

| 工具 | 優勢 | 劣勢 | Lobster 差異化 |
|------|------|------|----------------|
| **kube-linter** | 成熟的靜態分析、CLI 整合 | 無 AI、無 Web UI | AI 診斷 + Web Dashboard |
| **Polaris** | 豐富的最佳實踐規則 | 無故障診斷、無歷史記錄 | 故障診斷 + 診斷歷史 |
| **K9s** | 強大的終端機 UI | 無 YAML 掃描、無 AI 功能 | YAML 掃描 + AI 建議 |
| **Datree** | 雲端政策管理 | 付費功能多、需聯網 | 本地 Ollama 支援、開源 |

---

## 7. MVP 範圍與迭代路線圖

### 7.1 MVP (v1.0) 範圍

✅ 已實作功能:
- Pod 狀態列表 (Namespace 篩選)
- AI 故障診斷 (CrashLoopBackOff / OOM / ImagePullBackOff)
- YAML 掃描器 (15+ 規則)
- 多環境 YAML Diff
- 診斷歷史 (儲存、查詢、搜尋)
- 多 AI 模型支援 (Ollama / OpenAI / Gemini)

### 7.2 迭代路線圖

| 版本 | 時程 | 主要功能 |
|------|------|----------|
| **v1.1** | +2 週 | 深色主題 UI、RWD 優化 |
| **v1.2** | +4 週 | Webhook 整合、CI/CD 攔截 |
| **v2.0** | +8 週 | 多叢集支援、RBAC |
| **v2.1** | +12 週 | Slack/Teams 整合、自訂規則 |

---

## 8. UI/UX 設計規範

### 8.1 色彩計畫 (深色主題)

| 用途 | 名稱 | Hex Code | 說明 |
|------|------|----------|------|
| **主色** | Lobster Red | `#E85D4C` | 品牌識別、主要按鈕、重點強調 |
| **輔色** | Ocean Blue | `#3B82F6` | 連結、資訊提示、hover 狀態 |
| **成功色** | Terminal Green | `#22C55E` | 成功狀態、健康 Pod、通過檢查 |
| **警告色** | Amber | `#F59E0B` | WARNING 級別、需注意事項 |
| **錯誤色** | Error Red | `#EF4444` | ERROR 級別、異常 Pod、失敗狀態 |
| **背景主色** | Dark Slate | `#0F172A` | 頁面主背景 (Slate 900) |
| **背景次色** | Card Background | `#1E293B` | 卡片、面板背景 (Slate 800) |
| **邊框色** | Border | `#334155` | 分隔線、邊框 (Slate 700) |
| **文字主色** | Text Primary | `#F1F5F9` | 主要文字 (Slate 100) |
| **文字次色** | Text Secondary | `#94A3B8` | 次要文字、說明 (Slate 400) |
| **文字禁用** | Text Disabled | `#64748B` | 禁用狀態文字 (Slate 500) |

### 8.2 字型選擇

| 用途 | 字型 | Fallback |
|------|------|----------|
| **介面文字** | Inter | system-ui, sans-serif |
| **程式碼/YAML** | JetBrains Mono | Fira Code, monospace |

### 8.3 元件風格

| 屬性 | 值 | 說明 |
|------|-----|------|
| **圓角** | `8px` (md) / `12px` (lg) | 現代感但不過於圓潤 |
| **陰影** | `shadow-lg` (深色環境用微光) | `0 0 15px rgba(232, 93, 76, 0.1)` |
| **間距基準** | 4px grid | 間距為 4 的倍數 (8, 12, 16, 24, 32) |
| **動畫時長** | 150ms (快) / 300ms (標準) | transition-all |

### 8.4 RWD 斷點

| 斷點名稱 | 寬度 | 說明 |
|----------|------|------|
| **sm** | ≥ 640px | 大型手機 |
| **md** | ≥ 768px | 平板 |
| **lg** | ≥ 1024px | 筆電 |
| **xl** | ≥ 1280px | 桌機 |
| **2xl** | ≥ 1536px | 大螢幕 |

### 8.5 深色/淺色模式

- **預設**: 深色模式 (符合終端機使用者習慣)
- **切換**: 右上角提供主題切換按鈕 (月亮/太陽圖示)
- **持久化**: 使用 localStorage 記住用戶偏好

---

## 9. 成功指標 (KPIs)

### 9.1 產品指標

| 指標 | 目標值 | 量測方式 |
|------|--------|----------|
| 部署失敗率降低 | ≥ 30% | 使用前後 CI/CD 失敗率比較 |
| MTTR 縮短 | ≥ 40% | 故障處理時間追蹤 |
| 用戶滿意度 | ≥ 4.0/5.0 | 內建問卷調查 |

### 9.2 技術指標

| 指標 | 目標值 | 量測方式 |
|------|--------|----------|
| API 可用性 | ≥ 99.5% | Uptime 監控 |
| 測試覆蓋率 | ≥ 80% | pytest-cov / Jest coverage |
| 安全漏洞 | 0 CRITICAL/HIGH | Bandit / npm audit |
| 效能達標率 | 100% | 所有 NFR 指標通過 |

---

## 10. 現有程式碼評估與重構需求

### 10.1 符合新 PRD 的部分 ✅

- ✅ FastAPI 後端架構 (模組化、RESTful API)
- ✅ YAML 掃描器功能完整
- ✅ AI 故障診斷 (Ollama/OpenAI/Gemini 三引擎)
- ✅ 診斷歷史儲存與查詢
- ✅ 多環境 YAML Diff
- ✅ Pod 狀態列表
- ✅ 安全審計通過 (OWASP Top 10 合規)

### 10.2 需要重構的部分 ⚠️

| 項目 | 現狀 | 目標 | 優先級 |
|------|------|------|--------|
| **UI 主題** | 淺色主題 (bg-slate-50, bg-white) | 深色主題為主 (bg-slate-900) | P1 |
| **字型** | 系統預設 | Inter + JetBrains Mono | P1 |
| **色彩系統** | 無統一規範 | 套用設計規範色彩 | P1 |
| **主題切換** | 無 | 深色/淺色切換功能 | P1 |
| **RWD 優化** | 基本響應式 | 完整斷點測試 | P2 |

### 10.3 重構計畫

重構工作已納入 v1.1 迭代，預估工時 2 週：
1. **Phase 1** (3 天): Tailwind 配置更新、全域色彩變數
2. **Phase 2** (4 天): 所有元件深色主題化
3. **Phase 3** (2 天): 主題切換功能
4. **Phase 4** (1 天): 測試與修正

---

## 附錄 A: YAML 掃描規則清單

| 規則 ID | 分類 | 嚴重度 | 說明 |
|---------|------|--------|------|
| SEC-001 | Security | ERROR | Container 使用 root 權限 |
| SEC-002 | Security | ERROR | 缺少 securityContext |
| SEC-003 | Security | WARNING | 使用 privileged: true |
| SEC-004 | Security | WARNING | 掛載敏感路徑 (/etc, /var/run) |
| PERF-001 | Performance | ERROR | 缺少 resources.limits |
| PERF-002 | Performance | ERROR | 缺少 resources.requests |
| PERF-003 | Performance | WARNING | CPU/Memory limit 過高 |
| REL-001 | Reliability | ERROR | 缺少 livenessProbe |
| REL-002 | Reliability | ERROR | 缺少 readinessProbe |
| REL-003 | Reliability | WARNING | replicas < 2 |
| REL-004 | Reliability | WARNING | 缺少 PodDisruptionBudget |
| IMG-001 | Image | ERROR | 使用 :latest tag |
| IMG-002 | Image | WARNING | 缺少 imagePullPolicy |
| NET-001 | Network | WARNING | 缺少 NetworkPolicy |
| CONF-001 | Config | INFO | 缺少 annotations |
| CONF-002 | Config | INFO | 缺少 labels |

---

## 附錄 B: 詞彙表

| 術語 | 定義 |
|------|------|
| **Anti-pattern** | 常見但不建議的配置方式 |
| **CrashLoopBackOff** | Pod 反覆崩潰重啟的狀態 |
| **OOM (Out of Memory)** | 記憶體不足導致 Pod 被終止 |
| **ImagePullBackOff** | 無法拉取容器映像的狀態 |
| **MTTR** | Mean Time To Recovery，平均故障恢復時間 |
| **Fallback** | 主要服務不可用時的備援機制 |

---

*Document End*
