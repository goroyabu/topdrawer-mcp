# Unsupported Direct Function Plot: Gaussian curve

## Intent

The user request is clear, but the current MCP surface does not provide a
direct function-to-curve plotting tool. The scenario checks whether the agent
can avoid inventing one, inspect the available surface, and describe the
closest supported path.

## Expected Workflow

1. Use `discover_topdrawer_command` or a similar discovery-oriented start.
2. Use `reverse_lookup_commands` to find likely plotting command families from
   the request wording.
3. Use `lookup_command` for the most relevant plotting commands, such as
   `PLOT`, `JOIN`, or data-entry-related commands, to confirm what is actually
   supported.
4. Use `search_manual` only if the reverse lookup candidates or command
   guidance still are not enough to resolve the capability question.
5. Explain that direct function plotting is not currently exposed by this MCP
   surface.
6. Describe the closest supported path, such as supplying explicit data points
   and then using a plotting command.

## Required Surface Elements

- `discover_topdrawer_command` prompt or equivalent discovery-oriented flow
- `reverse_lookup_commands`
- `search_manual`
- `lookup_command`
- optional command resources

## Success

Success means the agent:

- does not invent a direct Gaussian plotting feature that is not currently
  exposed
- correctly distinguishes between supported plotting commands and missing
  function-generation capability
- explains the closest supported path in a way that stays within repository
  scope
