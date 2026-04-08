"""
Sends simulated events to PostHog using historical_migration mode.
Configurable user count for chunked testing.

Usage:
    python send_events.py        # defaults to 50 users
    python send_events.py 10     # 10 users
    python send_events.py 1000   # full simulation
"""

import os
import sys
import time
from dotenv import load_dotenv
from posthog import Posthog

from simulator import generate_all

load_dotenv()

api_key = os.getenv("POSTHOG_API_KEY")
host = os.getenv("POSTHOG_HOST")
assert api_key and "eu" in host, "Check your .env file"

# How many users to simulate. Override from CLI: python send_events.py 50
NUM_USERS = int(sys.argv[1]) if len(sys.argv) > 1 else 50
FLUSH_EVERY = 5000  # PostHog queue limit is 10K, we flush at half

posthog = Posthog(
    project_api_key=api_key,
    host=host,
    debug=False,
    historical_migration=True,
)

print(f"Generating {NUM_USERS} users...")
users, events = generate_all(num_users=NUM_USERS)
print(f"Generated {len(events)} events. Sending to PostHog...")

# Sort events by timestamp so PostHog ingests them in order
events.sort(key=lambda e: e["timestamp"])

start = time.time()
sent = 0
identified_users = set()

for event in events:
    distinct_id = event["distinct_id"]

    # Build properties — force PostHog to create a person profile (SDK 7.x fix)
    event_props = dict(event["properties"])
    event_props["$process_person_profile"] = True

    # First time we see a user, attach person properties via $set
    if distinct_id not in identified_users:
        user = next(u for u in users if u["distinct_id"] == distinct_id)
        event_props["$set"] = user["person_properties"]
        identified_users.add(distinct_id)

    posthog.capture(
        distinct_id=distinct_id,
        event=event["event"],
        properties=event_props,
        timestamp=event["timestamp"],
    )
    sent += 1

    if sent % FLUSH_EVERY == 0:
        posthog.flush()
        elapsed = time.time() - start
        print(f"  Sent {sent}/{len(events)} events ({elapsed:.1f}s elapsed)")

posthog.flush()
posthog.shutdown()
elapsed = time.time() - start
print(f"\nDone. Sent {sent} events in {elapsed:.1f}s.")
print("Check PostHog → Activity tab. Historical events take 2-5 min to appear.")