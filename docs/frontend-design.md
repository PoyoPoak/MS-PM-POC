# Frontend Design Form

Refer to this form when designing a new frontend surface. It guides you through the key design decisions and documentation needed to create a distinctive, production-grade frontend interface that meets user needs and product goals. Fill out each section with as much detail as possible to ensure a clear design direction for implementation.

## Scope

This document is for frontend design only.

- In scope: layout, visual design, components, content structure, interactions, states, accessibility, responsiveness, and design system decisions
- Out of scope: backend integration, API contracts, authentication flows, route implementation, database behavior, and production deployment concerns

---

## 1. Project Context

### 1.1 Feature or Surface Name

- Feature/page/component name: App Dashboard

### 1.2 Purpose

- What is this frontend surface supposed to help the user do? See a list of patients, view key metrics, manage models, and monitor system health.
- What problem does it solve? Visibility and control over patient data, model management, and system health monitoring.
- Why does it matter in the product? To provide a central hub for users to access critical information and perform key actions efficiently.

### 1.3 Audience

- Primary user type: Healthcare professionals, data scientists, and system administrators.
- User skill level: Non-technical users.
- Accessibility or usability needs already known: Light theme, hospital environment, quick access to critical information, and clear visual hierarchy. Simple/POC design with minimal interactions. Should not be so basic as to looking like an AI generated it. Should look like a real product and be aesthetically simple and professional.

### 1.4 Success Criteria

- What would make this frontend feel successful? Users can quickly identify key information, table is easy to scan, and primary actions are intuitive.
- What should users be able to understand in the first 5 seconds? What the active machine learning model is and its metrics, the list of patients and their status, the ability to train a new model and deploy it or refresh to run inference.
- What should users be able to complete without help? Everything.

---

## 2. Design Direction

### 2.1 Visual Direction

- Choose a design tone:
	- Minimal and clinical
	- Editorial and information-dense
	- Technical yet simple.
	- Premium and polished
	- Warm and approachable
- Describe the intended visual personality in 3 to 5 adjectives: Clinical, simple, clear, efficient, trustworthy.
- What should this UI definitely not look like? Techy, playful, complicated.

### 2.2 Brand and Mood

- Emotional tone for the user: Reassuring, professional, efficient, trustworthy.
- Confidence level the UI should project: High
- Should the design feel more operational, medical, analytical, or consumer-like? Medical and operational.

### 2.3 Inspiration

- Reference products, apps, or design systems: MyChart, Tableau, and other healthcare dashboards.
- Specific elements worth borrowing: Color themes, clear typography, and simple data presentation.
- Specific elements to avoid: Complexity and unnecessary visual embellishments.

---

## 3. Information Architecture

### 3.1 Surface Type

- What is being designed?
	- Dashboard, the actual page itself, keep the components within the current page simple and focused on the core content, but the overall page will have multiple components to show different types of information and actions.
    - Quick Stats component cards, showing key metrics like total patients, number of patients at risk, last update time, and alerts sent out(placeholder metrics for now). These will be above the list view component, arranged in a row of 4 cards in the second column.
	- List view component, showing a list of patients (patientid, risk score, lead impedance, capture threshold, battery voltage, last update). These will be arranged in the second column, below the quick stats cards, and will be the most prominent component on the page. The list should be sortable by each column, and filterable by risk score and alerts sent out. Default sort is by risk score. Add a search bar to search by patient id. Paginated.
	- Model Management component, below the Active Model component in the left column, with buttons to train a new model, run inference, and upload model. Below the buttons will be a list of the recent 3 models with their training date, and f1 score. Beside each will be a button to deploy that model which will trigger a confirmation modal to apply and rerun inference.
	- Active Model component, arranged at the top of the left column, showing details as to the model version, training date, and dataset size. Below it will be a 2x2 grid of 4 summary cards showing accuracy, precision, recall, and f1 score. Below will also be a row card of the OOB score.
	- Left Nav Bar component, keep the same nav bar, add placeholder tabs for other potential windows.
	- Footer bar component, keep the same footer bar, replace the Full Stack FastAPI text with the app name, remove the social links on the right, replace it with the repo link and a updating commit hash.

