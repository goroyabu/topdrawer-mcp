# MCP Resource/Prompt Surface Redesign

## Summary

Adjust the MCP surface so it follows the MCP 2025-11-25 resource/prompt split
more closely.

- keep `resources` limited to stable reviewed command data
- move workflow guidance responsibility fully onto `prompts`
- replace `topdrawer://...` command resources with hierarchical
  `resource://commands/...` URIs

## Implementation Steps

1. Remove guide resources from the server surface and keep only command data
   resources.
2. Redesign command resource URIs as canonical hierarchical paths:
   - `resource://commands/index`
   - `resource://commands/{command}`
   - `resource://commands/{parent}/{command}`
3. Build command-path mapping from the reviewed command lookup index rather
   than parsing command names from raw URIs.
4. Add `uri` fields to command-index entries so clients can follow index results
   directly into `resources/read`.
5. Keep `inspect_topdrawer_script` and `discover_topdrawer_command` as the
   workflow-discovery surface.
6. Update README and MCP integration tests to the new surface.

## Verification

- unit tests for resource listing, command-resource lookup, and prompt exposure
- Inspector integration tests for `resources/list`,
  `resources/templates/list`, `resources/read`, `prompts/list`, and
  `prompts/get`

## Defaults

- alias-specific resource URIs are not added in this batch
- nested command resources use two URI templates because the current FastMCP
  implementation does not accept wildcard template parameters here
- `lookup_command` behavior remains unchanged
- command resource payload shape stays aligned with the existing reviewed lookup
  entry
