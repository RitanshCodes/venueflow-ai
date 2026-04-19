from __future__ import annotations

import json
import re

from app.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Deterministic local provider for development and demos."""

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        lower_prompt = user_prompt.lower()
        venue = self._extract_section(user_prompt, "Venue") or "Riverside Stadium"
        event = self._extract_section(user_prompt, "Event") or "match day"
        attendance = self._extract_section(user_prompt, "Expected attendance") or "48000"
        priority = self._extract_section(user_prompt, "Experience priority") or "balanced"
        latest_update = self._extract_section(user_prompt, "Latest operator update") or self._extract_section(
            user_prompt,
            "Operator update",
        ) or "Gate queues are rising and the crowd needs a clearer reroute."

        if "venue kickoff packet" in lower_prompt:
            return json.dumps(
                {
                    "north_star": (
                        f"Move {attendance} guests through {venue} with visible routing, sub-12-minute queues, "
                        "and confidence-building updates before pressure turns into frustration."
                    ),
                    "opening_brief": (
                        f"For {event} at {venue}, start with flex ingress on the busiest plaza, a roaming response pod "
                        "between security and guest services, and one shared command cadence every five minutes."
                    ),
                    "fan_message": (
                        f"{event} guests: use the light-blue routes for the fastest entry, keep mobile tickets ready, "
                        "and follow staff for express and accessible lanes."
                    ),
                    "hotspot_watchlist": [
                        "Primary entry gates 20 minutes before start time.",
                        "Main concourse intersections after halftime or rain delays.",
                        "Restroom and concession clusters near family sections.",
                    ],
                    "quick_wins": [
                        "Open one backup lane before queues exceed 12 minutes.",
                        "Push one in-app and PA update before each traffic shift.",
                        "Assign a named zone owner for entry, concourse, and guest recovery.",
                    ],
                    "coordination_focus": [
                        f"Bias toward {priority.replace('_', ' ')} while protecting accessibility.",
                        "Keep security, ushers, and guest services on one radio loop.",
                        "Escalate bottlenecks with a timestamp, queue estimate, and fallback route.",
                    ],
                }
            )

        if "dispatcher response move" in lower_prompt:
            priority_level = self._infer_priority(latest_update)
            return json.dumps(
                {
                    "operational_response": (
                        f"Stabilize the pressure point first: route overflow away from the tightest pinch point at {venue}, "
                        "open one backup service position, and have the zone lead confirm queue time, signage, and staff spacing "
                        "within the next three minutes."
                    ),
                    "public_message": (
                        "Fans near the busiest entry should follow blue route signage for the fastest access. "
                        "Extra staff and additional lanes are now being opened."
                    ),
                    "staff_actions": [
                        "Dispatch one supervisor to own the hotspot and report queue time every 3 minutes.",
                        "Shift two frontline staff to the backup lane or adjacent service bank.",
                        "Send guest-services ambassadors to guide families and accessible guests to lower-friction routes.",
                    ],
                    "priority_level": priority_level,
                }
            )

        if "operations analyst feedback" in lower_prompt:
            wins = [
                "The update is grounded in the live floor reality instead of vague concern.",
                "The response keeps movement and communications connected, which helps prevent crowd anxiety.",
            ]
            if re.search(r"\b\d+(?:\.\d+)?\b|minutes?|eta|scanner|lane\b", latest_update.lower()):
                wins[0] = "You quantified the bottleneck, which makes escalation faster and more credible."
            risks = [
                "Ownership could still blur if one zone lead is not explicitly named.",
                "The guest message should mention the fallback route and accessible option more clearly.",
            ]
            if re.search(r"\b(accessible|wheelchair|mobility|family|stroller|ada)\b", latest_update.lower()):
                risks[1] = "Accessibility is mentioned, but the physical handoff still needs a clear waypoint."
            return json.dumps(
                {
                    "wins": wins,
                    "risks": risks,
                    "coaching_tip": (
                        "Always pair the bottleneck report with one metric, one owner, and one guest-facing message."
                    ),
                    "next_move": (
                        "Confirm the new queue time after the reroute, then decide whether to keep the backup lane open."
                    ),
                }
            )

        if "attendee experience lens" in lower_prompt:
            return json.dumps(
                {
                    "experience_upgrade": (
                        "Add a service-recovery touch: use staff with handheld signs to intercept confused guests before they hit the pinch point, "
                        "and provide one reassuring message about what changed and where to go."
                    ),
                    "blindspots": [
                        "Families and first-time visitors may not decode a reroute without visual wayfinding.",
                        "Guests already in a long line need an ETA, not just a direction change.",
                        "Hydration, shade, and restroom access matter if the delay sits outside the bowl.",
                    ],
                    "accessibility_check": (
                        "Keep one clearly marked accessible lane active during every reroute and position a staff member at the decision point."
                    ),
                }
            )

        return json.dumps({"message": "Mock response generated for local development."})

    @staticmethod
    def _extract_section(prompt: str, label: str) -> str:
        pattern = rf"{re.escape(label)}:\n(.*?)(?:\n\n[A-Z][^:\n]*:\n|\Z)"
        match = re.search(pattern, prompt, re.DOTALL)
        if not match:
            return ""
        return match.group(1).strip()

    @staticmethod
    def _infer_priority(update: str) -> str:
        lower = update.lower()
        if re.search(r"\b(crush|medical|injury|evacuat|fight|storm|fire)\b", lower):
            return "critical"
        if re.search(r"\b(surge|overflow|scanner|down|jam|bottleneck|queue)\b", lower):
            return "high"
        if re.search(r"\b(delay|slow|busy|traffic)\b", lower):
            return "medium"
        return "low"
