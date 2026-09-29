"""Public aliases for this newly constructed demo; not the source system schema."""
COUNT_FEATURES = [
    "quick_result_count", "consult_result_count", "followup_shown_count", "followup_click_count"
]
MODEL_FEATURES = COUNT_FEATURES + ["is_returning", "age_level", "age_unknown"]
POS_TAGS = ["pos_recommendation", "pos_clarity", "pos_warmth", "pos_professional"]
NEG_TAGS = ["neg_offtopic", "neg_inaccurate", "neg_thin", "neg_recommendation"]
FORBIDDEN_FEATURES = POS_TAGS + NEG_TAGS + [
    "has_positive_tag", "tag_net_score", "order_flag", "expert_score", "score"
]
# Display names explain demo semantics, not confidential column names.
CATALOG = {
    "session_id": ("会话键", "metadata", "仅去重与连接；不是预测特征"),
    "user_id": ("登录标识", "metadata", "0 仅表示未登录；不可将所有 0 合为一人"),
    "anonymous_id": ("匿名演示标识", "metadata", "仅用于演示分组；全部为合成标识"),
    "survey_time": ("问卷时间", "metadata", "限定事件窗口；重复问卷保留最新提交"),
    "period": ("演示时期", "group", "仅分组展示；不对应真实业务日期"),
    "entry_source": ("入口类型", "group", "用于分层检查；演示主模型不纳入"),
    "score": ("满意度评分", "target", "1–5 有序结果，不得进入特征白名单"),
    "age_level": ("年龄组序位", "control", "控制项；按 0–3 等距近似仅用于演示"),
    "is_returning": ("是否老用户", "control", "问卷前已知的二元控制项"),
    "quick_result_count": ("快测结果展示", "behavior", "问卷前事件计数；训练集 P99 缩尾后 log1p"),
    "consult_result_count": ("问诊结果展示", "behavior", "问卷前事件计数；训练集 P99 缩尾后 log1p"),
    "followup_shown_count": ("追问提示展示", "behavior", "演示定义为展示事件数；非真实表头"),
    "followup_click_count": ("追问提示点击", "behavior", "问卷前计数；不预设越多越好"),
    "order_flag": ("是否下单", "downstream", "同期/下游结果；不进入满意度前因模型"),
    "return_next_day": ("次日回访字段", "unusable", "故意构造的常量，用于演示数据质量拦截"),
    "legacy_card_count": ("旧版卡片计数", "versioned", "演示 P3/P4 结构性缺失，不能补零后做跨期趋势"),
    "unused_empty": ("空导出列", "unusable", "故意构造的全空列，保留在字段盘点中"),
    "expert_score": ("独立评测评分", "evaluation", "仅演示样本有值；与满意度分开报告"),
}
for _field in POS_TAGS:
    CATALOG[_field] = (_field.replace("pos_", "正向标签·"), "gated_label", "评分≥4 后展示；仅作反馈描述，不作前因特征")
for _field in NEG_TAGS:
    CATALOG[_field] = (_field.replace("neg_", "负向标签·"), "gated_label", "评分≤3 后展示；仅作反馈描述，不作前因特征")
ROLE_NAMES = {"metadata":"标识与元数据", "group":"分组维度", "target":"结果变量", "control":"控制项", "behavior":"行为候选", "downstream":"下游结果", "unusable":"不可用字段", "versioned":"口径变更", "evaluation":"独立评测", "gated_label":"门控标签"}
