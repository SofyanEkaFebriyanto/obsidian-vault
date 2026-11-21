---
name: motion-graphics-code
description: "Use when building deterministic motion graphics from code."
---

# Motion graphics from code

Use this class-level skill for code-generated animated videos, especially projects where every frame is computed from time and scene timing is centrally managed.

## Operating sequence

1. Read the project's entry instructions, storyboard/treatment, style guide, world/character guide, timeline, scene template, shared UI helpers, palettes, sprite registry, and background APIs before proposing implementation.
2. Respect the repository's approval gate. Before each new stage, state intended files and observable result, then wait for the requested approval token. Approval for one stage is not approval for the next.
3. When asked for a plan and approval, do not edit files until approval arrives.
4. Before coding scenes, reconcile the storyboard with existing code: confirm imports still exist, helper signatures match, requested background keys are implemented, scene durations are contiguous, cue types are valid, and render/check commands can reach the selected timeline.
5. Implement one scene per file from the project template. Register every scene in both the central timeline and the scene draw map. Avoid unrelated changes; if a pre-existing import blocks verification, report the blocker and ask before expanding scope unless repair was authorized.
6. Keep frame rendering deterministic: scene output is a pure function of global/local time and inputs. No cross-frame mutable state, wall clock, timers, or `Math.random`; use the project's seeded random helper for deterministic variation.
7. Reuse project sprite, palette, typography, and UI helpers. Use required pixel drawing primitives and text renderer. Do not create or fetch unapproved assets.
8. Follow the storyboard for scene intent, VO, HUD, transitions, rule-slot completion times, and one clear prop per instructional rule. Keep scene cuts gapless and transitions on valid scene boundaries.
9. Run project validation first, then still-frame checks at requested key seconds. Do not render final MP4 or commit unless explicitly requested.
10. Report exactly what changed and actual check/still outcomes. Do not claim a still was generated if validation prevented rendering.

## Visual review and revision loop

A successful build proves code validity, not visual quality. For visual work, create a representative still set and inspect the actual rendered images and sprite sheet before claiming completion.

1. Translate each visual request into observable checks: requested locations and timestamps, resemblance to supplied character references, palette conflicts, text readability at final scale, prop hierarchy, cropping or overlap, and whether interactions are visible.
2. Make a coverage checklist from requested timestamps. Deduplicate overlapping times while retaining their distinct purposes; render every unique requested time and confirm the output files exist.
3. Inspect the opener, closing or transformation scene, key instructional beats, and at least one still per distinct location. Inspect the sprite sheet separately when sprites change. One good frame does not establish that the rest pass.
4. Treat text as foreground content, not texture. Check actual rendered glyphs at output resolution. Give short labels contrast, padding, and separation from borders and props. If text is crossed or occluded, remove/move the interference and inspect a fresh render.
5. When users report clashing colors, simplify each scene's active palette and assign distinct jobs to base, text, accent, and warning colors. Do not add unrelated accents; ensure character identity remains readable against each background.
6. Compare revised sprites with their reference at the displayed sprite scale, not only on the sprite sheet. Check silhouette and distinguishing features; verify characters remain distinct inside scenes.
7. Character motion must include legible actions, not only bobbing. Give each beat a clear pose silhouette (such as pointing, typing, reaching, reacting, or presenting), and connect hands/arms visibly to the prop or target. Sprite-row edits that change only a few pixels may still read as static at final output size; review rendered scene stills at each meaningful pose. Avoid disconnected marks that look like stray pixels. If sprite variants are used, keep row dimensions and palette keys valid, register every variant when the sprite sheet/checker expects it, and select variants deterministically from scene-local time.
8. Motion should show a meaningful process or state change (for example, a cursor selecting, playhead tracking, frames appearing in sequence, or progress completing). Derive it from scene time and inspect that it does not obscure focal text or remain stuck in a misleading state.
9. If inspection finds a defect, fix the source, rerun validation and affected stills, and inspect the new render. Do not call a visual issue fixed based only on a source edit or successful command.
10. Link requested stills and sprite sheets when available, state exactly what was inspected, and name any remaining caveat. Avoid blanket claims that visuals are fixed when only a subset was reviewed.

## Timing and validation checklist

- Check first scene start and final scene end against requested duration.
- Verify each scene starts exactly when its predecessor ends.
- Confirm each transition is at a cut and each `SLOT_AT` corresponds to rule completion.
- Confirm cues use valid types and are ordered by time.
- Ensure slot count matches the number of rules.
- Choose still timestamps inside representative scene intervals, not exactly on cuts, and cover each requested location when feasible.
- After generating stills, inspect the actual images, not only the command output. Check text legibility, cropping, character visibility, overlapping props/UI, visual match to the treatment, and whether transition frames hide key content. Fix verified issues, then rerun `npm run check` and the requested stills.
- For scenes that fill HUD rule slots at a scene boundary, remember `sceneAt(t)` selects the next scene at the exact boundary. Trigger the completion `+1` in that next scene using `age = t - SLOT_AT[i]`; do not place the effect only in the scene that has already ended.
- Treat storyboard VO as production content: preserve it per scene in the treatment/VO map, and check whether the project has a recorded voiceover asset or an explicit audio-generation task before implying VO is implemented by scene code. Do not claim VO was generated merely because its text is present in the storyboard.
- If check fails before still rendering, report the exact failure; do not render a final video as workaround.

## Pitfalls

- Removing a legacy sprite export can break older scene modules even if inactive, because the module graph may still import them. Search all imports before deleting aliases. If the user explicitly requests alias removal, report dependents and get authorization before changing them.
- `check` may validate the currently registered project, not the newly planned storyboard. Confirm active scene registry and duration before presenting it as evidence for new implementation.
- Background functions are not automatically used by scenes. Trace each scene's call chain; a background API alone does not integrate into the video.
- Still rendering only shows active scenes. Verify accepted seconds syntax and timeline before running requested stills.
- Distinguish an image-edit request from permission to alter surrounding files. Keep stage scope explicit.

## Evidence in final report

List created and modified files, then report:
- `npm run check`: pass/fail and concise output.
- Requested still command: pass/fail, generated paths, or exact blocker.
- Whether MP4 was intentionally not rendered and whether any commit was made.

Never render MP4 or commit unless explicitly requested.

For recorded-VO transcription, cut selection, caption timing, slot/cue synchronization, and verification, follow [`references/vo-led-scene-recut.md`](references/vo-led-scene-recut.md).