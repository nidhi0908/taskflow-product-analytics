"""
TaskFlow event simulator.
Generates synthetic but structured user behavior with deliberate patterns:
  1. ~40% drop off during onboarding (funnel)
  2. Users who invite a teammate retain ~3x better (multiplayer)
  3. A/B test: simplified onboarding lifts activation ~15%
  4. Paid acquisition users churn faster than organic (HogQL story)
"""

import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

SEED = 42
random.seed(SEED)

# ---------- Config ----------
SIMULATION_END = datetime.now(timezone.utc) - timedelta(days=3)  # 48hr+ buffer
SIMULATION_START = SIMULATION_END - timedelta(days=30)

ACQUISITION_CHANNELS = ["organic", "paid_search", "referral", "direct"]
COMPANY_SIZES = ["1", "2-10", "11-50", "51-200", "200+"]
INDUSTRIES = ["tech", "marketing", "design", "consulting", "other"]
COUNTRIES = ["DE", "US", "GB", "FR", "NL", "IN"]
TASK_PRIORITIES = ["low", "medium", "high"]
PAYWALL_FEATURES = ["gantt_chart", "file_attachment", "advanced_reports"]

# ---------- Helpers ----------
def random_datetime_between(start, end):
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)

def make_user(user_index):
    """Create a user with person properties and a hidden 'archetype' that drives behavior."""
    channel = random.choices(
        ACQUISITION_CHANNELS, weights=[40, 30, 20, 10]
    )[0]
    signup_date = random_datetime_between(SIMULATION_START, SIMULATION_END - timedelta(days=2))

    # A/B test variant: 50/50 split
    variant = random.choice(["control", "treatment"])

    # Hidden archetype — drives how engaged this user becomes.
    # Treatment group has higher activation rate (the lift we want to detect)
    base_activation_rate = 0.60 if variant == "control" else 0.75
    # Paid acquisition users are slightly less sticky
    if channel == "paid_search":
        base_activation_rate -= 0.10

    will_activate = random.random() < base_activation_rate
    will_invite = will_activate and random.random() < 0.40  # 40% of activated users invite

    return {
        "distinct_id": f"user_{user_index:05d}",
        "person_properties": {
            "username": f"user_{user_index:05d}",
            "signup_date": signup_date.isoformat(),
            "acquisition_channel": channel,
            "company_size": random.choice(COMPANY_SIZES),
            "industry": random.choice(INDUSTRIES),
            "country": random.choice(COUNTRIES),
            "plan": "free",
            "experiment_variant": variant,
        },
        "_signup_date": signup_date,
        "_will_activate": will_activate,
        "_will_invite": will_invite,
        "_channel": channel,
        "_variant": variant,
    }

def simulate_user_events(user):
    """Generate the full event sequence for one user. Returns list of event dicts."""
    events = []
    distinct_id = user["distinct_id"]
    signup = user["_signup_date"]

    def add_event(name, ts, props=None):
        events.append({
            "distinct_id": distinct_id,
            "event": name,
            "timestamp": ts,
            "properties": props or {},
        })

    # 1. Signup (everyone)
    add_event("signed_up", signup, {
        "acquisition_channel": user["_channel"],
        "experiment_variant": user["_variant"],
    })

    # 2. Onboarding started — 95% of signups
    if random.random() < 0.95:
        ts = signup + timedelta(minutes=random.randint(1, 10))
        add_event("onboarding_started", ts)
    else:
        return events  # bounced immediately

    # 3. Onboarding completed — depends on activation archetype
    if not user["_will_activate"]:
        return events  # dropped during onboarding (funnel pattern #1)

    ts = signup + timedelta(minutes=random.randint(5, 30))
    add_event("onboarding_completed", ts)

    # 4. First project
    ts = signup + timedelta(minutes=random.randint(10, 60))
    project_id = f"proj_{uuid4().hex[:8]}"
    add_event("project_created", ts, {"project_id": project_id})

    # 5. First few tasks
    num_initial_tasks = random.randint(2, 6)
    for i in range(num_initial_tasks):
        ts = signup + timedelta(minutes=random.randint(15, 120))
        add_event("task_created", ts, {
            "project_id": project_id,
            "task_priority": random.choice(TASK_PRIORITIES),
            "task_has_due_date": random.random() < 0.5,
        })

    # 6. Member invite (multiplayer threshold — pattern #2)
    if user["_will_invite"]:
        ts = signup + timedelta(hours=random.randint(1, 24))
        add_event("member_invited", ts, {"invite_method": "email"})
        # 70% of invites get accepted
        if random.random() < 0.70:
            ts2 = ts + timedelta(hours=random.randint(1, 48))
            add_event("member_joined", ts2)

    # 7. Return-visit sessions over the next 30 days
    # Multiplayer users retain ~3x better
    if user["_will_invite"]:
        retention_strength = 0.55  # comes back ~55% of remaining days
    else:
        retention_strength = 0.18

    days_remaining = (SIMULATION_END - signup).days
    for day_offset in range(1, days_remaining + 1):
        if random.random() > retention_strength:
            continue
        # paid users decay faster over time (pattern #4)
        if user["_channel"] == "paid_search" and day_offset > 14:
            if random.random() < 0.5:
                continue

        session_day = signup + timedelta(days=day_offset)
        session_start = session_day + timedelta(
            hours=random.randint(8, 20),
            minutes=random.randint(0, 59)
        )
        add_event("session_started", session_start)

        # During the session: do some work
        for _ in range(random.randint(1, 5)):
            t = session_start + timedelta(minutes=random.randint(1, 30))
            action = random.choices(
                ["task_created", "task_completed", "task_assigned", "task_commented", "task_updated"],
                weights=[30, 30, 15, 15, 10]
            )[0]
            add_event(action, t, {
                "project_id": project_id,
                "task_priority": random.choice(TASK_PRIORITIES),
            })

        # Maybe hit a paywall
        if random.random() < 0.05:
            t = session_start + timedelta(minutes=random.randint(5, 25))
            feature = random.choice(PAYWALL_FEATURES)
            add_event("paywall_shown", t, {"feature_name": feature})
            if random.random() < 0.30:
                add_event("paywall_upgrade_clicked", t + timedelta(seconds=15), {"feature_name": feature})
                if random.random() < 0.50:
                    add_event("pricing_page_viewed", t + timedelta(seconds=30))
                    if random.random() < 0.40:
                        add_event("checkout_started", t + timedelta(minutes=1))
                        if random.random() < 0.70:
                            add_event("checkout_completed", t + timedelta(minutes=3), {
                                "plan_chosen": "pro",
                                "billing_period": "monthly",
                                "revenue_usd": 12,
                            })
                            add_event("subscription_activated", t + timedelta(minutes=3, seconds=10))

    return events


def generate_all(num_users):
    """Generate all users + their events. Returns (users, events)."""
    users = [make_user(i) for i in range(num_users)]
    all_events = []
    for u in users:
        all_events.extend(simulate_user_events(u))
    return users, all_events


if __name__ == "__main__":
    # Smoke test the simulator with no PostHog calls
    users, events = generate_all(num_users=10)
    print(f"Generated {len(users)} users and {len(events)} events")
    print("\nSample user:")
    print(users[0])
    print("\nFirst 5 events:")
    for e in events[:5]:
        print(f"  {e['timestamp'].isoformat()}  {e['distinct_id']}  {e['event']}")