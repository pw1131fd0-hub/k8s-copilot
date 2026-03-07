# 🦞 Lobster K8s Copilot - 產品需求文件 (PRD)

## 1. 專案概述 (Project Overview)
Lobster K8s Copilot 是一款專為開發者與 SRE 打造的 Kubernetes 智能輔助工具。透過 AI 技術簡化 K8s YAML 的編寫與維護，並提供自動化的故障診斷與修復建議。

- **專案名稱**：Lobster K8s Copilot
- **專案狀態**：開發中 (MVP 階段)
- **目標用戶**：DevOps 工程師、SRE、K8s 開發者。

## 2. 產品願景 (Product Vision)
讓 Kubernetes 管理變得像聊天一樣簡單。透過 AI 賦能，降低 K8s 的學習曲線，並顯著提升故障排查的效率 (MTTR)。

## 3. 核心功能需求 (Functional Requirements)

### 3.1 YAML 智能管理 (YAML Master)
- **FR-1.1 反模式偵測 (Anti-pattern Detection)**：自動掃描 YAML 文件中的安全性 (如 Privileged Container) 與最佳實踐問題 (如缺少 Resource Limits)。
- **FR-1.2 部署預檢驗 (Pre-flight Check)**：在 `kubectl apply` 之前，模擬對 K8s 集群的影響，預測可能的崩潰。
- **FR-1.3 差異對比 (Diffing)**：跨環境 (Dev/Staging/Prod) 進行 YAML 配置對比。

### 3.2 AI 故障診斷 (AI Diagnoser)
- **FR-2.1 自動日誌抓取 (Auto-log Fetching)**：當 Pod 進入異常狀態 (CrashLoopBackOff, Pending, Error) 時，自動抓取 `logs` 與 `describe` 資訊。
- **FR-2.2 根因診斷 (Root Cause Analysis)**：將異常上下文傳送至 LLM，產出結構化的故障原因分析報告。
- **FR-2.3 修復建議 (Remediation)**：提供具體的 kubectl 指令或 YAML 修改建議，供用戶一鍵執行。

## 4. 非功能需求 (Non-Functional Requirements)
- **效能**：AI 診斷響應時間應在 10 秒內。
- **安全性**：不應將用戶敏感的 Secret 或 ConfigMap 內容傳送至外部 LLM (需過濾敏感資訊)。
- **易用性**：提供視覺化 Dashboard 監控叢集健康度。

## 5. 技術約束 (Constraints)
- **後端**：FastAPI 提供 API，Go (client-go) 負責 K8s 原生通訊。
- **前端**：React + Tailwind CSS 打造現代化介面。
- **AI**：支援 OpenAI (線上)、Gemini (線上) 與 Ollama (本地部署)。

## 6. 使用者流程 (User Journey)
1. 用戶開啟 Lobster Dashboard。
2. 系統顯示當前 K8s 叢集警告/錯誤。
3. 用戶點擊「Diagnose」按鈕。
4. 系統背景收集資訊並顯示 AI 診斷報告。
5. 用戶根據建議執行修復。

## 7. 成功指標 (Success Metrics)
- 縮短 50% 以上的常見 Pod 故障診斷時間。
- YAML 掃描發現率達 90% 以上。

---
*文件建立日期：2026-03-06*
*撰寫者：Senior PM (Lobster Team)*