### 3.2 Content Hierarchy

- Primary content block: List view component, as this is the core of the page and the most important information for users to see. It should be the most prominent and take up the most space on the page.
- Secondary content block: Active Model component, as it provides important context about the current model and its performance metrics, but is not the main focus of the page.
- Supporting content block: Model Management component, as it provides important functionality for managing models, but is not critical for users to see at all times. It can be placed below the Active Model component and should be easily accessible when needed.
- What information must always stay visible? Everything, but especially the list view component and the active model component, as they provide critical information about patients and the current model.
- What information can be collapsed, hidden, or deferred? None.

### 3.3 Page Structure

- Header needed: yes, use the existing header, but update it.
- Sidebar needed: yes, use the existing left nav bar, but updated it as said.
- Filters/search needed: yes, for the list view component.
- Main content zones: two columns, with the left column containing the Active Model component at the top and the Model Management component below it, and the right column containing the Quick Stats component cards at the top and the List View component below it. In mobile, the layout will collapse into a single column with the quick stats cards at the top, followed by the active model component, then the model management component, and finally the list view component.
- Footer actions: none, but the footer will be updated as said in the left nav bar component section.

### 3.4 Navigation Within the Surface

- Internal sections or tabs: none, but the left nav bar will have placeholder tabs for other potential windows.
- Anchors or stepper needed: none.
- Prev/next flow needed: no, this is a dashboard and not a multi-step process.
- Should this surface stand alone or feel part of a larger workspace? Standalone for now, but it should feel like it could be part of a larger healthcare management system in the future.

---

## 4. Layout Planning

### 4.1 Desktop Layout

- Target desktop width assumptions:
- Preferred layout pattern:
	- Two column, with the left column containing the Active Model component at the top and the Model Management component below it, and the right column containing the Quick Stats component cards at the top and the List View component below it. In mobile, the layout will collapse into a single column with the quick stats cards at the top, followed by the active model component, then the model management component, and finally the list view component.
- Desired density:
	- Balanced

### 4.2 Tablet Layout

- What changes on medium screens? The layout will collapse into a single column, with the quick stats cards at the top, followed by the patient list, then the active model component, and finally the model management component. The left nav bar will collapse into a hamburger menu.
- Which sections stack? The quick stats cards will stack vertically and be more compact, and the patient list will take up the full width below them. The active model component and model management component will also stack vertically below the patient list.


### 4.4 Spatial Priorities

- Where should visual weight go first?
- Which sections deserve the most space? List view component, as it contains the most critical information for users to see and interact with.
- Which sections can shrink without harming comprehension? List view but only vertically.

---

## 5. Content and Messaging

### 5.1 Headings and Labels

- Preferred tone for headings:
- Preferred tone for helper text:
- Should labels be formal, clinical, technical, or plain language?

### 5.2 Empty and Placeholder Content

- What should users see before data exists?
- Should empty states teach, reassure, or push an action?
- What placeholders or skeletons are appropriate?

### 5.3 Microcopy

- Confirmation language style:
- Error language style:
- Call-to-action tone:
- Tooltip tone:

### 5.4 Content Constraints

- Longest expected labels:
- Longest expected values:
- Any medical or regulated language constraints:
- Terms that must be used exactly:

---

## 6. Components Inventory

List the components needed for this frontend surface.

| Component | Purpose | Priority | Notes |
|---|---|---|---|
| Example: summary card | Show key metric | High | Large value, short label |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

### 6.1 Required UI Patterns

Mark all that apply.

- Cards
- Data table
- Search input
- Filter bar
- Tabs
- Accordion
- Badge/status pill
- Chart or graph
- Toast/notification
- Inline validation
- Pagination
- Etc.


## 7. Interaction Design

### 7.1 Primary Actions


### 7.2 Interaction Model

- Should actions happen inline, in a modal, in a drawer, or on a dedicated screen?
- Should advanced options stay hidden by default?
- Should interactions feel fast/minimal or guided/explicit?

### 7.3 Feedback

- What should happen after a successful action?
- What should happen after a failed action? For each action possible, when an error occurs show a toast notification with the error message and a link to retry the action. For example, if an error occurs when trying to deploy a model, show a toast notification that says "Failed to deploy model. Please try again." with a "Retry" button that triggers the deploy action again.


