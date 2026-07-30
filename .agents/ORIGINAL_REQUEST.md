# Original User Request

## 2026-07-30T10:01:06Z

An autonomous Campus Copilot (ICHIKA) student scheduler web application for VIT Chennai students. The system integrates a student's timetable, deadlines, events, and mess menu to maintain a clean daily agenda, handle schedule re-alignment when items are missed, and coordinate study sessions via multi-agent negotiation.

Working directory: c:/Users/Nileshkumar/Downloads/files
Integrity mode: demo

## References
- Custom UI Layout Reference Image: [thumbnail.jpeg](file:///C:/Users/Nileshkumar/.gemini/antigravity/brain/c6d2b3f9-ec75-4e49-a251-c6c1df6b085c/thumbnail.jpeg)

## Requirements

### R1. Student Profile & Timetable Import
The system must parse VTOP student timetables (supporting both PDF and MHTML formats) and deadlines, storing them in isolated, student-specific JSON configurations. It must support multiple active student registration numbers (e.g., `26BEC1185` and `26BLC1265`).

### R2. Visual Design & Interface
The user interface must match the custom visual layout specified in the reference image ([thumbnail.jpeg](file:///C:/Users/Nileshkumar/.gemini/antigravity/brain/c6d2b3f9-ec75-4e49-a251-c6c1df6b085c/thumbnail.jpeg)). It must use a high-contrast institutional theme (Prussian Blue `#002147`, Gold `#FFA500`, and Charcoal text on a light background) without decorative AI buzzwords or emoji clutter.

### R3. Weekly Agenda & Smart Replanner
An autonomous agent must merge course slots, meals, events, and academic deadlines into a clean day-by-day timetable grid. If a student misses a course, the Replanner agent must mark it visually and reschedule tasks into remaining free slots later in the week.

### R4. Multi-Agent Group Negotiator
The system must run an autonomous negotiation protocol where agent representations of teammates (e.g., Aarav, Ananya, Rohan) coordinate schedules over a maximum of 3 rounds to select a consensus study slot. It must output the final agreed slot and a step-by-step transaction log.

## Acceptance Criteria

### Verification Target
- [ ] Backend API compilation and test suite passes 100% check.
- [ ] Schedule tables are rendered with high-contrast text and explicit borders matching the layout references.
- [ ] Dropdown options and sidebar controls have high contrast with no overlapping or invisible text.
- [ ] PDF/MHTML CLI extraction script successfully executes and produces schema-validated student timetables.

## 2026-07-30T10:09:13Z

Please resume execution. The user has confirmed the custom layout reference image is located at "C:\Users\Nileshkumar\Downloads\thumbnail.jpeg". Use this reference to guide the UI alignment for the Campus Copilot dashboard.

