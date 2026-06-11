# Render Device Control Design

## Goal

Capture the current rendering-wrapper behavior, the observed orientation
problem, and the design questions for exposing device/render controls to
agents without broadening repository scope too far.

## Status Level

This topic is at investigation and design level.

- Confirmed current behavior:
  - render tools prepend a fixed `SET DEVICE POSTSCR FILE='...'` line
  - Ghostscript rendering settings are mostly fixed in runtime code
- Confirmed problem:
  - the default rendered PNG orientation is not always the expected one
  - the issue is primarily driven by Topdrawer PostScript orientation, not a
    Ghostscript auto-rotation step
- Open design work:
  - which render controls should be exposed as MCP tool arguments
  - what defaults should be fixed by the server
  - how user script `SET DEVICE` lines should interact with server-managed
    output settings

This document is therefore a design note, not an implementation-ready plan.

## Current State

The runtime render flow currently works like this:

1. The agent provides Topdrawer script text or an existing `.top` file.
2. The server prepends one wrapper line:

   `SET DEVICE POSTSCR FILE='render.ps'`

3. `td` renders that wrapper script into PostScript.
4. Ghostscript reads the PostScript bounding box and renders a trimmed PNG.

The server does not currently expose Topdrawer device options such as:

- `ORIENTATION`
- other `SET DEVICE POSTSCR ...` options

The server also fixes Ghostscript-side behavior in code, including:

- `png16m` output
- fixed DPI
- fixed padding
- bounding-box-based translation

## Investigation Findings

The observed 90-degree-orientation problem appears before PNG conversion is
complete.

Key findings:

- The PostScript produced by `td` already matches the final rotated-looking
  output.
- Ghostscript is not currently issuing an explicit rotate operation in the
  runtime command.
- Adding `SET DEVICE POSTSCRIPT ORIENTATION=3` to the input produces the
  expected orientation for the investigated sample.
- Different `ORIENTATION` values change the rendered layout substantially,
  including whether the output is portrait-like or landscape-like.

This means the immediate cause is Topdrawer PostScript device behavior rather
than an accidental Ghostscript rotation step.

## Why This Matters

The current render API hides important output controls inside the server.

That is acceptable for a very narrow MVP, but it becomes limiting when:

- the default orientation is wrong for a concrete script
- an agent needs to control device behavior intentionally
- a later agent needs predictable render behavior across multiple scripts

At the same time, the repository should not become a fully general wrapper for
all Topdrawer output-device configuration.

## Design Questions

### 1. Which controls belong in MCP tool arguments?

The first candidates are:

- Topdrawer device orientation
- Ghostscript output DPI
- Ghostscript padding/margin around the cropped plot

A second-tier candidate is:

- an escape hatch for extra PostScript-device options

The design question is how much should be explicitly modeled before the runtime
surface becomes too broad.

### 2. What should the server default be?

The current fixed wrapper line does not choose an explicit orientation.

One plausible direction is:

- set a server default orientation explicitly
- let the agent override it when needed

The current investigation suggests `ORIENTATION=3` is a strong candidate for
the default, but this should be treated as a design choice rather than assumed
global truth until checked against a broader set of scripts.

### 3. How should script-authored `SET DEVICE` interact with server-managed output?

This is the most important interface question.

The server currently owns:

- the output PostScript file location
- the conversion pipeline to PNG

If user script text also contains `SET DEVICE ...`, the resulting precedence is
unclear and could break output capture entirely.

Possible policy directions include:

- reject script-side `SET DEVICE` in render inputs
- allow script-side `SET DEVICE` only for a narrow allowlist of options
- let MCP tool arguments override script-side settings

This needs an explicit rule before implementation.

### 4. Should Ghostscript controls be part of the public surface?

Some render controls are not Topdrawer device controls at all.

Examples:

- output DPI
- output background behavior implied by the chosen device
- padding around the cropped image

The question is whether these should be exposed directly, partially exposed, or
kept as fixed runtime policy.

## Recommended Direction

The likely narrow direction is:

1. Keep the wrapper-based output capture model.
2. Introduce a small structured argument surface for the highest-value controls.
3. Prefer explicit server-managed defaults over hidden implicit device behavior.
4. Define a clear precedence rule between:
   - server-managed output capture
   - MCP render arguments
   - script-authored device commands

The first explicit render controls most likely worth modeling are:

- orientation
- DPI
- padding

An unrestricted device-options passthrough should be treated cautiously and is
not yet assumed to be part of the first implementation.

## Non-Goals

- Do not turn the repository into a broad Topdrawer device-configuration
  frontend.
- Do not add general support for arbitrary PostScript manipulation.
- Do not couple this topic to broader manual-coverage or command-discovery
  roadmap work.
- Do not assume every Topdrawer script should be rendered with the same device
  policy without further review.

## Candidate Next Step

If this topic moves forward, the next focused work should define:

- the minimal new render arguments
- the precedence rule for script-side `SET DEVICE`
- the initial default orientation policy

That work should then move into a plan document or a concrete issue.
