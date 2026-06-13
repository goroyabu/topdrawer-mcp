# Render Device Parse And Execution Policy Design

## Goal

Record the current design direction for how render/output tools should handle
Topdrawer `SET DEVICE` usage in user-provided scripts.

This note focuses on:

- the public render/output surface around device handling
- the role of a `SET DEVICE` parser
- the distinction between Topdrawer syntax acceptance and tool-level policy
- the execution flow for scripts with or without `SET DEVICE`
- server-managed output-path handling for PNG and PostScript generation

This document complements broader render-format strategy notes and stays
focused on device parsing, normalization, and execution policy.

## Status Level

This topic is at design level.

Confirmed inputs to this note:

- the current runtime prepends a fixed `SET DEVICE POSTSCR FILE='...'` wrapper
- Topdrawer also allows device selection on the command line using the same
  device syntax described by `SET DEVICE`
- the repository should avoid full Topdrawer-language parsing while still
  handling `SET DEVICE` in a more principled way than blind text prepending

This document is a design note, not an implementation plan.

## Surface Direction

The current preferred public surface is:

- one tool per output format
- one shared naming pattern across formats
- one tool accepting either file input or inline script input

The currently preferred initial tools are:

- `generate_topdrawer_png`
- `generate_topdrawer_postscript`

The preferred input contract is:

- exactly one of `input_path` or `script` must be provided
- `base_dir` may be used when inline script input needs a filesystem base

This keeps the public surface organized by output format rather than by input
source.

## Why Device Parsing Is Needed

If a user script already contains `SET DEVICE`, the server cannot safely assume
that simple line prepending is enough.

The server needs to answer:

- whether the script contains device control at all
- whether that device syntax is valid Topdrawer syntax
- whether the selected device/options are supported by the current tool
- whether output-path settings must be replaced by server-managed paths

This means the repository needs a device-aware normalization step even if it
does not attempt to parse all Topdrawer commands.

## Syntax Acceptance Versus Tool Policy

The preferred design separates two concerns:

1. syntax acceptance
2. tool policy validation

### Syntax Acceptance

The parser should aim to accept `SET DEVICE` syntax that is consistent with the
manual, including documented abbreviations where practical.

This means the parser should not define repo-specific syntax for device
commands. It should try to recognize manual-compatible forms such as:

- device names
- common device options
- documented abbreviations
- output-path-related options such as `FILE`, `OUTPUT`, or `DDNAME`

### Tool Policy Validation

After parsing succeeds, the tool should separately decide whether the parsed
device configuration is usable for the current output tool.

This makes it possible to distinguish:

- invalid Topdrawer syntax
- valid Topdrawer syntax that is unsupported by the current tool

That distinction is important because the repository should avoid rejecting a
manual-compatible command merely because the current PNG/PostScript tools do
not support every device mode.

## Parser Scope

The parser should remain narrowly scoped to `SET DEVICE`.

It does not need to become a full Topdrawer parser.

Its expected responsibilities are:

- detect one or more `SET DEVICE` occurrences in script text
- parse the selected device name
- parse common device tokens and key/value options
- normalize recognized abbreviations to canonical internal names where needed
- preserve enough information to explain errors clearly

The parser may keep some device-specific string content in an opaque form if
needed, as long as later policy validation can reject unsupported usage
cleanly.

## Initial Policy Targets

The initial output tools are expected to center on PostScript-backed flows.

That means policy validation should initially target:

- `POSTSCRIPT`
- later candidates such as `EPS` or `GPOSTSCRIPT`

The parser may still accept syntax for other devices when recognizable, but the
tool policy may reject them for the current output tools.

Examples of likely tool-policy rejection categories include:

- interactive/window devices such as `XWINDOW`
- terminal-emulation devices such as `TEKTRONIX`, `REGIS`, or `SIXEL`
- multi-device output usage such as `ADD` and `UNIT`
- device/file-routing combinations that conflict with server-managed output

## Output Path Authority

One of the most important policy decisions is that output capture remains
server-managed.

This means:

- user-authored `FILE=...`, `OUTPUT=...`, or `DDNAME=...` may be valid
  Topdrawer syntax
- but the execution path used by the tool may replace those values with
  server-managed paths

This is especially important for PNG generation:

- Topdrawer must first write a PostScript file
- the server must know exactly where that temporary PostScript file is
- Ghostscript must then consume that exact file to produce the final PNG

So even when a user script includes its own output file target, the execution
flow may need to override that target in the normalized execution config.

## Execution Flow

The preferred execution flow has three broad phases:

1. input normalization
2. device analysis and normalization
3. execution and output conversion

### 1. Input Normalization

The tool should:

