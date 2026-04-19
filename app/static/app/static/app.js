const socketStatus = document.getElementById("socket-status");
const liveChip = socketStatus?.closest(".live-chip");
const roundChip = document.getElementById("round-chip");
const transcript = document.getElementById("transcript");
const sessionMeta = document.getElementById("session-meta");
const analystFeedback = document.getElementById("analyst-feedback");
const flaggedRisks = document.getElementById("flagged-risks");
const dispatcherActions = document.getElementById("dispatcher-actions");
const experienceLens = document.getElementById("experience-lens");
const summary = document.getElementById("summary");
const submitUpdateButton = document.getElementById("submit-update");
const startForm = document.getElementById("start-form");
const updateForm = document.getElementById("update-form");
const eventLabel = document.getElementById("event-label");
const attendanceLabel = document.getElementById("attendance-label");
const priorityLabel = document.getElementById("priority-label");
const heroMode = document.getElementById("hero-mode");
const avgWaitTime = document.getElementById("avg-wait-time");
const densityZoneCount = document.getElementById("density-zone-count");
const systemStatusText = document.getElementById("system-status-text");
const systemStatusNote = document.getElementById("system-status-note");
const attendanceNote = document.getElementById("attendance-note");
const waitNote = document.getElementById("wait-note");
const densityNote = document.getElementById("density-note");
const dashboardClock = document.getElementById("dashboard-clock");
const runSimShortcut = document.getElementById("run-sim-shortcut");
const presetButtons = document.querySelectorAll(".preset-btn");
const scoreCrowdFlow = document.getElementById("score-crowd-flow");
const scoreWaitTime = document.getElementById("score-wait-time");
const scoreCoordination = document.getElementById("score-coordination");
const scoreFanExperience = document.getElementById("score-fan-experience");
const scoreOverall = document.getElementById("score-overall");
const barCrowdFlow = document.getElementById("bar-crowd-flow");
const barWaitTime = document.getElementById("bar-wait-time");
const barCoordination = document.getElementById("bar-coordination");
const barFanExperience = document.getElementById("bar-fan-experience");
const barOverall = document.getElementById("bar-overall");

let socket;
let sessionStarted = false;
let currentRoundLimit = 0;

function connectSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/ws/operations`);

  socket.addEventListener("open", () => {
    socketStatus.textContent = "LIVE";
    liveChip?.classList.add("connected");
  });

  socket.addEventListener("close", () => {
    socketStatus.textContent = "Offline";
    liveChip?.classList.remove("connected");
    submitUpdateButton.disabled = true;
    sessionStarted = false;
    heroMode.textContent = "Reconnecting";
    window.setTimeout(connectSocket, 800);
  });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "session_started") {
      handleSessionStarted(message.payload);
      return;
    }

    if (message.type === "round_result") {
      handleRoundResult(message.payload);
      return;
    }

    if (message.type === "error") {
      addBubble("command", "System", message.payload.message, "Notice");
    }
  });
}

function handleSessionStarted(payload) {
  sessionStarted = true;
  currentRoundLimit = payload.round_limit;
  submitUpdateButton.disabled = false;
  transcript.innerHTML = "";

  heroMode.textContent = "System Active";
  eventLabel.textContent = payload.event_name;
  attendanceLabel.textContent = formatAttendance(payload.expected_attendance);
  attendanceNote.textContent = payload.venue_name;
  priorityLabel.textContent = `${formatPriority(payload.priority)} focus`;
  avgWaitTime.textContent = `${baselineWaitForPriority(payload.priority).toFixed(1)} min`;
  waitNote.textContent = "Initial projection";
  densityZoneCount.textContent = String(Math.max(1, Math.min(4, payload.strategy.hotspot_watchlist.length)));
  densityNote.textContent = "Watchlist loaded";
  systemStatusText.textContent = "READY";
  systemStatusNote.textContent = "Awaiting first floor signal";

  resetAnalysis();
  addBubble("command", "AI Command", payload.opening_turn.message, "Kickoff");
  addBubble("broadcast", "Fan Broadcast", payload.strategy.fan_message, "Attendee Alert");
  roundChip.textContent = `Round 1 / ${payload.round_limit}`;

  sessionMeta.innerHTML = `
    <p><strong>North star:</strong> ${escapeHtml(payload.strategy.north_star)}</p>
    <p class="detail-title">Hotspot watchlist</p>
    ${renderList(payload.strategy.hotspot_watchlist)}
    <p class="detail-title">Quick wins</p>
    ${renderList(payload.strategy.quick_wins)}
    <p class="detail-title">Coordination focus</p>
    ${renderList(payload.strategy.coordination_focus)}
  `;
}

function handleRoundResult(payload) {
  addBubble("command", "Dispatcher", payload.dispatcher_move.operational_response, `Round ${payload.round_number}`);
  addBubble(
    "broadcast",
    "Attendee Message",
    payload.dispatcher_move.public_message,
    payload.dispatcher_move.priority_level.toUpperCase(),
  );

  renderScoreBoard(payload.scorecard);
  updateOverviewTelemetry(payload);

  analystFeedback.classList.remove("muted");
  analystFeedback.innerHTML = `
    <p><strong>Coaching tip:</strong> ${escapeHtml(payload.analyst_feedback.coaching_tip)}</p>
    <p><strong>Next move:</strong> ${escapeHtml(payload.analyst_feedback.next_move)}</p>
    <p class="detail-title">Wins</p>
    ${renderList(payload.analyst_feedback.wins)}
    <p class="detail-title">Risks</p>
    ${renderList(payload.analyst_feedback.risks)}
  `;

  if (payload.scorecard.flagged_risks.length) {
    flaggedRisks.classList.remove("muted");
    flaggedRisks.innerHTML = payload.scorecard.flagged_risks
      .map((item) => `<span class="tag">${escapeHtml(item)}</span>`)
      .join("");
  } else {
    flaggedRisks.textContent = "No major risks flagged in this round.";
    flaggedRisks.classList.add("muted");
  }

  dispatcherActions.classList.remove("muted");
  dispatcherActions.innerHTML = `
    <p><strong>Priority:</strong> ${escapeHtml(formatPriority(payload.dispatcher_move.priority_level))}</p>
    <p>${escapeHtml(payload.dispatcher_move.operational_response)}</p>
    <p class="detail-title">Staff actions</p>
    ${renderList(payload.dispatcher_move.staff_actions)}
  `;

  experienceLens.classList.remove("muted");
  experienceLens.innerHTML = `
    <p>${escapeHtml(payload.experience_coach.experience_upgrade)}</p>
    <p><strong>Accessibility check:</strong> ${escapeHtml(payload.experience_coach.accessibility_check)}</p>
    <p class="detail-title">Blindspots</p>
    ${renderList(payload.experience_coach.blindspots)}
  `;

  if (payload.session_complete && payload.summary) {
    submitUpdateButton.disabled = true;
    roundChip.textContent = "Simulation Complete";
    summary.classList.remove("muted");
    summary.innerHTML = `
      <p><strong>Best call:</strong> ${escapeHtml(payload.summary.best_call)}</p>
      <p><strong>Biggest bottleneck:</strong> ${escapeHtml(payload.summary.biggest_bottleneck)}</p>
      <p><strong>Next priority:</strong> ${escapeHtml(payload.summary.next_priority)}</p>
      <p class="muted">
        Avg flow ${payload.summary.average_crowd_flow} | Avg wait ${payload.summary.average_wait_time} |
        Avg coordination ${payload.summary.average_coordination} | Avg experience ${payload.summary.average_fan_experience}
      </p>
    `;
    return;
  }

  roundChip.textContent = `Round ${payload.round_number + 1} / ${currentRoundLimit}`;
}

function resetAnalysis() {
  renderScoreBoard({ crowd_flow: 0, wait_time: 0, coordination: 0, fan_experience: 0, overall: 0 });
  analystFeedback.textContent = "No round scored yet.";
  analystFeedback.classList.add("muted");
  flaggedRisks.textContent = "No risks flagged yet.";
  flaggedRisks.classList.add("muted");
  dispatcherActions.textContent = "Field actions will appear here after the first live update.";
  dispatcherActions.classList.add("muted");
  experienceLens.textContent = "The attendee experience layer will call out accessibility, reassurance, and service-recovery gaps.";
  experienceLens.classList.add("muted");
  summary.textContent = "Finish the live rounds to unlock the final summary.";
  summary.classList.add("muted");
}

function renderScoreBoard(scorecard) {
  scoreCrowdFlow.textContent = `${scorecard.crowd_flow}/10`;
  scoreWaitTime.textContent = `${scorecard.wait_time}/10`;
  scoreCoordination.textContent = `${scorecard.coordination}/10`;
  scoreFanExperience.textContent = `${scorecard.fan_experience}/10`;
  scoreOverall.textContent = `${scorecard.overall}/100`;

  barCrowdFlow.style.width = `${(scorecard.crowd_flow / 10) * 100}%`;
  barWaitTime.style.width = `${(scorecard.wait_time / 10) * 100}%`;
  barCoordination.style.width = `${(scorecard.coordination / 10) * 100}%`;
  barFanExperience.style.width = `${(scorecard.fan_experience / 10) * 100}%`;
  barOverall.style.width = `${scorecard.overall}%`;
}

function updateOverviewTelemetry(payload) {
  const waitMinutes = extractWaitMinutes(payload.operator_update) ?? derivedWaitMinutes(payload.scorecard.wait_time);
  const hotspotCount = estimateHotspotCount(payload);
  const status = statusFromOverall(payload.scorecard.overall, payload.dispatcher_move.priority_level);

  avgWaitTime.textContent = `${waitMinutes.toFixed(1)} min`;
  waitNote.textContent = waitMinutes >= 16 ? "Intervention needed" : waitMinutes >= 11 ? "Manageable pressure" : "Queues stabilizing";

  densityZoneCount.textContent = String(hotspotCount);
  densityNote.textContent = `${formatPriority(payload.dispatcher_move.priority_level)} response`;

  systemStatusText.textContent = status.label;
  systemStatusNote.textContent = status.note;
  heroMode.textContent = status.banner;
}

function addBubble(kind, speaker, message, label) {
  const bubble = document.createElement("article");
  bubble.className = `bubble ${kind}`;
  bubble.innerHTML = `
    <div class="bubble-meta">
      <span>${escapeHtml(speaker)}</span>
      <span>${escapeHtml(label)}</span>
    </div>
    <div>${escapeHtml(message).replace(/\n/g, "<br />")}</div>
  `;
  transcript.appendChild(bubble);
  transcript.scrollTop = transcript.scrollHeight;
}

function renderList(items) {
  if (!items || !items.length) {
    return '<p class="muted">None</p>';
  }

  return `<ul class="bullet-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function extractWaitMinutes(text) {
  const match = String(text).match(/(\d+(?:\.\d+)?)\s*(?:min|mins|minute|minutes)\b/i);
  return match ? Number(match[1]) : null;
}

