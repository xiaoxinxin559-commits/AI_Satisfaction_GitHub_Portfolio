-- Newly written SQLite demo, not an original production query.
-- One latest valid questionnaire per session; events after the survey are excluded.
-- Known complete event coverage is assumed. With real incomplete logs, missing != zero.
WITH ranked_surveys AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY session_id ORDER BY survey_time DESC
    ) AS submission_rank
    FROM surveys
), valid_surveys AS (
    SELECT * FROM ranked_surveys
    WHERE submission_rank=1 AND score IN (1,2,3,4,5)
), aggregated AS (
    SELECT s.session_id,
           SUM(CASE WHEN e.event_name='quick_result_count' THEN 1 ELSE 0 END) AS quick_result_count,
           SUM(CASE WHEN e.event_name='consult_result_count' THEN 1 ELSE 0 END) AS consult_result_count,
           SUM(CASE WHEN e.event_name='followup_shown_count' THEN 1 ELSE 0 END) AS followup_shown_count,
           SUM(CASE WHEN e.event_name='followup_click_count' THEN 1 ELSE 0 END) AS followup_click_count
    FROM valid_surveys s
    LEFT JOIN events e ON e.session_id=s.session_id
      AND e.event_time <= s.survey_time
      AND julianday(e.event_time) >= julianday(s.survey_time)-1
    GROUP BY s.session_id
)
SELECT s.session_id, s.score, a.quick_result_count, a.consult_result_count,
       a.followup_shown_count, a.followup_click_count
FROM valid_surveys s
LEFT JOIN aggregated a ON s.session_id=a.session_id
ORDER BY s.session_id;
