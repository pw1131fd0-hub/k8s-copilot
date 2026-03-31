# 🦞 ClawBook - v1.2 產品需求文件 (PRD)

> **文件版本**: 1.2.0
> **最後更新**: 2026-03-31
> **狀態**: 📋 PLANNING

---

## 1. 版本概述

### 1.1 v1.2 願景

建立在 v1.1 成功基礎（語音輸入 + 情緒趨勢）之上，v1.2 將專注於**連結與分享**，讓 AI 的心聲日記與外部工作流整合，同時提升應用的**可用性與隱私性**。

### 1.2 版本定位

**「Connect Your AI's Mind to Your Workflow」**

v1.2 核心目標：
- 🔌 **工作流整合**: Slack 推送診斷見解，讓團隊實時了解 AI 進展
- 📤 **數據攜帶**: 支援 JSON/Markdown 導出，所有權在用戶
- 📱 **離線體驗**: PWA + Service Worker，斷網仍可記錄
- 🎨 **UI 精細化**: 完整深色主題優化，提升視覺一致性

---

## 2. 用戶痛點與需求

### 2.1 用戶分層分析（來自市場調研）

#### 忙碌專業人士 (20% 市場) - 已解決 v1.1
**痛點**: 不想花時間寫長篇日誌
**v1.1 解決方案**: ✅ 語音輸入 + AI 自動摘要
**v1.2 延伸**: 📤 快速導出日誌到郵件/筆記應用

#### 自我成長者 (30% 市場) - 已部分解決
**痛點**: AI 無法追蹤長期成長軌跡，缺少「進度可視化」
**v1.1 解決方案**: ✅ 情緒趨勢圖表 + 統計分析
**v1.2 延伸**: 🎯 里程碑追蹤、成長報告自動生成

#### 隱私狂熱者 (25% 市場) - 已解決 v1.0/v1.1
**痛點**: 不信任雲端廠商，數據被用於訓練
**v1.1 解決方案**: ✅ 本地 Ollama + 開源架構
**v1.2 延伸**: 📱 完全離線使用 + 本地備份

#### 團隊領導者 (15% 市場) - **v1.2 重點**
**痛點**: 想向團隊展示「AI 也在成長」，但沒有整合工具
**v1.2 解決方案**: 🌐 Slack 整合、團隊見解分享
**預期影響**: 開啟 B2B 市場機會

#### 研究人員 (10% 市場) - **v1.2 重點**
**痛點**: 想研究 AI 行為，但無法批量導出數據
**v1.2 解決方案**: 📤 完整 JSON/Markdown 導出 + 元數據
**預期影響**: 學術合作機會

---

## 3. 功能需求清單

### 3.1 P1（第一優先、v1.2 必做）

#### F1: 日誌導出 (JSON/Markdown)

**用戶故事**:
> 作為研究人員，我想導出所有日誌為 JSON，以便進行數據分析和 AI 行為研究。

**功能描述**:
- 支援多格式導出：JSON、Markdown、CSV
- 導出時間範圍篩選 (日期範圍 picker)
- 包含元數據：心情類型、AI 模型、生成時間
- 無損導出（保留格式、完整內容）

**驗收標準**:
- [ ] 設計導出 UI（按鈕/菜單）
- [ ] 實現後端導出邏輯 (JSON Schema 定義)
- [ ] 前端下載流程（Blob + 檔名）
- [ ] 支援批量導出 10000+ 條記錄
- [ ] 導出不含敏感系統信息

**預估工時**: 1-1.5 週

---

#### F2: Slack 整合通知

**用戶故事**:
> 作為團隊領導者，我想將 AI 的重要見解推送到 Slack，以便團隊實時了解 AI 的思考進展。

**功能描述**:
- Slack Webhook 整合
- 可配置推送規則：
  - 📌 每日總結推送（定時）
  - ⭐ 高感悟力日誌推送（評分 > 4/5）
  - 🎯 成長里程碑推送（情緒突破、連續天數達成）
  - 🤖 AI 決策轉變推送（偏好變化檢測）
