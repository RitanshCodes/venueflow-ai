from __future__ import annotations

import re
from statistics import mean

from app.core.models import OperationsScoreCard


class VenueOperationsScorer:
    crowd_flow_markers = {
        "gate",
        "lane",
        "ingress",
        "egress",
        "reroute",
        "redirect",
        "concourse",
        "entry",
        "exit",
        "section",
        "plaza",
        "overflow",
        "wayfinding",
        "open",
        "close",
    }
    wait_time_markers = {
        "queue",
        "line",
        "minutes",
        "eta",
        "scanner",
        "turnstile",
        "checkpoint",
        "concession",
        "restroom",
        "bag check",
        "express",
        "kiosk",
        "booth",
    }
    coordination_markers = {
        "dispatch",
        "notify",
        "update",
        "supervisor",
        "radio",
        "security",
        "medical",
        "guest services",
        "operations",
        "ops",
        "steward",
        "usher",
        "volunteer",
        "command",
        "team",
    }
    experience_markers = {
        "fan",
        "guest",
        "accessible",
        "accessibility",
        "wheelchair",
        "mobility",
        "family",
        "stroller",
        "hydration",
        "shade",
        "signage",
        "restroom",
        "sensory",
        "premium",
        "reassure",
    }
    communication_markers = {
        "message",
        "alert",
        "announce",
        "push",
        "broadcast",
        "signage",
        "pa",
        "app",
        "notify",
        "eta",
    }
    stopwords = {
        "about",
        "after",
        "before",
        "being",
        "between",
        "could",
        "first",
        "from",
        "into",
        "only",
        "other",
        "should",
        "their",
        "there",
        "these",
        "they",
        "this",
        "when",
        "where",
        "while",
        "with",
        "would",
    }
    risky_patterns = {
        "Potential overreaction": [
            r"\bshut down everything\b",
            r"\bclose all gates\b",
            r"\bstop all entry\b",
        ],
        "Passive monitoring risk": [
            r"\bwait and see\b",
            r"\bmonitor only\b",
            r"\bkeep watching\b",
        ],
    }

    def score_update(
        self,
        update: str,
        latest_command_message: str = "",
        event_name: str = "",
    ) -> OperationsScoreCard:
        text = " ".join(update.split())
        lower = text.lower()
        sentences = [sentence.strip() for sentence in re.split(r"[.!?]+", text) if sentence.strip()]
        words = re.findall(r"\b[\w'-]+\b", lower)

        crowd_flow_hits = self._count_hits(lower, self.crowd_flow_markers)
        wait_time_hits = self._count_hits(lower, self.wait_time_markers)
        coordination_hits = self._count_hits(lower, self.coordination_markers)
        experience_hits = self._count_hits(lower, self.experience_markers)
        communication_hits = self._count_hits(lower, self.communication_markers)
        overlap = self._keyword_overlap(lower, latest_command_message.lower())
        zone_bonus = 1 if re.search(r"\b(gate|zone|lane|section|entry|exit|plaza|concourse)\b", lower) else 0
        quant_bonus = 1 if re.search(r"\b\d+(?:\.\d+)?\b|%", text) else 0
        time_bonus = 1 if re.search(r"\b\d+\s?(?:min|mins|minute|minutes)\b|\beta\b", lower) else 0
        team_bonus = 1 if len(re.findall(r"\b(security|medical|usher|volunteer|ops|operations|guest services)\b", lower)) >= 2 else 0
        accessibility_bonus = 1 if re.search(r"\b(accessible|wheelchair|mobility|ada|family|stroller|sensory)\b", lower) else 0
        sentence_bonus = 1 if len(sentences) >= 3 else 0
        depth_bonus = min(len(words) // 50, 2)
        event_bonus = 1 if event_name and any(token in lower for token in re.findall(r"\b[a-z]{4,}\b", event_name.lower())) else 0

        crowd_flow = min(10, max(2, 3 + crowd_flow_hits + zone_bonus + sentence_bonus + min(overlap, 2)))
        wait_time = min(10, max(1, 2 + wait_time_hits + quant_bonus + time_bonus + min(depth_bonus, 2)))
        coordination = min(10, max(2, 3 + coordination_hits + team_bonus + min(overlap, 2) + event_bonus))
        fan_experience = min(10, max(2, 2 + experience_hits + communication_hits + accessibility_bonus + min(depth_bonus, 1)))

        risks = self._detect_risks(
            text=lower,
            wait_time_hits=wait_time_hits,
            coordination_hits=coordination_hits,
            experience_hits=experience_hits,
            communication_hits=communication_hits,
            quant_bonus=quant_bonus,
            accessibility_bonus=accessibility_bonus,
        )
        penalty = min(len(risks) * 4, 16)
        weighted = (crowd_flow * 0.30) + (wait_time * 0.25) + (coordination * 0.25) + (fan_experience * 0.20)
        overall = max(0, min(100, round(weighted * 10) - penalty))

        return OperationsScoreCard(
            crowd_flow=crowd_flow,
            wait_time=wait_time,
            coordination=coordination,
            fan_experience=fan_experience,
            overall=overall,
            flagged_risks=risks,
            rubric_notes=self._build_notes(crowd_flow, wait_time, coordination, fan_experience, risks),
        )

    @staticmethod
    def average_overall(scores: list[OperationsScoreCard]) -> float:
        if not scores:
            return 0.0
        return round(mean(score.overall for score in scores), 2)

    def _count_hits(self, text: str, markers: set[str]) -> int:
        return sum(1 for marker in markers if marker in text)

    def _keyword_overlap(self, text: str, latest_command_message: str) -> int:
        command_keywords = {
            token
            for token in re.findall(r"\b[a-z]{4,}\b", latest_command_message)
            if token not in self.stopwords
        }
        if not command_keywords:
            return 0

        update_tokens = set(re.findall(r"\b[a-z]{4,}\b", text))
        return len(command_keywords & update_tokens)

    def _detect_risks(
        self,
        *,
        text: str,
        wait_time_hits: int,
        coordination_hits: int,
        experience_hits: int,
        communication_hits: int,
        quant_bonus: int,
        accessibility_bonus: int,
    ) -> list[str]:
        risks: list[str] = []

        if wait_time_hits == 0 and quant_bonus == 0:
            risks.append("Queue impact is not quantified yet.")
        if coordination_hits < 2:
            risks.append("Cross-team ownership is still unclear.")
        if communication_hits == 0:
            risks.append("Attendee messaging is missing from the plan.")
        if experience_hits == 0 and accessibility_bonus == 0:
            risks.append("Accessibility and family needs are not addressed.")

        for name, patterns in self.risky_patterns.items():
            if any(re.search(pattern, text) for pattern in patterns):
                risks.append(name)

        return risks[:4]

    def _build_notes(
        self,
        crowd_flow: int,
        wait_time: int,
        coordination: int,
        fan_experience: int,
        risks: list[str],
    ) -> list[str]:
        notes: list[str] = []

        if crowd_flow >= 7:
            notes.append("Flow actions are concrete and tied to physical movement on site.")
        else:
            notes.append("Be more explicit about which gate, lane, or route you are changing.")

        if wait_time >= 7:
            notes.append("The update treats queue pressure as an operational metric, not a vague concern.")
        else:
            notes.append("Add a queue estimate, ETA, or throughput metric to sharpen the response.")

        if coordination >= 7:
            notes.append("Multiple teams have a clearer operating rhythm and owner.")
        else:
            notes.append("Name the owner and the teams who need to move together.")

        if fan_experience >= 7:
            notes.append("The plan protects attendee confidence, not just throughput.")
        else:
            notes.append("Include guest messaging, signage, or accessibility support in the response.")

        if risks:
            notes.append(f"Biggest risk right now: {risks[0]}")

        return notes[:5]


DebateRubricScorer = VenueOperationsScorer
