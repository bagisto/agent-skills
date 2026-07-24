# Bagisto UI/UX foundations

## Contents

- [Separate design from implementation](#separate-design-from-implementation)
- [Create the visual thesis](#create-the-visual-thesis)
- [Build recognizable signatures](#build-recognizable-signatures)
- [Control composition](#control-composition)
- [Engineer typography](#engineer-typography)
- [Engineer color and surfaces](#engineer-color-and-surfaces)
- [Direct imagery and icons](#direct-imagery-and-icons)
- [Create component anatomy](#create-component-anatomy)
- [Compose responsive behavior](#compose-responsive-behavior)
- [Translate the system into Bagisto](#translate-the-system-into-bagisto)
- [Run the visual-quality gate](#run-the-visual-quality-gate)

Read this reference only when creating or substantially redesigning the storefront visual system. Use it to decide what the interface should look and feel like. Use the architecture, Blade/Vue, commerce-contract, asset, and deployment references separately to decide how to implement it.

## Separate design from implementation

Complete the design direction before selecting components or copying templates. Work in this order:

1. Understand brand, merchandise, customer, catalog, price position, content, and primary journey.
2. Generate candidates with the bundled `bagisto-ui-ux` engine.
3. Select one archetype and at most one supporting influence.
4. Define recognizable signatures, composition, typography, palette, image language, shape, surface, and motion.
5. Map the system across home, listing, product, cart, checkout, account, CMS, extensions, and system states.
6. Translate the approved system onto installed Bagisto and Tailwind contracts.

Never begin with a component library aesthetic. Bagisto storefronts use the installed Blade/Vue component runtime. A React-oriented example may teach a general interaction principle, but it is not an implementation source and does not authorize adding another framework.

## Create the visual thesis

Write a one-sentence thesis that links:

- what the brand promises;
- what is physically or emotionally distinctive about the products;
- how customers need to discover or compare them; and
- what the interface will repeatedly do to express that difference.

Weak: “A clean, modern premium store.”

Useful: “A field-guide toy shop uses age-coded shapes, generous product-in-play imagery, and calm safety evidence to make discovery joyful for children and dependable for adults.”

Turn the thesis into three to five observable principles. Each principle must affect multiple pages. “Use joyful color” is vague; “assign one accessible accent family to each age gateway, then return product and checkout surfaces to the neutral base” is testable.

Create anti-goals at the same time. Name the shortcuts most likely to make this store generic: indiscriminate glass, gradient text, excessive pills, identical cards, arbitrary blobs, low-contrast luxury styling, gratuitous horizontal scrolling, or animation on every section.

## Build recognizable signatures

Choose at least three signatures that survive without the logo:

- a repeatable section rhythm or edge treatment;
- a distinctive but usable type relationship;
- a catalog-specific label, marker, annotation, or framing device;
- a controlled image crop or art-direction rule;
- a unique relationship between product evidence and imagery;
- a small interaction motif used only where it reinforces the brand.

Repeat a signature with variation. Repetition creates identity; variation keeps it alive. Do not invent a new visual language for each homepage section.

Test the system by hiding the logo and replacing marketing copy with another language. If the design becomes indistinguishable from a generic template, strengthen composition and product-specific signatures instead of adding effects.

## Control composition

Use a stable container and spacing system, then create contrast through a small set of compositional moves:

- **anchor:** one dominant object, statement, or product establishes the section;
- **counterweight:** a smaller copy or evidence block balances the anchor;
- **sequence:** size, alignment, and spacing create an unmistakable reading order;
- **pause:** quiet space separates distinct ideas rather than filling every gap;
- **rhythm:** alternate media, product density, evidence, and editorial moments;
- **edge:** allow selected media or color fields to meet a container or viewport edge;
- **overlap:** use only when reading order, focus order, contrast, and responsive fallback remain clear.

Reserve the highest variance for discovery and campaigns. Listing pages need stable comparison. Product pages need a predictable purchase zone. Cart, checkout, and account pages should express the brand through type, tokens, details, and service tone—not experimental layout.

Do not use one card grid for every content type. A category gateway, product card, testimonial, evidence item, article, service promise, and campaign require different anatomy even when they share tokens.

## Engineer typography

Define roles before selecting a font file:

- display and campaign;
- page and section title;
- product title;
- body and long-form content;
- label and control;
- price and numeric data;
- metadata, helper, validation, and status.

Use one family when its range is sufficient; use two only when the contrast reinforces the thesis. Keep transactional text, options, prices, forms, and status messages extremely legible. Use tabular numerals where changing prices, quantities, totals, or countdown values could shift layout.

Set a deliberate scale with `clamp()` only where continuous scaling helps. Bound line length. Keep mobile body and form text at least 16px unless a tested exception remains comfortably readable. Avoid ultra-light weights, all-caps paragraphs, tight body tracking, and display faces in dense product data.

Do not generate a remote font import. First inventory installed and approved assets. If a new font is justified, record its license, files, weights, subsets, preload strategy, fallback metrics, privacy impact, and byte budget before implementation.

## Engineer color and surfaces

Start with semantic roles, not a row of attractive swatches:

- canvas, surface, elevated, text, muted, decorative border, strong control border;
- brand, on-brand, accent, on-accent, focus;
- price, sale, stock, success, warning, danger;
- disabled, selected, loading, and overlay.

Give saturated colors scarce responsibilities. A brand color does not need to fill every header, button, badge, and link. Preserve a single unmistakable primary action on each surface.

Verify literal foreground/background pairs. Normal text targets at least 4.5:1, large text and meaningful non-text boundaries at least 3:1, and focus indicators must remain visible against adjacent colors. Keep a subtle decorative-border role separate from the contrast-safe boundary used by controls and meaningful states. Error, sale, and stock states need text or icons in addition to color.

Use surface changes to express hierarchy before shadows. Define a small elevation scale. Avoid placing shadows on every card; borders, spacing, and background contrast are often clearer and cheaper. Use transparency or blur only for an overlay relationship that remains readable without the effect.

## Direct imagery and icons

Create a shot list rather than saying “use beautiful images.” Define:

- subject and customer context;
- camera distance and angle;
- lighting and shadow character;
- background and prop rules;
- product scale cues;
- crop behavior for mobile, card, gallery, and campaign ratios;
- required product, detail, process, lifestyle, and evidence coverage.

Protect image truth. Never use decoration to imply a product capability, ingredient, size, or included item that is not authoritative.

Use one icon language with consistent optical size, stroke or fill, corner behavior, and state treatment. Prefer installed Bagisto icons or locally approved SVGs. Icons supplement labels for navigation and commerce actions; they do not replace critical text. Decorative SVGs must be hidden from assistive technology.

## Create component anatomy

Specify components as anatomy plus states, not screenshots. For every interactive component define:

- semantic element and accessible name;
- content slots and content limits;
- default, hover, focus-visible, active, selected, loading, disabled, error, success, and empty states;
- keyboard and pointer behavior;
- server-rendered baseline and Vue enhancement;
- narrow, wide, translated, RTL, zoomed, and missing-content behavior.

Product cards must preserve image, product identity, authoritative price, relevant status, and supported actions. Product-detail purchase controls must preserve all installed product-type options, validation, stock, tax, quantity, and add-to-cart behavior. Decorative consistency never outranks commerce completeness.

## Compose responsive behavior

Begin with the narrow composition and add space only when content needs it. Do not rely only on named device widths.

For each major surface record:

- reading and DOM order;
- grid changes and minimum card width;
- which content moves, folds, scrolls, or becomes a drawer;
- sticky elements and reserved offsets;
- primary-action position;
- media aspect ratio and focal-point behavior;
- overflow strategy;
- pointer, keyboard, and touch behavior.

Use logical properties for inline and block placement. Test 320px width, landscape phones, zoom/reflow, long translations, RTL, long prices, badges, missing images, many options, validation errors, empty merchandising, and out-of-stock states.

Hide secondary decoration when needed, but do not duplicate meaningful content into separate mobile and desktop trees unless the installed component contract already handles accessible state and IDs correctly.

## Translate the system into Bagisto

Map approved roles to the installed theme asset system:

- use CSS custom properties or the discovered Tailwind extension mechanism;
- preserve required Shop compatibility tokens and content globs;
- keep utility class names statically discoverable by the installed build;
- use reusable Blade partials/components for repeated anatomy;
- enhance only stateful interactions with the installed Vue application;
- retain server-rendered product, price, stock, SEO, and merchant content;
- preserve render events and extension insertion points.

Do not install shadcn, Radix, a React runtime, a second Tailwind version, an icon package, or a design-system package to reproduce a visual example. Re-express the approved design through installed Bagisto primitives unless the user separately approves an architectural change.

## Run the visual-quality gate

Before calling the design complete, inspect real rendered pages and answer:

1. Is the store identifiable without its logo?
2. Does every page have one obvious dominant task?
3. Are products, prices, options, stock, errors, totals, and trust easier to understand than before?
4. Do visual signatures repeat without turning every section into the same component?
5. Does the design survive real catalog content, translations, RTL, missing media, and empty sections?
6. Are mobile layouts intentionally recomposed?
7. Are typography, imagery, icons, and effects licensed and within budget?
8. Do keyboard, zoom, screen-reader, contrast, touch, and reduced-motion users retain the full journey?
9. Can merchants change intended content without editing Blade?
10. Do measured performance and automated journeys pass?

Review the whole journey, not only a polished homepage viewport.