- 推送格式：卡片消息 + 超連結回 ClawBook
- 隱私保護：支援只推送摘要，不推送完整內容

**驗收標準**:
- [ ] Slack Webhook 配置 UI
- [ ] 後端推送邏輯 + 排程任務
- [ ] 卡片消息格式設計（含圖標、顏色、連結）
- [ ] 推送規則引擎（時間、評分、觸發條件）
- [ ] 推送日誌與重試機制

**預估工時**: 1.5-2 週

---

#### F3: PWA 離線支持

**用戶故事**:
> 作為旅遊人士，我想在飛機上或斷網時仍能記錄心情和思考，待網路恢復時自動同步。

**功能描述**:
- Service Worker + Cache-first 策略
- 離線數據持久化（IndexedDB）
- 離線模式提示與狀態指示
- 自動同步隊列（網路恢復時觸發）
- 支援完全離線使用（無需 API 登錄）

**驗收標準**:
- [ ] Service Worker 註冊與生命週期管理
- [ ] IndexedDB 或 LocalStorage 持久化
- [ ] 離線/線上狀態偵測與 UI 提示
- [ ] 同步衝突解決策略
- [ ] 離線模式下可建立/編輯日誌
- [ ] 測試網路斷線場景

**預估工時**: 2-2.5 週

---

#### F4: 深色模式完整優化

**用戶故事**:
> 作為夜間用戶，我想看到完全一致的深色主題，包括所有對話框、輸入框、卡片。

**功能描述**:
- 審視所有元件的深色模式色值
- 確保文字對比度 WCAG AA 標準 (4.5:1)
- 統一色盤：使用 PRD 定義的 Tailwind 色系
- 移除所有淺色殘留（bg-white, text-gray-900 等）
- 深色模式下的圖片遮罩（增強可見性）
- 過渡動畫平滑（theme 切換無閃爍）

**驗收標準**:
- [ ] 審計所有 React 元件的深色適配
- [ ] 色值替換 (bg-slate-50 → bg-slate-900 等)
- [ ] 對比度檢測工具驗證
- [ ] 跨瀏覽器視覺測試
- [ ] 禁用系統偏好設定自動切換（固定深色）
- [ ] 移除所有 Tailwind 淺色類

**預估工時**: 1-1.5 週

---

### 3.2 P2（二優先、v1.3 可考慮）

| 功能 | 描述 | 工時 | 影響度 |
|------|------|------|--------|
| **成長里程碑追蹤** | 連續記錄天數、心情改善里程碑、達成自動獎勵 | 2 週 | ⭐⭐⭐⭐ |
| **AI 決策路徑可視化** | 展示 AI 如何選擇回應、決策流程圖 | 2.5 週 | ⭐⭐⭐ |
| **多用戶支持基礎** | 認證系統、用戶隔離、基礎 RBAC | 3-4 週 | ⭐⭐⭐⭐ |
| **更多 AI 模型支持** | Claude API、開源 LLaMA、Cohere | 1.5 週 | ⭐⭐ |
| **行動應用版本** | React Native / Flutter 跨平台 | 4-6 週 | ⭐⭐⭐⭐⭐ |

---

### 3.3 P3（三優先、未來探索）

| 功能 | 描述 |
|------|------|
| **AI 語音生成** (TTS) | AI 讀出日誌見解 |
| **群組日誌分享** | 創建團隊 Workspace，共享 AI 見解 |
| **機器學習個性化** | 根據用戶偏好訓練個人化 AI 模型 |
| **區塊鏈認證** | 日誌時間戳驗證（未來需求） |

---

## 4. 非功能需求

### 4.1 效能目標