function derivedWaitMinutes(score) {
  return Math.max(6.5, Math.min(24.5, 24 - score * 1.45));
}

function estimateHotspotCount(payload) {
  const riskCount = payload.scorecard.flagged_risks.length;
  const baseCount = payload.dispatcher_move.priority_level === "critical" ? 4 : payload.dispatcher_move.priority_level === "high" ? 3 : 2;
  return Math.max(1, Math.min(5, Math.max(baseCount, riskCount + 1)));
}

function baselineWaitForPriority(priority) {
  const map = {
    balanced: 12.4,
    crowd_flow: 14.1,
    wait_times: 10.8,
    accessibility: 9.6,
    premium_service: 8.4,
  };
  return map[priority] ?? 12.4;
}

function statusFromOverall(overall, priorityLevel) {
  if (priorityLevel === "critical" || overall < 48) {
    return {
      label: "CRITICAL",
      note: "Immediate intervention required",
      banner: "Critical Response",
    };
  }

  if (priorityLevel === "high" || overall < 66) {
    return {
      label: "MONITORING",
      note: "Load is rising across the venue",
      banner: "Load Rising",
    };
  }

  if (overall < 82) {
    return {
      label: "ACTIVE",
      note: "System adapting in real time",
      banner: "System Active",
    };
  }

  return {
    label: "OPTIMAL",
    note: "Flow and experience are holding steady",
    banner: "System Active",
  };
}

function formatAttendance(value) {
  return Number(value).toLocaleString();
}

function formatPriority(value) {
  return String(value)
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function updateClock() {
  const now = new Date();
  dashboardClock.textContent = now.toLocaleTimeString("en-GB", { hour12: false });
}

startForm.addEventListener("submit", (event) => {
  event.preventDefault();

  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }

  const knownFriction = document.getElementById("known-friction").value.trim();
  socket.send(
    JSON.stringify({
      type: "start_session",
      payload: {
        venue_name: document.getElementById("venue-name").value.trim(),
        event_name: document.getElementById("event-name").value.trim(),
        expected_attendance: Number(document.getElementById("expected-attendance").value),
        priority: document.getElementById("priority").value,
        round_limit: Number(document.getElementById("round-limit").value),
        context: knownFriction ? { known_friction: knownFriction } : {},
      },
    }),
  );
});

updateForm.addEventListener("submit", (event) => {
  event.preventDefault();

  if (!sessionStarted || !socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }

  const updateInput = document.getElementById("update");
  const update = updateInput.value.trim();
  if (!update) {
    return;
  }

  addBubble("operator", "Ops Lead", update, "Field Update");
  socket.send(
    JSON.stringify({
      type: "submit_update",
      payload: {
        update,
      },
    }),
  );
  updateInput.value = "";
});

runSimShortcut?.addEventListener("click", () => {
  if (!sessionStarted) {
    startForm.requestSubmit();
    return;
  }

  const updateInput = document.getElementById("update");
  updateInput.scrollIntoView({ behavior: "smooth", block: "center" });
  updateInput.focus();
});

presetButtons.forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById("venue-name").value = button.dataset.venue || "";
    document.getElementById("event-name").value = button.dataset.event || "";
    document.getElementById("expected-attendance").value = button.dataset.attendance || "";
    document.getElementById("priority").value = button.dataset.priority || "balanced";
    document.getElementById("known-friction").value = button.dataset.context || "";
  });
});

updateClock();
window.setInterval(updateClock, 1000);
connectSocket();
