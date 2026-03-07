"""Prompt templates for Kubernetes pod diagnosis and YAML scanning via LLM."""
DIAGNOSE_PROMPT_TEMPLATE = """You are a Senior Kubernetes SRE Expert.

## Task
Diagnose the following Kubernetes pod failure and provide a structured analysis.

## Pod Context
- Pod Name: {pod_name}
- Namespace: {namespace}
- Error Type: {error_type}

## Describe Output
{describe}

## Recent Logs (last 100 lines)
{logs}

## Required Output Format
Respond with a JSON object with these exact keys:
{{
  "root_cause": "<one-sentence summary of the root cause>",
  "detailed_analysis": "<2-4 paragraph markdown analysis explaining why the pod failed>",
  "remediation": "<specific kubectl commands or YAML changes to fix the issue, formatted as markdown code blocks>"
}}

Focus on actionable, precise diagnosis. Do not include secrets or sensitive data in your response.
"""

YAML_SCAN_PROMPT_TEMPLATE = """You are a Senior Kubernetes Security and Best-Practices Expert.

## Task
The following Kubernetes YAML has been scanned by a static linter. Convert the linter errors into clear, 
developer-friendly explanations with specific fix instructions.

特別注意：
如果發現 `ingress-nginx` 的相關警告，請強調該組件已於 2026 年 3 月退役，並強烈建議遷移至 Gateway API。提供具體的 Gateway API (HTTPRoute) 範例作為替代方案。

## Linter Issues Found
{issues}

## Original YAML
{yaml_content}

## Required Output
For each issue, provide:
1. **Why it matters** (security/reliability impact)
2. **How to fix it** (exact YAML snippet to change)

Format your response as Markdown.
"""
