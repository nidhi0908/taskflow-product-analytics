-- Channel Quality Deep-Dive
-- Compares activation, retention, and monetization across acquisition channels.
-- Answers: "Are paid-acquisition users worth the CAC?"

WITH user_channels AS (
    SELECT
        person_id,
        any(properties.acquisition_channel) AS channel
    FROM events
    WHERE event = 'signed_up'
      AND properties.acquisition_channel IS NOT NULL
    GROUP BY person_id
),
activation AS (
    SELECT
        uc.channel,
        count(DISTINCT uc.person_id) AS total_signups,
        count(DISTINCT CASE WHEN e.event = 'onboarding_completed' THEN uc.person_id ELSE NULL END) AS activated,
        count(DISTINCT CASE WHEN e.event = 'checkout_completed' THEN uc.person_id ELSE NULL END) AS paid,
        count(DISTINCT CASE WHEN e.event = 'session_started' THEN uc.person_id ELSE NULL END) AS returned_at_least_once
    FROM user_channels uc
    LEFT JOIN events e ON e.person_id = uc.person_id
    GROUP BY uc.channel
)
SELECT
    channel,
    total_signups,
    activated,
    round(activated * 100.0 / total_signups, 1) AS activation_rate_pct,
    returned_at_least_once,
    round(returned_at_least_once * 100.0 / total_signups, 1) AS return_rate_pct,
    paid,
    round(paid * 100.0 / total_signups, 2) AS paid_conversion_pct
FROM activation
ORDER BY total_signups DESC;