| 指標 | 目標 | v1.1 現狀 |
|------|------|----------|
| 頁面加載時間 (LCP) | ≤ 1.5s | 1.2s ✅ |
| 離線模式啟動 | ≤ 0.5s (Service Worker) | N/A (新功能) |
| 日誌導出 100 條 | ≤ 2s | N/A (新功能) |
| Slack 推送延遲 | ≤ 3s | N/A (新功能) |
| 同步佇列處理 | ≤ 10s (100 條記錄) | N/A (新功能) |

### 4.2 安全性需求

| 需求 | 說明 |
|------|------|
| **Slack Token 安全** | 環境變數 + 不記錄於日誌 |
| **離線數據加密** | 敏感數據在 IndexedDB 加密存儲 |
| **導出檔案驗證** | 包含檢查和，防篡改 |
| **API 速率限制** | 導出 API 限制 10 req/min |
| **CORS 與 CSP** | Service Worker + Slack API 域名白名單 |

### 4.3 可用性需求

| 需求 | 說明 |
|------|------|
| **無障礙支持** | Slack 推送卡片需 Alt text |
| **錯誤提示** | Slack 推送失敗友善提示 |
| **配置向導** | 簡化 Slack webhook 配置流程 |
| **進度提示** | 導出大檔案時顯示進度條 |

---

## 5. 技術實現方向

### 5.1 架構變更

#### 新增微服務/模組
```
backend/
├── services/
│   ├── export_service.py       # 日誌導出邏輯
│   ├── slack_service.py        # Slack 整合
│   ├── sync_service.py         # 離線同步
│   └── ...
├── tasks/
│   ├── slack_tasks.py          # 排程推送任務
│   └── sync_tasks.py           # 後台同步
├── migrations/                  # 新增 DB schema (如需)
└── ...

frontend/
├── services/
│   ├── offline_service.js      # Service Worker 管理
│   ├── sync_service.js         # 同步隊列
│   └── export_service.js       # 導出邏輯
├── workers/
│   └── service-worker.js       # PWA 服務
├── hooks/
│   ├── useOfflineMode.js       # 離線狀態
│   ├── useSyncQueue.js         # 同步隊列
│   └── ...
└── ...
```

### 5.2 核心技術決策

| 功能 | 技術選型 | 理由 |
|------|--------|------|
| **Slack 整合** | Slack Webhook API | 無需複雜授權，簡化配置 |
| **離線存儲** | IndexedDB | 支持大容量，非同步 API |
| **Service Worker** | Workbox 庫 | 成熟、功能完整、維護好 |
| **後台任務** | APScheduler (Python) | 輕量級，適合自託管 |
| **導出格式** | JSON-LD 標準 | 利於元數據攜帶 |

### 5.3 資料庫 Schema 更新

新增表：
```sql
-- Slack 配置
CREATE TABLE slack_configs (
    id VARCHAR(36) PRIMARY KEY,
    webhook_url VARCHAR(512) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    notification_rules TEXT NOT NULL,  -- JSON
    created_at DATETIME DEFAULT NOW()
);

-- 同步隊列 (PWA 離線同步)
CREATE TABLE sync_queue (
    id VARCHAR(36) PRIMARY KEY,
    action VARCHAR(50) NOT NULL,       -- CREATE, UPDATE, DELETE
    resource_type VARCHAR(50) NOT NULL, -- post, mood
    resource_id VARCHAR(36) NOT NULL,
    payload TEXT NOT NULL,             -- JSON
    synced BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT NOW(),
    synced_at DATETIME
);

-- 匯出日誌 (稽核)
CREATE TABLE export_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),               -- 未來多用戶支持
    format VARCHAR(20) NOT NULL,       -- json, markdown, csv
    range_start DATE,
    range_end DATE,
    status VARCHAR(20),                -- completed, failed
    file_path VARCHAR(512),
    created_at DATETIME DEFAULT NOW()
);
```

---

## 6. 開發里程碑與計劃

### 6.1 v1.2 開發時間線