## 9. Data Presentation

Complete this section if the frontend includes metrics, tables, charts, logs, or analytical view. To whatever extent is suited to the project, describe the data presentation needs and decisions.

### 9.1 Data Density

- Should the UI favor scanability or depth? Scannability, as users need to quickly identify key information and take action.
- Is this more operational monitoring or analytical review? Operational monitoring, as users need to quickly identify patients at risk and take action, rather than performing deep analysis.

### 9.2 Tables and Lists

- Key columns or fields:
- Sorting needed: yes
- What urgency levels exist? Yes, use colors and badges to indicate risk levels for patients.

---

### 10.1 Color Strategy

- Retain the same color palette as the existing design system.

### 10.2 Typography

- Retain the same typography as the existing design system.

### 10.3 Shape and Surfaces

- Retain the same shape and surface styles as the existing design system, but use cards to create clear separation between different sections of the page and to highlight key information. Additionally, any design changes made must be reflected in the design system for consistency across the product.

### 10.4 Iconography and Illustration

- Icon style:
	- Minimal
	- Clean
    - Simple
- Illustrations needed: yes, use simple icons to represent different sections of the page to improve aesthetics and help users quickly identify different areas of the dashboard. For example, use a cpu icon for the Active Model component, a exclaimation icon for the List View component, and a settings icon for the Model Management component.
- Decorative visuals needed: yes

---

## 11. Motion and Attention

### 11.1 Motion Principles

- Should the interface feel calm, clean, smooth
- How much motion is appropriate? Use motion but keep it minimal and purposeful, to draw attention to key information and actions without overwhelming the user. Avoid using motion for purely decorative purposes, and ensure that all motion can be disabled for users who prefer reduced motion.

### 11.2 Motion Inventory

- Page-load transitions:
- Hover effects: Buttons should have a subtle hover effect to indicate interactivity, such as a slight increase in brightness or a shadow effect.
- Loading placeholders: For the list view component, use skeleton loading placeholders to indicate that data is being loaded and to improve perceived performance.
- Expand/collapse transitions: For the list view component.
- Feedback animations: For example, when a user deploys a model, show a brief success animation on the Active Model component to indicate that the new model is now active.

---



---

### 13.1 Accessibility Targets

- Required accessibility level: None, POC



---

## 14. Responsiveness and Device Behavior

### 14.1 Breakpoint Priorities

- Breakpoints that matter most:
- Which experience must be highest quality first:
	- Desktop, keep it responsive, but the main focus is desktop for this POC.

### 14.2 Device-Specific Behavior

- Touch target considerations:
- Hover-only interactions that need touch alternatives:
- Sticky controls on small screens:
- Horizontal scroll tolerance:

---

## 15. Design System Alignment

### 15.1 Existing System Usage

- Which existing UI primitives should be reused? Refer to the README in ./frontend
- Which new component patterns may be needed? Cards, data table, search input, filter bar, tabs, badge/status pill, pagination, etc. React components for these will need to be created and added to the design system for consistency across the product.
- Which existing styles should be preserved? The existing one.

### 15.3 Consistency Rules

- What must stay consistent across all frontend surfaces? Once finished with the dashboard, I will later instruct you to update the login page.

---

## 16. Constraints and Non-Goals

### 16.1 Technical Constraints

- Browser/device constraints:
- Performance constraints:
- Library/component constraints:
- Asset constraints:

### 16.2 Explicit Non-Goals

- What should not be designed right now? Backend. Focus on frontend and the design and user experience. I will later connect backend.

---

## 17. Acceptance Criteria for Frontend Design

The frontend design will be considered sufficiently defined when the following are complete.

- Visual direction is clear and specific
- Layout decisions exist for desktop, tablet, and mobile
- Core content hierarchy is defined
- Required components are listed
- Primary interactions and states are documented
- Form behavior is documented if forms exist
- Accessibility expectations are documented
- Design system alignment is documented
- Non-goals are explicit
- Open questions are captured

Add project-specific acceptance criteria below.

-
-
-

