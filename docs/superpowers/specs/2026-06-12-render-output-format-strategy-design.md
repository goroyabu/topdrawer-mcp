# Render Output Format Strategy Design

## Goal

Record the current design direction for Topdrawer render/export outputs at a
larger scope than device-orientation control alone.

This note captures:

- which output formats should be treated as the main supported targets
- which additional formats remain future candidates
- how Ghostscript fits into the rendering/export pipeline
- why interactive or terminal-display devices are not part of the current
  implementation scope

## Status Level

This topic is at design and scope-definition level.

Confirmed inputs to this note:

- the current runtime uses a PostScript-based wrapper flow for PNG rendering
- Topdrawer supports a broader set of legacy device targets than the repo
  should expose directly
- the highest-value outputs for the current repo scope are image output for
  inspection and PostScript output as the primary intermediate/source artifact

This document is a design record, not an implementation plan.

## Current State

The current render flow is intentionally narrow:

1. The server prepends a `SET DEVICE POSTSCR FILE='...'` wrapper line.
2. `td` writes PostScript output.
3. Ghostscript reads that PostScript and produces a PNG image.

This means the implementation already has two output artifacts in practice:

- a raster image used for inspection
- a PostScript file used as the render source

However, the public surface still behaves mainly as a PNG-rendering feature,
and the broader output-format strategy has not yet been recorded explicitly.

## Design Direction

### Main Supported Output Families

The main output families should be:

- image output
- PostScript output

Within those families, the primary concrete formats are:

- `png`
- `ps`

Rationale:

- `png` is the most practical inspection artifact for agents and users
- `ps` is the native render source already used by the runtime and is the
  cleanest export target to expose first

### Secondary Future Candidates

The following should remain in design scope as future candidates, but not as
immediate implementation targets:

- `eps`
- `pdf`
- `hpgl`
- `cgm`

These are worth preserving in the design because they have plausible technical
value, but they are not required for the next step of narrowing the runtime
surface.

### Out Of Scope For The Current Surface

The following classes of output should not be part of the current
implementation scope:

- interactive display devices
- terminal-emulation graphics devices
- printer-specific legacy device frontends

This includes device families such as:

- `XWINDOW`
- `TEKTRONIX` and related `TEK*` variants
- `REGIS`
- `SIXEL`
- `PRINTRONIX`
- `VERSATEK`
- `IMAGEN`

The reason is not that they are impossible to use. Rather, they would broaden
the repository from a narrow file-oriented MCP server into a GUI/device bridge
with much weaker portability and more runtime coupling.

## Format Positioning

### PNG

`png` should remain the main inspection format.

It is the best fit for:

- agent-readable visual review
- user confirmation of plot output
- stable downstream handling in MCP clients

The server should continue to treat PNG as a rendered view artifact rather than
as Topdrawer's primary source format.

### PostScript

`ps` should be treated as the primary export/source artifact.

It is already central to the runtime behavior and should be considered the
first non-image output worth exposing explicitly.

PostScript also provides the cleanest base for:

- rasterization to PNG
- later conversion to PDF
- later conversion to EPS

### EPS

`eps` is the strongest future candidate after `ps`.

It is closely related to the existing PostScript path and remains useful for
technical-document workflows, but it does not need to be part of the first
surface expansion.

### PDF

`pdf` is a practical future candidate even though it is not the current native
Topdrawer export path being used in the runtime.

Its value is convenience for user consumption rather than preserving a
Topdrawer-native artifact.

### HPGL And CGM

`hpgl` and `cgm` should remain explicit future candidates only.

They have legitimate historical and technical use cases, but they are more
specialized and should not shape the first widened render/export API.

## Ghostscript Role

Ghostscript should continue to be treated as the main downstream converter for
the PostScript pipeline.

Its role in the design is:

- convert PostScript to PNG for inspection
- provide future conversion paths from PostScript to:
  - PDF
  - EPS
- remain outside the command-discovery and manual-search concerns of the repo

This keeps the architecture simple:

- Topdrawer owns plot generation
- Ghostscript owns PostScript consumption and derivative output generation

The server should not attempt to make Ghostscript an arbitrary document
conversion frontend. It should use Ghostscript only where that supports the
narrow Topdrawer-output workflow.

## Tool Surface Direction

The preferred high-level direction is:

- one tool per output format
- one shared naming pattern across formats
- one tool accepting either file input or inline script input

The naming pattern should avoid format-dependent verb choices such as mixing
`render_*` and `export_*`.

The current preferred naming form is:

- `generate_topdrawer_png`
- `generate_topdrawer_postscript`

This pattern is preferred because:

- it keeps the verb stable across formats
- it scales naturally to future formats such as:
  - `generate_topdrawer_eps`
  - `generate_topdrawer_pdf`
- it avoids having to justify why one format is "rendered" while another is
  "exported"

The input shape should also stay consistent across formats.

The current preferred contract is:

- `input_path` or `script`
- exactly one of them must be provided
- both at once are an error

This means the surface should be organized primarily by output format rather
than by input source.

That direction avoids growing into four first-class tools immediately such as:

- file-to-png
- script-to-png
- file-to-postscript
- script-to-postscript

The exact Python/FastMCP validation approach is still open, but the public
contract should be explicit and consistent.

## Input Contract Considerations

The most important design constraint for this surface is input disambiguation.

If one tool accepts both file input and inline script input, it must clearly
enforce:

- exactly one of `input_path` or `script`

This introduces some implementation complexity, but it is acceptable because
it keeps the public tool count smaller and keeps output-format choice as the
main organizing principle.

One secondary asymmetry remains:

- `input_path` naturally carries a filesystem location and relative-reference
  base
- `script` may need an explicit `base_dir`

That asymmetry should be treated as an argument-level detail, not a reason to
split the public surface by input mode.

## Naming Direction

The preferred naming convention for future output tools is:

- `generate_topdrawer_<format>`

For the currently approved primary targets, this means:

- `generate_topdrawer_png`
- `generate_topdrawer_postscript`

This naming convention should be treated as the default pattern for future
format additions unless a later design note explicitly changes it.

## Why Interactive Display Is Excluded

Interactive display remains an understandable user wish, especially for cases
where a user wants to inspect output in a live window and then give follow-up
instructions.

However, the current repo should not treat legacy display devices as a core
output family.

Key reasons:

- they depend on local GUI or terminal capabilities
- they are less portable across MCP clients and execution environments
- they introduce lifecycle concerns such as window launch, focus, session
  state, and cleanup
- they solve a different problem from stable artifact generation

If preview functionality is explored later, it should be treated as a separate
local-preview feature layered on top of file outputs, not as direct exposure of
legacy Topdrawer interactive devices.

## Recommended Scope Boundary

The practical near-term boundary should be:

- main implementation targets:
  - `png`
  - `ps`
- future-but-not-now targets:
  - `eps`
  - `pdf`
  - `hpgl`
  - `cgm`
- excluded from current implementation scope:
  - interactive display devices
  - terminal/legacy display devices

This boundary preserves a small public surface while keeping the design open to
incremental expansion.

## Relationship To Earlier Render Design Work

This document complements rather than replaces:

- `docs/superpowers/specs/2026-06-06-render-device-control-design.md`

The earlier note focuses on device-orientation and wrapper-control questions.
This note widens the frame to output-family strategy and public-surface scope.

Both should be read together when planning future render/export changes.

## Candidate Next Step

The next focused design or plan should decide:

- whether the first widened public surface splits render and export into
  separate tools
- whether `ps` is returned as a direct artifact or only through an explicit
  export path
- which minimal options belong in the first export-facing API

That later step can then translate this strategy into an implementation plan.
