# Ambiguous Goal Discovery: make this polar

## Intent

The request describes a goal, not a command name. The agent should reach the
relevant command family through the current discovery surface.

## Expected Workflow

1. Use `discover_topdrawer_command` or an equivalent prompt-guided discovery
   flow.
2. Use `reverse_lookup_commands` with the user's wording.
3. Confirm the best candidate with `lookup_command`.
4. Use `search_manual` only if the reverse lookup candidates or command
   guidance remain ambiguous.
5. Explain which command path should be used before editing the script.

## Required Surface Elements

- `discover_topdrawer_command` prompt or equivalent prompt-guided flow
- `reverse_lookup_commands`
- `search_manual`
- `lookup_command`

## Success

Success means the agent:

- reaches the relevant command family for polar plotting
- does not rely only on hidden prior command knowledge
- can explain why the chosen command path is the right one
