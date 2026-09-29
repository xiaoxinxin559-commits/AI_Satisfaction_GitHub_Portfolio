# 按步骤读代码

所有代码均为本次新建的合成数据演示，不是历史代码片段。代码执行结果只对应 `data/synthetic/`。

## 1. 生成数据：让作品在没有企业数据时也可运行

看 `src/generate_demo.py`。使用固定随机种子生成会话、评分、事件与受评分门控的标签，并故意加入重复问卷、无效评分、全空列、常量字段、跨版本结构性缺失和两条问卷后的事件。

得到 `sessions.csv` 与 `events.csv`。这里的数据生成公式不追求原业务分布，也不以复现原系数为目标。

## 2. 全字段审计：每一列都有去向

看 `src/schema.py` 与 `src/audit.py`。字段按标识、结果、行为、控制、分组、门控标签、下游结果、评测、口径变更与不可用列分类。输出缺失比例、唯一值数与处理理由；新增的未知字段默认进入待确认，不会静默入模。

```python
inventory = field_inventory(raw)
assert set(inventory['field']) == set(raw.columns)
```

## 3. 先确认样本粒度，再去重

保留同一 `session_id` 最新一次问卷，删除不属于 1–5 的结果评分，不插补结果。匿名用户使用独立的演示匿名键，不按 `user_id=0` 一次性去重。不同会话不是重复问卷。

## 4. SQL 聚合：不偷看问卷之后发生的事

看 `sql/session_features.sql`。先限定最新有效问卷，再按会话连接问卷前 24 小时的事件，计算条件计数。SQL 输出与 Python 合成底表逐字段核验；两条未来事件应被排除。

```sql
LEFT JOIN events e ON e.session_id=s.session_id
  AND e.event_time <= s.survey_time
  AND julianday(e.event_time) >= julianday(s.survey_time)-1
```

“没有事件就是零”的前提是事件采集完整。真实日志缺口不能套这个默认值。

## 5. 标签门控检查：识别问卷规则而非产品效果

```python
pos = df[POS_TAGS].sum(axis=1) > 0
violations = (pos & (df['score'] <= 3)).sum()
```

这段代码结合已知问卷规则检查违规记录。零违规并不说明标签独立于分数，反而提醒我们标签是评分后的派生信息。`validate_feature_allowlist` 拒绝评分、门控标签及下游订单等特征。

## 6. 分组留出与训练集内预处理

看 `src/model.py`。同一参与者不跨训练与留出集；缩尾阈值、均值与标准差在训练集学习，留出集只变换。输出参与者划分明细，便于核对是否重叠。

## 7. 模型与诊断

OLS 给出近似等距分数下的条件关联和参与者聚类区间；有序 Logit 做方向敏感性对照。额外报告 Spearman 相关、BH 校正结果、VIF、标准化设计矩阵条件数。结果不自动翻译成“提升量”。

错误模型另加“是否勾选正向标签”，演示为什么泄漏特征会让指标显得更好。这个分支始终标为无效方案，不进入正式特征列表。

## 8. 输出与复盘

`outputs/run_summary.json` 保存实际运行口径与环境；CSV 保留图表底数；`src/plots.py` 生成四张独立统计图；`src/render_site.py` 将实际结果写入离线交互页面。

`src/weekly_report.py` 只展示从非敏感决策日志生成固定结构总结，不调用 LLM，不是运行中的 OpenClaw 或企业 Agent。

## 9. 验收

```bash
python -m pytest -q
```

测试覆盖样本数对账、匿名标识、字段完整性、空/常量列、门控规则与违规捕获、禁止特征、训练集内变换、SQL 时序、缺失主键、随机种子复现和负计数拦截。通过测试证明的是公开演示代码按这些规则运行，不证明真实业务结论。
