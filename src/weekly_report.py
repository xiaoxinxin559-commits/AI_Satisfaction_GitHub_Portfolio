"""Deterministic report demo from a mock decision log, not an LLM/Agent integration."""
import json
from pathlib import Path


def render_weekly(log_path: Path) -> str:
    log=json.loads(log_path.read_text(encoding="utf-8"))
    lines=["# 工作复盘示例", "", "> 本页从公开演示决策日志生成，非原始周报。没有调用任何模型或后台 Agent。", "", "## 本周完成", ""]
    for entry in log["decisions"]:
        lines.append(f"- {entry['task']}：{entry['decision']}；依据：{entry['evidence']}。")
    lines.extend(["", "## 下一步验证", "", "补足独立测量与线上验证，不把相关系数写成提升量。", "", "## 已确认的协作偏好", "", "先确认指标口径；代码、输出和解释一起交付；保留版本与取舍依据。", "", "这些是工作偏好，不是心理测评或人格诊断。", ""])
    return "\n".join(lines)
