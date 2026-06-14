# Script Command Discovery V1 Design

## Goal

Define a narrow v1 flow for agent use of the MCP server around existing
Topdrawer scripts.

The primary workflow is:

1. scan a script to extract recognized command names
2. look up those commands for reviewed guidance
3. when the command name is still unknown, use a simple reverse lookup from
   script/user words to command candidates

## Scope

This design covers only the v1 discovery flow around:

- `scan_topdrawer_script`
- `scan_topdrawer_file`
- `lookup_command`
- one future reverse-lookup tool for command candidates

It does not redefine the broader repository roadmap, render pipeline, or
tabular-data questions already covered elsewhere.

## Intended V1 Behavior

### Scanner role

The scanner should stay narrow.

Its primary job is to extract recognized command occurrences from a script, not
to act as a general validator or parser.

For v1, the scanner remains useful when it returns:

- normalized command names
- command kind
- line numbers
- optionally the matched raw line text

Existing lightweight warnings may remain, but warning expansion is not the main
goal of this batch.

### Lookup role

`lookup_command` remains the main source of reviewed command explanation.

The intended agent flow is:

1. use scan results to identify commands present in a script
2. call `lookup_command` for the commands that matter to the current task
3. fall back to manual search only when reviewed command lookup is insufficient

### Reverse-lookup role

V1 should add a simple reverse-lookup path for cases where the agent has a word
or phrase but not yet a command name.

The reverse-lookup tool should return candidate command names to investigate
next. It should be narrower than full manual search and should not try to
replace `lookup_command`.

Example inputs include words taken from:

- user instructions such as "error bars" or "polar"
- script text such as labels, axis terms, or option words

The intended public contract is:

- input: one short query string
- output: a small ordered list of candidate command headings

The tool is meant to support a follow-up `lookup_command` call rather than to
explain the commands by itself.

## Non-Goals

- Do not turn the scanner into a full Topdrawer parser.
- Do not add broad command-order validation.
- Do not infer general data-block structure.
- Do not add generic authoring-from-tabular-data in this batch.
- Do not duplicate large manual excerpts in scan output.

## Design Direction

### 1. Keep scan lightweight

The scanner should be treated as command discovery, not semantic diagnosis.

This keeps the implementation robust against the flexibility of Topdrawer
scripts and avoids low-confidence warnings that would not reliably help agents.

### 2. Make scan feed lookup directly

The command names returned by scan should be directly usable as inputs to
`lookup_command`.

The value of scan is therefore not that it fully explains a script, but that it
reduces a free-form file into a smaller set of command targets for reviewed
lookup.

### 3. Add a narrow reverse-lookup layer

The missing middle layer in the current MCP surface is a tool that maps words
to likely command candidates.

That tool should be intentionally simple and candidate-oriented:

- input: a short query string
- output: a small list of candidate commands
- default candidate limit: `5`
- optional caller-provided max result count

It should search over repository-owned structured command data rather than over
the full manual text alone.

## Reverse-Lookup Specific Direction

### Candidate source

The reverse-lookup layer should search across all currently known command
entries, not only the reviewed subset.

However, reviewed entries should rank more strongly by default because they are
currently the higher-value, more frequently needed command set and usually have
better curated descriptive text.

This is not intended as a separate reviewed-only mode. It is an internal
ranking preference so that the most useful practical commands tend to surface
first.

### Match fields

The reverse-lookup layer should match query text against command-oriented
structured fields such as:

- canonical command name
- aliases
- reviewed title
- reviewed summary
- other short command description text already available in repository-owned
  command data

Parent-command or section metadata may be used as weak supporting signals, but
the tool should stay command-centered rather than becoming section discovery.

### Result shape

The initial result shape should stay narrow:

- an ordered list of candidate command headings only

It should not return:

- full reviewed command payloads
- long explanations
- manual snippets
- section-oriented results

The intended next step is:

1. call reverse lookup
2. inspect returned command names
3. call `lookup_command` on the best candidates

### Ranking intent

The ranking should favor practical narrowing over theoretical completeness.

The desired ordering signals are:

- strong signal:
  - command-name match
  - alias match
  - concise description/title/summary match
- weak signal:
  - parent-command context
  - section context
- preference signal:
  - reviewed/high-value command entries should rise naturally when they match

This should allow flows such as:

- `"polar"` -> `SET POLAR`
- `"error bars"` -> commands such as `SET ORDER` or other likely plotting
  candidates
- `"points and line"` -> plotting candidates such as `JOIN`

The tool does not need to prove that the top candidate is the single correct
command. It only needs to return a short, plausible set that improves the next
`lookup_command` step over going directly to broad manual search.

## Expected Agent Workflows

### Existing script inspection

1. call `scan_topdrawer_file`
2. inspect returned command names
3. call `lookup_command` for relevant commands
4. optionally call `search_manual` for deeper free-text context

### Inline script inspection

1. call `scan_topdrawer_script`
2. inspect returned command names
3. call `lookup_command` for relevant commands

### Word-to-command discovery

1. extract a useful word or short phrase from the user request or script text
2. call the reverse-lookup tool
3. call `lookup_command` on the returned candidates

## Constraints

- Keep the MCP surface small and reviewable.
- Prefer repository-owned structured data over broad new preprocessing unless a
  concrete runtime need requires it.
- Preserve `search_manual` as the plain-text fallback rather than the primary
  structured discovery tool.
- Keep reverse lookup command-only for v1; do not expand it into section lookup
  or general manual topic search.
