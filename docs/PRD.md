# 🦞 Lobster K8s Copilot - 產品需求文件 (PRD) v2.0 (Migration Focused)

## 1. 專案概述 (Project Overview)
隨著 Kubernetes 生態系的演進，舊有的 `ingress-nginx` 等組件於 2026 年正式退役。Lobster K8s Copilot v2.0 旨在轉型為**「智能遷移與穩定性守護者」**。除了基礎的 YAML 掃描與診斷，更強調**「自動化遷移路徑規劃」**，幫助企業無痛過渡至 Gateway API 與現代化的雲原生架構。

- **專案名稱**：Lobster K8s Copilot
- **版本編號**：v2.0 (Migration Era)
- **更新日期**：2026-03-07
- **目標用戶**：SRE、DevOps 工程師、面臨 K8s 版本更新壓力的基礎設施團隊。

## 2. 產品願景 (Product Vision)
消除 Kubernetes 升級與組件遷移的恐懼感。透過 AI 驅動的配置分析與轉換，讓「基礎設施現代化」成為一鍵點擊的簡單任務。

## 3. 核心功能需求 (Functional Requirements)

### 3.1 遷移獵人與診斷 (Migration Hunter & Diagnoser) [NEW]
- **FR-1.1 組件退役預警 (Deprecation Early Warning)**：
  - 自動偵測即將或已退役的組件（如 `ingress-nginx`, `old API versions`）。
  - **核心場景**：識別 `ingress-nginx` 並標記為高風險 (ERROR)，預警其在 2026 年 3 月後的維護風險。
- **FR-1.2 AI 自動配置轉換 (AI Config Transformer)**：
  - 將舊版 Ingress YAML 自動轉換為 **Gateway API (Gateway & HTTPRoute)** 配置。
  - 支援 `cert-manager` 與 `external-dns` 等連動組件的配置更新建議。
- **FR-1.3 遷移影響評估 (Migration Impact Assessment)**：分析遷移過程中可能的流量中斷點，產出「零停機遷移步驟書」。

### 3.2 強化版 YAML 智能掃描 (Enhanced YAML Master)
- **FR-2.1 現代化反模式偵測**：針對 Gateway API, Service Mesh (Istio/Cilium) 的最佳實踐進行掃描。
- **FR-2.2 多維度安全檢查**：掃描不安全的 RBAC 設定與 Pod Security Admission (PSA) 違規。

### 3.3 AI 故障根因分析 (AI RCA)
- **FR-3.1 跨組件診斷**：不僅診斷 Pod，還能自動關聯 Ingress -> Service -> Pod 的流量鏈路故障。
- **FR-3.2 遷移後效能對比**：對比遷移前後的 Resource 使用率與延遲情況。

## 4. 非功能需求 (Non-Functional Requirements)
- **精準度 (Accuracy)**：YAML 轉換後的有效性需經由 AI 引擎進行二次驗證 (Self-healing)。
- **安全性**：數據處理需符合 GDPR/CCPA，嚴禁外洩集群敏感證書 (Secrets)。
- **即時性**：市場獵人每 4 小時自動同步最新的 K8s 退役與漏洞情報。

## 5. 技術架構與擴充性
- **Backend**: FastAPI (Python) + Go Worker。
- **Frontend**: React 19 + Tailwind CSS + Monaco Editor (支援即時 Diff 預覽)。
- **Data Strategy**: 使用向量資料庫 (LanceDB) 儲存 K8s 官方文檔與遷移範本，實現 RAG 增強建議。

## 6. 使用者流程 (User Journey)
1. 用戶開啟 Dashboard，系統發出「⚠️ 偵測到 3 個 ingress-nginx 實例已退役」警告。
2. 用戶點擊「Plan Migration」。
3. 系統生成對應的 Gateway API YAML 並顯示 Side-by-Side 對比。
4. 用戶點擊「Validate」，系統在沙盒環境模擬部署。
5. 用戶點擊「Execute」，完成配置更新。

## 7. 成功指標 (Success Metrics)
- 遷移配置的手動修改率降低至 20% 以下。
- 支援至少 5 種主流 K8s 退役組件的自動化遷移路徑。

---
*文件更新日期：2026-03-07*
*撰寫者：小龍蝦 (Lobster AI)*