- validate that exactly one of `input_path` or `script` was provided
- resolve filesystem paths
- establish the effective working/base directory
- read or normalize the source text

### 2. Device Analysis And Normalization

The tool should then:

- detect `SET DEVICE` commands in the source text
- parse them with the device parser
- apply tool policy validation
- build one normalized execution device config

That normalized config should represent the device settings the server will
actually execute with, regardless of how the original script expressed them.

### 3. Execution And Output Conversion

Finally, the tool should:

- create the execution-time device output path(s)
- rewrite or synthesize the effective `SET DEVICE` configuration
- run `td`
- for PNG output, run Ghostscript on the generated PostScript
- verify the expected output artifact exists

## Flow Without `SET DEVICE`

If the source script contains no `SET DEVICE`, the flow is straightforward:

1. read input
2. detect no device command
3. build the execution device config from tool defaults and tool arguments
4. inject or otherwise supply the required PostScript device configuration
5. execute `td`
6. convert to PNG if needed

This is the simpler path and should remain well supported.

## Flow With `SET DEVICE`

If the source script contains `SET DEVICE`, the flow becomes:

1. read input
2. detect device command(s)
3. parse device syntax
4. validate against current tool policy
5. normalize the execution config
6. replace or override output-path-related settings as needed
7. execute using the normalized config

This means that a script-authored device command is not ignored, but neither is
it treated as authoritative for output-path capture.

## Rewriting Versus Blind Prepending

The preferred direction is away from blind prepending and toward normalized
execution configuration.

The exact mechanism is still open, but the design should assume one of these
families of implementation:

- rewrite the effective `SET DEVICE` line in execution-time source text
- or extract device intent and supply the effective configuration through the
  runtime invocation path

Whichever mechanism is chosen, the execution-time configuration should be based
on normalized parser output plus server-managed overrides, not on naive text
insertion alone.

## Error Categories

Error reporting should distinguish at least these classes:

- parse error for invalid `SET DEVICE` syntax
- unsupported device for the current tool
- unsupported option or mode for the current tool
- output-path override or capture conflict

For Ghostscript-related failures, the preferred direction is:

- classify the error at the repository/tool layer
- include Ghostscript's own detail output as the lower-level diagnostic detail

Likely Ghostscript-related categories include:

- Ghostscript bounding-box read failure
- Ghostscript raster render failure
- final PNG artifact missing after Ghostscript reported success

This distinction helps the repository stay aligned with the manual while still
keeping the tool surface narrow.

## Relationship To Ghostscript

Ghostscript remains a downstream consumer of the normalized PostScript output.

For `generate_topdrawer_png`, the device policy must ensure:

- Topdrawer writes the PostScript file to a server-controlled temporary path
- Ghostscript reads that path
- the final PNG path is then handled separately from the intermediate PS path

For `generate_topdrawer_postscript`, the same device-normalization process may
still apply, but no Ghostscript conversion is needed.

This means Ghostscript concerns are coupled to output capture and path
authority, but not to the parser itself.

## Ghostscript Surface Direction

The Ghostscript-facing public surface should stay narrow.

Because PostScript output remains available as a first-class artifact, the PNG
generation tool does not need to expose every Ghostscript switch.

The current preferred user-facing Ghostscript-related arguments are:

- `dpi`
- `padding`
- `crop`
- `background`

These map to the highest-value output controls:

- output resolution
- extra whitespace around a cropped plot
- whether to trim output to the detected plot bounding box
- whether the background should be opaque white or transparent

The public surface should avoid exposing raw Ghostscript command switches
directly.

### Background Values

The preferred initial `background` values are:

- `white`
- `transparent`

The expected direction is:

- `white` uses `png16m`
- `transparent` uses `png16malpha`

The exact Ghostscript device names remain an implementation detail unless a
later design note decides they should become user-visible.

The current preferred transparent-background path follows Ghostscript's modern
recommended direction by preferring `png16malpha` over `pngalpha`.

### Crop Behavior

The current preferred meaning of `crop` is:

- `crop=true`: use the PostScript bounding box, trim to plot content, and apply
  `padding`
- `crop=false`: render the full PostScript page using the original PostScript
  page size without bounding-box trimming

When `crop=false`, the current preferred behavior is that `padding` is ignored.

### Default Values

The current preferred defaults are:

- `dpi=160`
- `padding=12` points
- `crop=true`
- `background=white`

These defaults are acceptable as a practical starting point and do not require
an immediate change from the current runtime values.

### Internal Fixed Values

Some Ghostscript behavior should remain server-managed even after the public
surface grows.

Likely internal fixed values or policies include:

