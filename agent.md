# agent.md — Campus Copilot Agent Architecture

This file describes how the AI agent(s) in Campus Copilot work. Use this as context when generating code with Gemma (or any coding assistant) so generated code matches the intended architecture.

## Model & Runtime

- **Model:** Gemma 4 12B QAT
- **Served via:** LM Studio local server (OpenAI-compatible API)
- **Endpoint:** `http://<server-laptop-ip>:1234/v1/chat/completions`
- **Server machine:** the gaming laptop (has the GPU). All other devices (2nd laptop, phones) connect to this IP over the same WiFi/hotspot.
- **No cloud calls, no API keys, no internet dependency at runtime.**

## Core Pattern: Plan → Act → Observe → Replan

Every agent in this app is the *same* loop, reused with different system prompts and inputs. There is no separate "model" per agent — just different prompts against the same local Gemma instance.

### 1. Planner Agent
**Purpose:** Build a structured weekly/daily agenda from timetable + deadlines + campus events + mess menu.

**Inputs:** timetable JSON, assignment deadlines JSON, campus events JSON, mess menu JSON

**System prompt (draft):**
```
You are a campus planning agent for a VIT Chennai student.
Given their timetable, deadlines, campus events, and mess menu,
produce a day-by-day plan for the week.

Rules:
- Respond ONLY with valid JSON, no markdown fences, no explanation.
- Schema: [{ "day": "", "items": [{ "time": "", "type": "class|deadline|event|meal|study", "label": "" }] }]
- Prioritize academic commitments over optional events.
- Flag conflicts explicitly with type "conflict".
```

### 2. Replanner Agent
**Purpose:** Adjust the remaining week's plan when the user reports a miss.

**Trigger:** user says "I missed X" or "I couldn't do Y"

**System prompt (draft):**
```
You are the same campus planning agent. The student missed the
following planned item: {missed_item}. Given the original plan
and this miss, regenerate only the remaining (future) days' plan,
redistributing any pending work reasonably. Respond ONLY with
valid JSON in the same schema as before.
```

### 3. Negotiator Agents (multi-agent)
**Purpose:** Find a common study-group time slot across 2-3 teammates.

**Design:** Each "teammate agent" is a separate call to the same local Gemma with a different system prompt containing that teammate's mock calendar. A coordinator prompt reconciles proposals.

**Round cap:** 3 rounds max (avoid open-ended negotiation loops — both for demo time and inference cost).

**Teammate agent system prompt (draft):**
```
You represent {teammate_name}'s calendar: {calendar_json}.
Given a proposed study slot, respond with ACCEPT or PROPOSE
an alternative from your free slots. Respond ONLY with JSON:
{ "response": "accept|propose", "slot": "" }
```

**Coordinator system prompt (draft):**
```
You are coordinating a study group of {n} students. You have
{n} responses to a proposed slot: {responses_json}. If all
accept, finalize. Otherwise pick the most-proposed alternative
and re-propose. Respond ONLY with JSON:
{ "status": "finalized|reproposing", "slot": "", "round": n }
```

**Log every round's transcript** — this is the demo centerpiece, so store `[{round, agent, message}]` for display in the UI.

### 4. Data Extraction Agent (one-time, not live)
**Purpose:** Convert the VTOP timetable PDF text and mess menu image into structured JSON. Run once during data prep, cache the output — do not depend on this working live during judging.

- Timetable: PDF text → Gemma (text-only) → JSON (see extraction prompt already validated against the sample PDF)
- Mess menu: image → Gemma (multimodal) → JSON. Cache the result; optionally re-run live once as a demo flourish.

## Error Handling (required, not optional)

- Every Gemma call must strip possible ` ```json ` fences before `JSON.parse`
- Wrap every parse in try/catch with a fallback to the last known-good cached plan
- Cap negotiation rounds at 3 — if no consensus, present the closest option instead of looping
- Log raw model output on parse failure for debugging during the hackathon

## API Call Template

```javascript
async function callGemma(systemPrompt, userPrompt) {
  const response = await fetch("http://<server-ip>:1234/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "gemma-4-12b-qat",
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt }
      ],
      temperature: 0.7
    })
  });
  const data = await response.json();
  const raw = data.choices[0].message.content;
  const clean = raw.replace(/```json|```/g, "").trim();
  try {
    return JSON.parse(clean);
  } catch (e) {
    console.error("Parse failed, raw output:", raw);
    return null; // caller falls back to cached state
  }
}
```