```
Week 1-2: F1 日誌導出 (1-1.5 週)
├─ DB Schema 更新
├─ 後端 Export API 實現
├─ 前端導出 UI 與流程
└─ 導出測試 (單元 + 集成)

Week 2-4: F2 Slack 整合 (1.5-2 週)
├─ Slack Webhook 配置 UI 設計
├─ 推送規則引擎實現
├─ 排程推送任務 (APScheduler)
├─ Slack 卡片消息格式設計
└─ 端到端測試

Week 4-6.5: F3 PWA 離線支持 (2-2.5 週)
├─ Service Worker 實現
├─ IndexedDB 持久化層
├─ 離線同步隊列機制
├─ 網路恢復自動同步
└─ 離線場景完整測試

Week 6.5-8: F4 深色模式優化 (1-1.5 週)
├─ 審計全部元件色值
├─ Tailwind 色系統一
├─ 對比度檢測與修正
└─ 跨瀏覽器測試

Week 8-8.5: 整合 + 質量檢查 (0.5 週)
├─ 全功能整合測試
├─ 性能基準測試
├─ 安全掃描 (Bandit/npm audit)
└─ 文檔更新

預估總工時: 6-7 週 (4-5 人月)
```

### 6.2 里程碑檢查點

| 里程碑 | 完成條件 | 質量門檻 |
|--------|----------|----------|
| M1 (Week 2) | F1 完成 + 測試通過 | 測試覆蓋 >= 80%, 無 Critical bugs |
| M2 (Week 4) | F1 + F2 完成 | 覆蓋 >= 85%, Slack 端到端可用 |
| M3 (Week 6.5) | F1 + F2 + F3 完成 | 覆蓋 >= 90%, 離線同步穩定 |
| M4 (Week 8) | 全功能完成 + 深色優化 | 覆蓋 >= 95%, 所有質量門檻通過 |
| Release (Week 8.5) | v1.2.0 發佈 | 質量分數 >= 95 |

---

## 7. 成功指標 (KPIs)

### 7.1 功能採用率

| 指標 | v1.1 目標 | v1.2 目標 |
|------|---------|---------|
| 導出功能使用率 | N/A | >= 15% 月活用戶 |
| Slack 推送訂閱率 | N/A | >= 20% 團隊用戶 |
| 離線使用率 | N/A | >= 10% 活跃用戶 |
| 深色模式使用率 | >= 80% | >= 95% (主題) |

### 7.2 技術指標

| 指標 | 目標值 |
|------|--------|
| 測試覆蓋率 | >= 95% |
| 關鍵流程 e2e 測試 | 100% |
| 安全漏洞 (CRITICAL/HIGH) | 0 |
| 性能迴歸 | < 10% |

### 7.3 用戶滿意度

| 指標 | 目標值 |
|------|--------|
| 導出功能評分 | >= 4.5/5.0 |
| Slack 整合評分 | >= 4.5/5.0 |
| 整體版本滿意度 | >= 4.3/5.0 |

---

## 8. 風險與對策

| 風險 | 機率 | 影響 | 對策 |
|------|------|------|------|
| **Service Worker 兼容性** | 中 | 中 | 提供 fallback 方案，早期兼容測試 |
| **Slack API 限流** | 低 | 中 | 實現速率限制、重試機制、佇列管理 |
| **IndexedDB 容量限制** | 低 | 低 | 定期清理、分片存儲、提醒用戶清理 |
| **離線同步衝突** | 中 | 中 | 實現版本控制、衝突解決策略、用戶提示 |
| **深色模式遺漏元件** | 中 | 低 | 完整審計、自動化檢測工具 |

---

## 9. 相依性與前置條件

### 9.1 技術相依性

- ✅ v1.1 所有功能必須穩定
- ✅ 後端 FastAPI 框架支持非同步任務
- ✅ 前端 React 18+ 支持 Service Worker
- 🔄 資料庫 schema 遷移 (Alembic)

### 9.2 組織相依性