- safety and non-interactive execution flags
- the use of a bounding-box read step when cropping is enabled
- the internal translation/page-sizing math used to realize cropped output
- low-level device naming details unless later promoted into the public surface

## Documentation And Guidance Implications

If the implementation stays relatively thin and relies on clear agent behavior,
documentation should explain:

- what the tools do with script-authored `SET DEVICE`
- which outputs are server-managed
- which devices or modes are unsupported by current output tools
- how tool-level restrictions differ from Topdrawer syntax validity

This guidance may need to appear in:

- README surface documentation
- MCP resources for stable reference guidance
- MCP prompts that teach recommended usage flows

## Recommended Near-Term Boundary

The near-term direction should be:

- parse `SET DEVICE` more intentionally
- preserve manual-compatible syntax acceptance as much as practical
- apply separate tool-level policy checks
- keep server authority over execution output paths
- avoid full Topdrawer-language parsing

This gives the repository a more principled render/output pipeline without
expanding into a general Topdrawer execution frontend.

## Result Shape Direction

The success result should remain compact at the top level.

A likely top-level shape is:

- `success`
- `format`
- `message`
- `artifact_id`
- `resource_uri`

Additional lower-priority details should be grouped under:

- `metadata`

This allows the tool surface to expose useful execution details without
overloading the primary result contract.

Examples of metadata candidates include:

- applied `dpi`
- applied `background`
- whether cropping was applied
- the intermediate PostScript path when appropriate
- normalized device-config summary
- whether a script-authored output path was overridden by the server
- whether the source was `input_path`-based or inline `script`

The exact metadata keys remain implementation-level work, but the preferred
structure is to keep optional execution detail inside one `metadata` field.

`output_path` may remain available temporarily as compatibility-oriented
metadata or supplemental output detail, but it should not remain the primary
artifact handoff mechanism.

The preferred direction is to phase the tool surface away from direct local
filesystem paths and toward MCP-readable artifact identifiers and resource
URIs.

## Generated Artifact Management

Generated outputs should be managed as artifact bundles rather than as
standalone files.

One artifact bundle should correspond to one generation request and should
store:

- the primary generated output such as `output.png` or `output.ps`
- the execution-time Topdrawer script used to create that output
- structured metadata such as `metadata.json`

The preferred logical artifact shape is:

- one generated output
- one execution script snapshot
- one metadata record

### Dynamic Resource Direction

The preferred delivery mechanism for generated artifacts is dynamic MCP
resources.

The tool result should primarily hand back:

- `artifact_id`
- `resource_uri`

Possible resource forms include:

- one bundle/manifest resource for the artifact
- one output resource
- one source-script resource
- one metadata resource

The exact URI layout remains implementation work, but the resource-based
handoff should replace direct reliance on local temp paths over time.

### Local Path Compatibility

Direct filesystem paths may still be present during a transition period, but
only as supplemental detail.

The preferred long-term direction is:

- do not require the client or agent to read arbitrary local paths
- do not treat `output_path` as the canonical way to consume a generated
  artifact

### Retention And Cleanup Policy

Generated artifacts should be retained under a bounded temporary storage
policy.

The preferred policy direction is:

- a time-to-live (TTL) limit
- a total storage-size limit
- an artifact-count limit
- automatic cleanup of older artifacts

The preferred cleanup trigger points are:

- server startup
- new artifact creation

When cleanup is needed, the preferred removal order is oldest or least
recently accessed artifacts first.

### Artifact Identity

Artifacts should receive server-generated IDs rather than user-facing names.

The ID should be:

- unique
- safe to embed in resource URIs
- stable for the lifetime of the retained artifact

The exact ID scheme is implementation work, but it should be server-assigned
and not derived from user-provided paths.

### Source Preservation

The preferred source snapshot to retain with an artifact is the execution-time
script that actually drove Topdrawer.

This preserves reproducibility better than storing only the original user input
shape. Additional original-input provenance may be kept in metadata where
helpful.

## Future Provenance Consideration

Embedding provenance into generated PNG files is not an immediate requirement,
but it remains a valid future consideration.

If explored later, the likely purpose would be lightweight generation metadata,
such as:

- generator identity
- generation timestamp
- source kind
- normalized output settings summary

This should be treated as a future enhancement rather than a prerequisite for
the new render/output surface.

## Candidate Next Step

The next focused plan should define:

- the concrete parsed fields for a normalized device config
- the initial tool-policy allow/deny matrix for PNG and PostScript generation
- whether execution uses source rewriting, command-line device injection, or a
  hybrid approach
- the exact result and error shapes exposed by the new tools
- the final Ghostscript public/private control split for PNG generation
- the dynamic artifact resource layout and cleanup implementation
