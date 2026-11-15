Use a fenced `states <lifecycle>` block to describe a lifecycle. List each state as `name: one sentence`; mark the entry state `(start)` and terminal states `(final)`. A state can end with `shows <screen-name>` to link it to a `screen` block in this plan.

List transitions as `from -> to: label`, using only declared state names. Every state must be reachable from the start; every state with no outgoing transition must be `(final)`.

Finish with `grid:` and place every state exactly once in a pipe-separated grid, using `.` for an empty cell. Keep to 8 states, 10 transitions, and a grid no larger than 4 columns by 3 rows.
