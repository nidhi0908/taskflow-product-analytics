# TaskFlow Event Schema

19 events across 5 phases of the B2B SaaS user journey. Designed to answer funnel, retention, A/B testing, and channel quality questions.

## Design principles

- **Naming:** `object_verb` past tense (e.g., `task_created`, not `create_task`)
- **Intentional actions only:** No vanity events like `button_clicked` or `page_viewed` — only actions that reflect real user intent
- **Avoid event explosion:** Paywall events use a single event with a `feature_name` property, not separate events per feature
- **Split events at funnel steps:** `member_invited` and `member_joined` are separate events so invite acceptance can be measured as a conversion

---

## Person properties

Set once per user via `$set` on their first event.

| Property | Type | Values |
|---|---|---|
| `username` | string | `user_00000`, `user_00001`... (display name) |
| `signup_date` | ISO datetime | Timestamp of signup |
| `acquisition_channel` | string | `organic`, `paid_search`, `referral`, `direct` |
| `company_size` | string | `1`, `2-10`, `11-50`, `51-200`, `200+` |
| `industry` | string | `tech`, `marketing`, `design`, `consulting`, `other` |
| `country` | string | ISO country code |
| `plan` | string | `free`, `pro`, `business` |
| `experiment_variant` | string | `control`, `treatment` (onboarding A/B test) |

---

## Events

### Phase 1: Activation

| Event | Fires when | Key properties |
|---|---|---|
| `signed_up` | User creates an account | `acquisition_channel`, `experiment_variant` |
| `onboarding_started` | User enters onboarding flow | — |
| `onboarding_completed` | User finishes all onboarding steps | — |
| `project_created` | User creates their first/Nth project | `project_id` |
| `task_created` | User creates a task | `project_id`, `task_priority`, `task_has_due_date` |

### Phase 2: Engagement (task lifecycle)

| Event | Fires when | Key properties |
|---|---|---|
| `task_assigned` | A task is assigned to a user | `project_id`, `task_priority` |
| `task_completed` | A task is marked done | `project_id`, `task_priority` |
| `task_commented` | A user comments on a task | `project_id` |
| `task_updated` | Task title/description/due date edited | `project_id` |

### Phase 3: Collaboration

| Event | Fires when | Key properties |
|---|---|---|
| `member_invited` | User sends an invite to a teammate | `invite_method` |
| `member_joined` | Invited teammate accepts and joins | — |

### Phase 4: Retention

| Event | Fires when | Key properties |
|---|---|---|
| `session_started` | New session after 30+ min of inactivity | — |

### Phase 5: Monetization

| Event | Fires when | Key properties |
|---|---|---|
| `paywall_shown` | User hits a premium feature gate | `feature_name` (`gantt_chart`, `file_attachment`, `advanced_reports`) |
| `paywall_upgrade_clicked` | User clicks the upgrade CTA on paywall | `feature_name` |
| `pricing_page_viewed` | User lands on /pricing | — |
| `checkout_started` | Payment form rendered | — |
| `checkout_completed` | Payment succeeded | `plan_chosen`, `billing_period`, `revenue_usd` |
| `subscription_activated` | Subscription is live (server confirmation) | — |

### Phase 6: Churn

| Event | Fires when | Key properties |
|---|---|---|
| `subscription_cancelled` | User downgrades or cancels | — |

---

## What I deliberately did NOT track

- **`button_clicked` / `page_viewed`** — vanity events that inflate event volume without producing insight
- **`task_hovered` / `task_scrolled`** — low-intent signals that don't predict retention or revenue
- **Separate events per paywall feature** — collapsed into `paywall_shown` + `feature_name` property to avoid event explosion
- **Login events** — modern apps keep users logged in for weeks; `session_started` is a better "user came back" signal

Keeping the schema deliberately small means dashboards stay readable, funnels are unambiguous, and new events can be added without bloating the analysis surface.