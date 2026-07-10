# Workbench Neutral UI Polish Design

## Context

The Workbench chat surface currently uses a saturated blue user message bubble and blue citation cards. That makes the conversation timeline feel more like a consumer chat app than a neutral research workbench. The user confirmed the desired direction: low-saturation neutral surfaces, blue reserved for primary actions/current tabs/small status indicators, white assistant answer paper, and quieter citation cards.

## Goals

- Change user messages from a solid blue block to a shallow gray/blue-gray surface with dark text.
- Keep assistant answers on a white reading surface with calmer borders and stronger body readability.
- Reduce citation card color intensity by replacing large blue fills with pale neutral backgrounds, soft borders, and small numbered badges.
- Preserve blue for the send button, active mode tab, save-note action, and compact source metadata accents.
- Keep the existing Workbench layout, chat behavior, streaming behavior, and dark-mode support intact.

## Non-Goals

- No layout restructure of the Workbench shell, sidebars, inspector, or modal system.
- No new component library or design token framework.
- No backend changes.
- No copy changes except CSS class-level visual treatment.

## Visual Direction

User messages should read as operator input inside a workbench: compact, restrained, and scannable. The bubble uses a light blue-gray/gray background, gray border, dark text, and a modest shadow. It remains right-aligned so conversational role remains clear.

Assistant answers should read like a paper surface. The answer card remains left-aligned and uses a white background, subtle gray border, softer shadow, and prose classes tuned for readable neutral text. The existing save-note affordance stays blue because it is an explicit command.

Citation cards should be supporting evidence, not primary content. Cards use white or near-white backgrounds, `slate`/`gray` borders, small blue-number badges, blue text only for document metadata or relevance chips, and no broad blue fill. Expanded citation content remains framed but neutral.

## Test Strategy

Add a focused React Testing Library test to `frontend/src/components/ChatInterface.test.tsx` that renders a user message and an assistant message with a citation, then asserts the intended visual contract through Tailwind class names:

- User message contains neutral `bg-slate-100`/dark text classes and no `bg-blue-600 text-white` treatment.
- Assistant message contains white paper and readable prose classes.
- Citation card uses a neutral border/background while its number badge keeps compact blue accent treatment.

Existing tests continue to cover timeline layout, source-selection recovery, and stream failure recovery.

## Screenshot Verification

After implementation, run frontend unit tests and build. Then start the Vite dev server and capture/inspect the Workbench in a browser-sized viewport. The screenshot check should verify:

- User message is not a saturated blue block.
- Assistant answer reads as a white paper card.
- Citation cards are quiet, with blue limited to badge/action accents.
- Composer send button and active mode tab remain blue.
