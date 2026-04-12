# UI Redesign Design

Date: 2026-04-13
Topic: Flask web UI redesign for DermAI
Status: Approved for planning

## Goal

Redesign the current Flask frontend so it feels cleaner, more trustworthy, and more visually polished while staying appropriate for a medical-adjacent academic demo. The new UI should be light mode by default, support dark mode, and guide users through a clearer 3-step flow: upload, review, and results.

## Context

The current interface is implemented in:

- `web/templates/index.html`
- `web/static/css/style.css`
- `web/static/js/main.js`

The existing page already supports file upload, prediction, error handling, loading state, and results rendering. The redesign should preserve those behaviors while changing the information architecture, visual system, and component presentation.

## Users

Primary audience:

- General users who need a simple and reassuring interface
- Lecturers and students using the project as an academic demo or presentation artifact

The UI must be understandable to non-technical users but polished enough to present in class or demos.

## Design Direction

### Recommended Direction

Clinical guided workflow.

This direction prioritizes clarity, trust, and step-by-step interaction over flashy presentation. It fits the academic-medical context better than a marketing-heavy landing page or a stripped diagnostic console.

### Visual Style

- Light mode is the default
- Dark mode is available through a theme toggle
- Both themes share the same layout and hierarchy
- The palette should move away from neon gradients, purple-heavy accents, and glassmorphism
- The interface should use soft medical tones such as warm white, muted blue, muted green, and restrained alert colors
- Surfaces should feel crisp and layered with subtle borders and soft shadows
- Motion should be minimal and deliberate

### Visual Mood

The page should feel:

- precise
- calm
- modern
- academically credible

## Experience Structure

The redesigned page should shift from the current two-column tool layout into a guided single-page flow with explicit steps.

### Step 1: Upload

The first primary action is image upload. This section should include:

- a prominent upload card
- drag-and-drop support
- browse action
- accepted file formats and max size
- short guidance copy for what kind of image to upload

### Step 2: Review

After an image is selected, the interface should transition into a review state that includes:

- larger image preview
- file name and file size
- replace image action
- remove image action
- primary analyze action

This review step makes the flow feel intentional and helps users confirm they selected the correct image before inference runs.

### Step 3: Results

After analysis, the result view should appear as a dedicated step with clear hierarchy:

- predicted class
- confidence
- risk level
- plain-language explanation
- recommended next action
- full class probability breakdown

The main diagnosis and guidance should appear before secondary probability details.

### Supporting Content

Below the main tool flow, keep compact supporting sections:

- a reference section for the 7 lesion classes
- a trust/disclaimer section stating the app is for research and learning use only

These sections should support presentations without distracting from the primary workflow.

## Layout

### Header

Replace the current dark, badge-heavy navbar with a cleaner clinical header that includes:

- brand
- model/server status
- theme toggle

The current beta badge is not part of this redesign.

### Hero

The hero should become shorter and more functional. It should:

- explain the tool clearly
- reinforce the academic-medical tone
- lead directly into the upload step

It should not dominate the page like a marketing banner.

### Main Tool Section

The analyzer should be presented as sequential cards or panels representing the current step rather than a fixed left-right split. On desktop, this may still use some horizontal alignment where useful, but the experience should read as one guided flow instead of two independent columns.

### Mobile

On mobile, all steps should stack naturally into full-width cards with comfortable spacing. No side-by-side panels should be required on small screens.

## Components

### Upload Card

States:

- empty
- file selected
- processing
- inline error

Behavior:

- The empty state emphasizes upload guidance
- The selected state shows preview and file details
- The processing state replaces the previous dramatic loader with a calmer clinical loading panel
- Validation errors should appear inline within the workflow

### Results Card

The results area should prioritize comprehension and trust.

The top result block should show:

- diagnosis code or name
- human-readable class name
- confidence
- risk badge and short risk explanation

Secondary blocks should show:

- description
- recommendation
- probability comparison across all classes

High-risk results should be visually prominent but not alarmist. Avoid pulsing danger effects and excessive glow.

### Class Reference Cards

Keep the existing educational/reference section for the 7 lesion classes, but redesign cards to be cleaner and more consistent with the new theme. The section should remain scannable and compact.

### Trust Section

Replace the current small warning box with a clearer trust/disclaimer section that states:

- the app is for research and learning use only
- predictions do not replace dermatologist diagnosis

## Typography

Use a more intentional type system than a single generic UI font everywhere.

Requirements:

- professional and readable body text
- more expressive but restrained headings
- clear hierarchy between section titles, labels, body copy, and result emphasis

The typography should support a medical-academic aesthetic rather than a startup-neon aesthetic.

## Theme Behavior

- Light mode is the default theme
- Dark mode is available through a toggle in the header
- The selected theme should persist in local storage
- Dark mode should preserve the same personality and hierarchy as light mode
- Dark mode should feel muted and professional, not flashy

## Motion

Allowed motion:

- short fade transitions
- slight upward movement for state changes
- subtle hover feedback

Disallowed motion:

- dramatic loading effects
- repeated pulsing alert animations
- flashy hero effects

Motion should support orientation and polish, not spectacle.

## Accessibility

The redesign should improve:

- color contrast in both themes
- keyboard focus visibility
- readable spacing and sizing
- button and control clarity
- predictable behavior across upload, review, error, and result states

Risk states should not rely on color alone. Text labels must remain clear.

## Error Handling

Preserve the current validation rules and error scenarios while integrating them more cleanly into the guided workflow.

Required handling:

- unsupported file type
- file too large
- missing file
- backend/server connection issues
- model unavailable
- inference failure

Errors should be shown inline with direct, human-readable guidance.

## Data Flow and Behavioral Boundaries

The redesign is presentation-focused. It should not change the prediction API contract unless required for purely presentational reasons. Existing backend behavior should remain compatible with the frontend.

Frontend responsibilities:

- manage step transitions
- render upload/review/results states
- persist theme preference
- display validation and server errors

Backend responsibilities remain unchanged:

- health check
- image validation already enforced server-side
- prediction response generation

## Implementation Scope

In scope:

- redesign `index.html` structure
- redesign `style.css` visual system
- update `main.js` to support guided steps, theme toggle, and revised state rendering
- preserve current upload and prediction behavior

Out of scope:

- model retraining
- prediction logic changes
- backend API redesign
- authentication or user accounts
- storing prediction history

## Verification

Minimum verification for implementation:

- `python -m compileall src web`
- manual smoke test through `python web/app.py`

Manual validation should cover:

- light theme default
- dark theme toggle and persistence
- upload flow
- review state
- loading state
- success results rendering
- high-risk result presentation
- inline error presentation
- mobile layout check

## Risks

- Over-designing the page could reduce trust or distract from the medical purpose
- Theme toggle work can introduce inconsistent styling if the token system is not centralized
- Reworking the layout without preserving current JS state logic can break upload or result rendering

## Recommended Implementation Strategy

1. Rework the HTML structure around a guided 3-step flow
2. Introduce theme tokens and implement light mode first
3. Add dark mode token overrides and persistence
4. Update JS state management to map onto the new step-based UI
5. Refine educational and trust sections
6. Run syntax and manual smoke validation

## Scope Check

This design is focused enough for a single implementation plan. It is a frontend redesign with limited behavioral additions and no backend contract changes.
