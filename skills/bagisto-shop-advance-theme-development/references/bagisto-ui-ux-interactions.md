# Bagisto UI/UX interaction craft

## Contents

- [Decide whether motion belongs](#decide-whether-motion-belongs)
- [Choose motion by purpose](#choose-motion-by-purpose)
- [Use a compact timing system](#use-a-compact-timing-system)
- [Make controls feel immediate](#make-controls-feel-immediate)
- [Handle overlays and disclosure](#handle-overlays-and-disclosure)
- [Animate lists and commerce feedback](#animate-lists-and-commerce-feedback)
- [Protect performance](#protect-performance)
- [Protect accessibility](#protect-accessibility)
- [Apply Bagisto-specific constraints](#apply-bagisto-specific-constraints)
- [Review interaction quality](#review-interaction-quality)

Read this reference when a theme adds or changes transitions, drawers, menus, dialogs, tabs, accordions, filters, product media, cart feedback, loading states, or campaign motion. Use installed Bagisto behavior first; this document refines presentation and interaction without replacing commerce state.

## Decide whether motion belongs

Evaluate frequency before adding motion:

| Customer exposure | Default decision |
|---|---|
| Constant or repeated navigation, typing, quantity changes | Immediate response; no decorative entrance |
| Frequent hover, filter, option, and card actions | State transition only |
| Occasional drawer, dialog, toast, or accordion | Short spatial transition when it clarifies the relationship |
| Rare campaign, onboarding, or success moment | Restrained delight within performance and reduced-motion budgets |

Keyboard-triggered actions should respond immediately. Never make a power user wait for decorative choreography. Checkout, payment, validation, stock, option, and cart feedback always prioritize certainty over spectacle.

## Choose motion by purpose

Every animation must serve at least one purpose:

- show where an overlay or panel came from;
- connect two states of the same component;
- acknowledge an action;
- prevent a content replacement from feeling broken;
- explain a product feature or campaign idea;
- preserve spatial continuity after filtering or navigation.

If removing the motion does not reduce understanding or useful brand expression, remove it. Motion intensity is not a quality score.

Choose the simplest mechanism that works:

- colors, borders, and small state changes: CSS transition;
- enter/exit with known endpoints: CSS transition or supported starting state;
- rapidly reversible UI: interruptible transitions driven by installed component state;
- user-controlled drag: only when the installed runtime already supports robust pointer, touch, velocity, focus, and cancellation behavior;
- campaign sequence: CSS first; add JavaScript only with evidence that CSS cannot express the approved behavior.

## Use a compact timing system

Define a global rhythm instead of choosing durations per component:

| Role | Typical range | Use |
|---|---:|---|
| Fast | 90–140ms | press, color, border, tiny disclosure feedback |
| Standard | 160–240ms | menus, compact panels, option changes |
| Deliberate | 220–320ms | drawers, dialogs, selected campaign reveals |

Exit should normally finish sooner than entry. Entering movement should start decisively and settle; on-screen repositioning should accelerate and decelerate smoothly. Constant progress indicators may move linearly. Avoid a slow start for controls because it delays visible feedback.

Use named motion tokens for duration, easing, and distance. Keep campaign-only values separate from UI values. Avoid `transition: all`; name the properties that actually change.

## Make controls feel immediate

Buttons and pressable cards need visible active feedback without moving surrounding layout. A slight transform, color, or border change may be appropriate when it:

- does not reduce the touch target;
- does not make text blurry at rest;
- does not fire on disabled controls;
- is gated correctly for pointer and keyboard input; and
- remains subtle enough for repeated use.

Never introduce layout shift to signal hover or selection. Reserve border width or use inset treatments. Keep focus-visible distinct from hover and selected states. A selected option still needs an accessible programmatic state.

Do not animate an element from a dimensionless point. Entering controls should retain a believable shape and use small distance or scale changes with opacity only when required.

## Handle overlays and disclosure

Drawers, menus, dialogs, popovers, and accordions must preserve their installed behavior:

- open/closed ARIA state stays synchronized;
- focus moves to a useful target when appropriate;
- focus remains contained only for modal interactions;
- Escape and the installed close action work;
- focus returns to the initiating control;
- background scrolling and inertness follow the installed contract;
- the overlay remains usable without animation.

An anchored surface should visually relate to its trigger. A centered modal should remain centered. Keep transforms small; avoid long travel that makes the interface feel disconnected.

Do not animate accordion height with fragile fixed measurements. Use the installed component behavior or a measured, interruptible approach that handles dynamic and translated content.

## Animate lists and commerce feedback

Product grids, filters, cart lines, toasts, and search results can update rapidly. Preserve state truth first:

- keep the result count and active filters current;
- announce meaningful asynchronous changes;
- prevent duplicate submits;
- keep old and new content from becoming simultaneously actionable;
- retain or intentionally restore focus and scroll;
- make error recovery obvious.

Use skeletons only when loading is expected and their dimensions match final content. Avoid shimmering every region or showing a skeleton for an operation that resolves instantly. Reserve media ratios to prevent layout shift.

If a small list entrance is appropriate, keep any sequence short and never delay interaction until all items finish. Do not stagger long product grids; customers are scanning, not watching an intro.

Cart feedback must not invent optimistic totals or stock. Let Bagisto remain authoritative. A visual acknowledgement may begin immediately, but final state, price, quantity, errors, and mini-cart content must reflect the installed response.

## Protect performance

Prefer opacity and transform when motion is necessary. Avoid continuously animating layout, filters, large blurs, shadows, or full-page backgrounds. Measure paint and compositing cost on representative mobile hardware.

Do not update inherited CSS variables every frame on a large subtree. Change the narrowest element and property possible. Avoid scroll listeners that perform layout reads and writes on every event. Use installed browser and framework capabilities before considering another dependency.

Motion cannot hide a slow interaction. Improve the request, render path, image strategy, and JavaScript budget first. Preserve LCP stability, CLS, input responsiveness, and useful server-rendered content.

## Protect accessibility

Reduced motion is a separate composition, not a blanket afterthought:

- remove spatial travel, parallax, auto-rotation, and nonessential sequences;
- keep short opacity, color, or state feedback when it improves comprehension;
- make all content and actions available immediately;
- stop autoplay movement and expose controls where required.

Apply hover effects only when hover and a fine pointer are available. Touchscreens can retain a hover state after tapping, so never make essential information hover-only.

Animations must not flash, trap attention, block input, steal focus, or hide status announcements. Pause or stop controls are required when movement meets applicable accessibility thresholds.

## Apply Bagisto-specific constraints

Keep these areas intentionally conservative:

- search suggestions and navigation;
- product options, quantity, stock, and add-to-cart;
- wishlist and compare feedback;
- cart editing, coupon, shipping estimate, and totals;
- checkout address, shipping, payment, review, errors, and success;
- authentication, account actions, returns, downloads, and extension flows.

Express the highest motion dial only on selected merchant-managed campaign surfaces. Lower the effective motion dial on listing, product, cart, checkout, and account pages as generated by `bagisto-ui-ux`.

Do not replace Bagisto events, API calls, validation, or Vue component state to obtain a particular animation. Style the installed lifecycle. Preserve render events and extension output even when their timing or dimensions are unpredictable.

## Review interaction quality

Inspect interactions at normal speed, slowed down, reduced motion, keyboard-only, touch, and under CPU/network pressure. Use a concise issue table during review:

| Current behavior | Required behavior | Reason |
|---|---|---|
| Broad transition catches unrelated properties | Transition only the intended color, opacity, or transform | Prevent accidental motion and debugging ambiguity |
| Control starts slowly after input | Show immediate state feedback and settle quickly | Preserve perceived responsiveness |
| Hover reveals required action | Keep the action visible or keyboard/touch discoverable | Maintain input parity |
| Drawer closes but focus is lost | Return focus to its trigger | Preserve navigation context |
| Cart animation shows an assumed total | Render the authoritative response | Preserve commerce truth |
| Product grid waits for a long sequence | Render all results immediately; keep any reveal brief | Preserve scanning speed |

Reject polish that only works in an unloaded desktop demo. The final interaction must remain coherent with real data, slow requests, errors, extensions, touch, keyboard, RTL, and reduced motion.
