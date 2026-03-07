# 🦞 Lobster K8s Copilot - PRD [DRAFT - 待展開]

> ⚠️ 這是老闆提供的產品需求草稿，請以此為核心展開完整 PRD。
> 現有程式碼可能與新需求不符，請重新評估。

## 產品期望

K8s Copilot — 智能 Kubernetes 運維助手

痛點：K8s YAML 設定容易出錯（缺 resource limits、權限過大、probe 未設），Pod 故障排查耗時，多環境設定容易飄移。

目標用戶：DevOps / SRE / 後端工程師

核心功能：
1. YAML 掃描器 — 自動偵測 anti-pattern（安全、效能、可靠性），部署前攔截
2. AI 故障診斷 — 分析 CrashLoopBackOff / OOM / ImagePullBackOff，給出根因 + 修復建議
3. 多環境 Diff — 比對 dev/staging/prod YAML 差異，標出潛在風險
4. 診斷歷史 — 記錄過去的診斷結果，支援搜尋回顧
5. Dashboard — 即時顯示叢集 Pod 狀態、告警、掃描結果

技術：Python FastAPI + React，支援 Ollama 本地模型 + OpenAI/Gemini 雲端 fallback，Docker Compose 部署

風格：深色主題為主，科技感，適合終端機使用者

---

請根據以上需求，撰寫完整的 PRD（含功能規格、使用者故事、非功能需求、技術限制、成功指標）。
