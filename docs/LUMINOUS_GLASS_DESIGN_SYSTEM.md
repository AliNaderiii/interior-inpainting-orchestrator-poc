# Luminous Glass — Spatial Studio Design System

**Status:** Phase 05 implementation baseline
**System type:** original, clean-room interface system
**Primary product surface:** Spatial Design Studio

## Purpose

Luminous Glass is a restrained control-layer system for a professional, canvas-first spatial design workflow. It uses translucency to clarify hierarchy around the work—not to decorate the work itself.

The system is informed by public platform guidance and broad patterns in professional canvas applications. It does not copy Apple, Figma, Canva, or any client-specific brand, assets, layouts, language, or trade dress.

## Research basis

- Apple WWDC25, “Meet Liquid Glass”: glass is most useful as a navigation/control material, while content should remain the focus. Nested glass and indiscriminate tint reduce hierarchy and legibility.
  https://developer.apple.com/videos/play/wwdc2025/219/
- Apple WWDC25, “Build a SwiftUI app with the new design”: grouping, concentric geometry, floating controls, and scroll-edge separation should communicate structure rather than novelty.
  https://developer.apple.com/videos/play/wwdc2025/356/
- Apple WWDC25, “Get to know the new design system”: tint should carry meaning, especially for primary actions and selected states.
  https://developer.apple.com/videos/play/wwdc2025/323/
- Apple accessibility guidance: Increased Contrast, Reduced Transparency, and Reduced Motion must be treated as core states.
  https://developer.apple.com/forums/topics/design-topic
- Figma UI3 design notes: the canvas should remain visually dominant; durable professional panels benefit from docking and resizing rather than excessive floating chrome.
  https://www.figma.com/blog/our-approach-to-designing-ui3/
- Lucid canvas-application guidance: canvas, contextual tools, fixed chrome, and modal/focus layers require distinct interaction rules.
  https://lucid.co/techblog/2023/08/25/design-for-canvas-based-applications

## Original layer model

1. **Environment layer** — restrained ambient color and depth; never carries required information.
2. **Content/canvas layer** — source scene, product asset, masks, placement, variants, and evidence. This layer uses stable, mostly opaque surfaces.
3. **Control glass layer** — top navigation, workflow rail, tool cluster, inspector, and compact review controls.
4. **Modal/focus layer** — high-opacity surfaces plus explicit dimming, used only when focus must be isolated.

## Non-negotiable rules

- Never place glass on glass.
- Never animate `backdrop-filter` or blur radius.
- Never use blur as the sole mechanism for text separation.
- Never put long-form content, proof tables, code, or the primary canvas on translucent surfaces.
- Keep primary actions solid and high contrast.
- Use accent tint only for selected tools, confirmed modes, or the primary action.
- Give every state a non-color cue: label, icon, geometry, border, or text.
- Keep hover motion under 220 ms and remove nonessential motion when requested.
- Maintain a solid-surface fallback for unsupported browsers and reduced-transparency preferences.

## Token architecture

### Color roles

- `--env-*`: ambient background colors only.
- `--surface-*`: opaque content, canvas, and proof surfaces.
- `--glass-*`: control chrome backgrounds and borders.
- `--ink-*`: primary, muted, and low-emphasis foreground roles.
- `--signal-cyan`: selection, alignment, and system focus.
- `--signal-lime`: verified/safe state.
- `--signal-amber`: provisional or attention state.
- `--signal-coral`: error/destructive state.

### Geometry

- Canvas and long-form cards: 24–32 px radii.
- Control glass: 18–24 px radii.
- Compact tools: 10–14 px radii.
- Concentric nested geometry is expressed through smaller inner radii, not additional glass.

### Depth

Depth combines a light edge, a dark keyline, and a soft shadow. Blur is an enhancement. Opaque fallbacks preserve all required separation.

## Accessibility states

The implementation must include all of the following:

```css
@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) { ... }
@media (prefers-reduced-transparency: reduce) { ... }
@media (prefers-reduced-motion: reduce) { ... }
@media (prefers-contrast: more) { ... }
```

A manual `data-transparency="reduced"` state is also provided because browser support for `prefers-reduced-transparency` is not universal.

## Performance budget

- Blur is limited to compact, persistent control surfaces.
- The canvas and variant cards are opaque.
- No full-page blur layers.
- No blur animation.
- Canvas renders are deterministic and scheduled through `requestAnimationFrame` during pointer interaction.
- Static assets remain local and bounded.

## Product application

Desktop uses a docked workflow rail, a dominant center canvas, and a docked contextual inspector. On narrower layouts these regions become stacked surfaces rather than overlapping floating panels. The bottom tool cluster may float because it is small, contextual, and does not obscure critical content.

## Review gate

A release candidate fails the visual-system gate if it:

- obscures content behind translucent surfaces;
- lacks a solid fallback;
- causes horizontal page scrolling at 320 CSS px;
- removes focus visibility;
- puts essential proof only in color or blur;
- adds external fonts/scripts/assets to the no-network showcase;
- copies distinctive external product or client styling.
