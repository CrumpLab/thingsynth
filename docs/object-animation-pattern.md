# The object animation pattern

*Agreed with Matt on 2026-10-24, after the pyramid and the stalks. Every object is reworked this way.*

## 1. Say what the thing is

Write a short description of the object: what it is (a plant, a creature, a blob, an eye, a building, water),
what it is made of in the painting (its shapes and colours), and how it sits in the picture: what it grows out of,
leans on, overlaps, faces, and what is around it.

## 2. Decide what it gets to do

From what it is, choose how it can grow or change over time, in a way that changes the *drawing*, not only its
colour or size:

- plants grow leaves, shoots, tendrils, buds, flowers;
- creatures move: arms raise, mouths open, heads turn, tails curl, antennae extend;
- blobby things get blobbier: bulges grow, drips lengthen, lobes split off;
- eyes open and close, pupils look around;
- other things in the same spirit (water rises and splashes, clouds billow, buildings stack up).

The change maps onto the binding's timeline: the first frame is the painting exactly as drawn (the least of the
thing), the last frame is the most of it, and the frame shown follows the parameter's value or the note. Nothing
moves on its own.

## 3. Draw it the way the painting draws

Anything new is drawn in the painting's style:

- **Every form is an outlined shape with a fill. No bare lines.** A branch is a tapered green shape with a black
  outline, not a stroke; a new arm is an outlined, filled limb.
- **The ink matches the painting's** weight and character: the finer outlines (about 11 px) for small new
  features, heavier for big forms; round joins, slightly irregular, hand-drawn.
- **Colours come from the object itself or the painting's candy palette.**
- **New parts join seamlessly**: they start inside the shape they grow from and leave their outline open where
  they join, so there is no seam.
- **Redraw existing linework where the change needs it** (a mouth opening, an arm moving), not just add on top.

Supporting effects (sap rising, glow, colour moving toward a hue) can accompany the drawn change, but the drawn
change is the point.

## 4. Repeat

For each object: render its current animation (`node scripts/object_frames.mjs <binding-id> --tag before`), write
the description and what it gets to do, build it, render the after, compare first-to-last frame, and tune until it
reads as the object doing its thing in the painting's style.

## Done so far

| object | binding | what it is | what it does |
| --- | --- | --- | --- |
| golden-pyramid | `amp.drive` | the big golden pyramid, centre-right, with creatures on it | molten heat rises inside it; past half its outline boils (to redo under this pattern) |
| stalk-left, stalk-right | `upper.db1`, `upper.db2` | two green stalks in the stalk forest, top left | they grow: one outlined branch per drawbar step, with leaves, spiral tendrils and eye-buds, sap rising |