---

## 18. Open Questions

-
-
-

---

## 19. Final Design Summary

Write a short summary after completing the form.

### 19.1 One-Paragraph Summary

- Summary:

### 19.2 Implementation Intent

- What should be built first on the frontend?
- What should be prototyped before full implementation?
- What design risks need validation early?

### 19.3 Sign-Off

- Prepared by:
- Reviewed by:
- Approved direction:

---

## 20. Ready-to-Use Frontend Agent Prompt

Use the prompt below with a frontend AI coding agent.

```text
Build the App Dashboard frontend for this project using the existing frontend stack and design system.

Important scope constraints:
- Frontend only.
- Do not hook up backend APIs.
- Do not add or change backend code.
- Do not create new app routes.
- Work within the existing dashboard page/surface and existing layout shell.

Goal:
Create a production-looking, simple, clinical, trustworthy dashboard UI that feels like a real healthcare product (not generic AI-looking), optimized for quick scanning and operational monitoring.

Target users:
- Healthcare professionals
- Data scientists
- System administrators
- Assume non-technical users

Visual direction:
- Medical + operational tone
- Simple, clear, efficient, professional
- Light theme
- Keep existing design system palette/typography/style foundations
- Minimal, purposeful motion only
- Avoid playful, overly techy, or visually noisy styling

Page composition (single dashboard surface):
1. Left column:
	 - Active Model component (top)
	 - Model Management component (below)

2. Right column:
	 - Quick Stats row (4 cards) at top
	 - Patient List table (main focus) below

3. Keep and update existing shell pieces:
	 - Header: keep existing, update content/styling as needed
	 - Left nav: keep existing, add placeholder tabs for future sections
	 - Footer: keep existing structure, replace "Full Stack FastAPI" text with app name, remove social links, add repo link and updating commit hash display

Detailed component requirements:

A) Quick Stats (4 cards)
- Placeholder values are fine
- Show:
	- Total patients
	- Patients at risk
	- Last update time
	- Alerts sent

B) Patient List (most prominent block)
- Columns:
	- patientId
	- risk score
	- lead impedance
	- capture threshold
	- battery voltage
	- last update
- Features:
	- sortable by each column
	- default sort by risk score
	- filter by risk score and alerts sent
	- search by patientId
	- pagination
- Add risk-level visual treatment (color/badge urgency cues)
- Use skeleton loading placeholders for table loading state

C) Active Model
- Show:
	- model version
	- training date
	- dataset size
- Metrics grid (2x2 cards):
	- accuracy
	- precision
	- recall
	- f1 score
- Additional row card for OOB score

D) Model Management
- Primary actions:
	- Train new model
	- Run inference
	- Upload model
- Show recent 3 models with:
	- training date
	- f1 score
- Each recent model has Deploy button
- Deploy action must open confirmation modal and then indicate rerun inference intent in UI state/messaging

Interaction and feedback requirements:
- Keep interactions minimal and intuitive
- Show toast notifications for errors with retry action where appropriate
- Example: deploy failure toast with retry CTA
- Include success feedback for major actions (subtle, not flashy)
- Button hover states should be subtle and professional
- Add reduced-motion-safe behavior for all non-essential animations

Responsive behavior:
- Desktop is primary target
- Tablet/mobile collapse into single column
- On smaller screens, stack in this order:
	1) Quick Stats
	2) Active Model
	3) Model Management
	4) Patient List
- Collapse left nav into hamburger pattern on medium/small screens

Accessibility and UX constraints:
- POC-level accessibility is acceptable, but keep keyboard/focus behavior sane
- Ensure clear visual hierarchy and fast scanability
- Do not overcomplicate interactions

Implementation guidance:
- Reuse existing primitives/components where possible
- Add new reusable dashboard components where needed
- Keep code clean and modular
- Use mock/local placeholder data only for now
- No backend wiring

Expected output:
1. Updated dashboard UI implementation in the existing frontend surface
2. New/updated reusable components for cards, patient table controls, model panels, and status badges
3. Updated header/nav/footer content per requirements
4. Clear loading, empty, and error visual states for key areas
5. Brief implementation summary of what was created and any assumptions
```