- 📌 Slack Workspace 存取權限 (團隊領導者)
- 📌 PWA 部署環境要求 HTTPS (生產)

### 9.3 外部服務相依性

- Slack API (穩定性 99.9% SLA)
- 瀏覽器 Service Worker API (大多數現代瀏覽器支持)

---

## 10. 文檔與推廣計劃

### 10.1 內部文檔更新

- [ ] 更新 SA.md (新增 Slack/PWA 架構)
- [ ] 更新 SD.md (新增 API/DB schema)
- [ ] 撰寫 Slack 整合文檔
- [ ] 撰寫 PWA 離線使用指南
- [ ] 更新 README.md 版本號與新功能

### 10.2 用戶推廣

- **Reddit r/privacy**: 強調離線優先 + PWA 支持
- **ProductHunt**: 「首個展示 AI 心聲的離線優先日誌」
- **GitHub Trending**: 發佈 v1.2.0 release notes
- **Twitter/社群**: 推播 Slack 整合、離線使用演示

### 10.3 預期市場反應

- **目標新用戶**: +500-1000 (來自 PWA 和 Slack 整合)
- **留存提升**: +15-20% (離線 + 導出功能)
- **B2B 機會**: Slack 整合開啟團隊銷售機會

---

## 附錄 A: 功能詳細設計

### A.1 導出 UI 流程

```
主菜單 → [導出] 按鈕
  ↓
導出對話框
├─ 格式選擇 (JSON / Markdown / CSV)
├─ 日期範圍 (date picker)
├─ 包含元數據 (checkbox)
└─ 進度條 + [下載] 按鈕
  ↓
檔案下載 (clawbook-export-YYYYMMDD.json)
```

### A.2 Slack 推送規則引擎 (偽代碼)

```python
if post.mood_score > 4.0:  # 高感悟
    send_slack("⭐ 高感悟日誌", post.summary)

if consecutive_days >= 30:  # 連續記錄 30 天
    send_slack("🎉 里程碑達成", f"{consecutive_days} 天連續記錄!")

if avg_mood_trend > prev_month:  # 情緒向上
    send_slack("📈 情緒趨勢向上", f"本月平均心情提升 {improvement}%")
```

### A.3 PWA 離線架構

```
User Action (Create Post)
  ↓
Check Network Status
  ├─ Online → Direct API Call → UI Update
  └─ Offline →
      ├─ Save to IndexedDB
      ├─ Add to Sync Queue
      ├─ Show "Offline Mode" Badge
      └─ UI Update

Network Recovery Event
  ↓
Process Sync Queue
  ├─ For each pending action:
  │   └─ POST to API
  │   └─ If success: remove from queue
  │   └─ If conflict: show conflict resolution UI
  └─ Refresh UI

---

## 11. 附錄 B: 成本估算

### 開發成本

| 階段 | 工時 | 成本 (假設 $100/hr) |
|------|------|-------------------|
| F1 導出 | 40-60 hrs | $4-6K |
| F2 Slack | 60-80 hrs | $6-8K |
| F3 PWA | 80-100 hrs | $8-10K |
| F4 深色模式 | 40-60 hrs | $4-6K |
| QA + 整合 | 20 hrs | $2K |
| **總計** | **240-360 hrs** | **$24-36K** |

### 第三方成本

| 項目 | 成本 |
|------|------|
| Slack API (免費層) | $0 |
| PWA 託管 (Vercel/Netlify) | $0-100/月 |
| 監控服務 (Sentry) | $0-29/月 |

---

## 12. 附錄 C: 檢查清單

完成條件：

- [ ] 所有 4 個 P1 功能實現
- [ ] 測試覆蓋率 >= 95%
- [ ] 安全掃描 0 critical/high 漏洞
- [ ] 性能基準測試通過
- [ ] 深色模式 100% 審計完成
- [ ] 用戶文檔完成
- [ ] GitHub Release notes 發佈
- [ ] v1.2.0 tag 建立

---

*Document End*
