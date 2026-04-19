const socketStatus = document.getElementById("socket-status");
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
const presetButtons = document.querySelectorAll(".preset-btn");

let socket;
let sessionStarted = false;
let currentRoundLimit = 0;

function connectSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/ws/operations`);

  socket.addEventListener("open", () => {
    socketStatus.textContent = "Connected";
    socketStatus.classList.add("connected");
  });

  socket.addEventListener("close", () => {
    socketStatus.textContent = "Offline";
    socketStatus.classList.remove("connected");
    submitUpdateButton.disabled = true;
    sessionStarted = false;
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
  heroMode.textContent = "Multi-Agent Venue Command Center";
  eventLabel.textContent = payload.event_name;
  attendanceLabel.textContent = formatAttendance(payload.expected_attendance);
  priorityLabel.textContent = formatPriority(payload.priority);
  transcript.innerHTML = "";
  resetAnalysis();
  addBubble("command", "AI Command", payload.opening_turn.message, "Kickoff");
  addBubble("broadcast", "Fan Broadcast", payload.strategy.fan_message, "Attendee Alert");
  roundChip.textContent = `Round 1 / ${payload.round_limit}`;
  sessionMeta.innerHTML = `
    <h3>Mission Brief</h3>
    <p><strong>North star:</strong> ${escapeHtml(payload.strategy.north_star)}</p>
    <p class="muted">Hotspot watchlist</p>
    ${renderList(payload.strategy.hotspot_watchlist)}
    <p class="muted">Quick wins</p>
    ${renderList(payload.strategy.quick_wins)}
    <p class="muted">Coordination focus</p>
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

  renderScores(payload.scorecard);
  analystFeedback.classList.remove("muted");
  analystFeedback.innerHTML = `
    <p><strong>Coaching tip:</strong> ${escapeHtml(payload.analyst_feedback.coaching_tip)}</p>
    <p><strong>Next move:</strong> ${escapeHtml(payload.analyst_feedback.next_move)}</p>
    <p class="muted">Wins</p>
    ${renderList(payload.analyst_feedback.wins)}
    <p class="muted">Risks</p>
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
    <p class="muted">Staff actions</p>
    ${renderList(payload.dispatcher_move.staff_actions)}
  `;

  experienceLens.classList.remove("muted");
  experienceLens.innerHTML = `
    <p>${escapeHtml(payload.experience_coach.experience_upgrade)}</p>
    <p><strong>Accessibility check:</strong> ${escapeHtml(payload.experience_coach.accessibility_check)}</p>
    <p class="muted">Blindspots</p>
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
  renderScores({ crowd_flow: 0, wait_time: 0, coordination: 0, fan_experience: 0, overall: 0 });
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

function renderScores(scorecard) {
  const cards = document.querySelectorAll(".score-card");
  const values = [
    scorecard.crowd_flow,
    scorecard.wait_time,
    scorecard.coordination,
    scorecard.fan_experience,
    scorecard.overall,
  ];

  cards.forEach((card, index) => {
    card.querySelector(".score-value").textContent = values[index];
    const span = card.querySelector(".score-bar span");
    const max = index === 4 ? 100 : 10;
    span.style.width = `${(values[index] / max) * 100}%`;
  });
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

  return `<ul class="bullet-list">${items
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("")}</ul>`;
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

presetButtons.forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById("venue-name").value = button.dataset.venue || "";
    document.getElementById("event-name").value = button.dataset.event || "";
    document.getElementById("expected-attendance").value = button.dataset.attendance || "";
    document.getElementById("priority").value = button.dataset.priority || "balanced";
    document.getElementById("known-friction").value = button.dataset.context || "";
  });
});

connectSocket();
