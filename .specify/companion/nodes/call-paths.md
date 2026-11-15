Use a fenced `calls <behavior>` block for a path that crosses functions or files. Include one entry point at column 0, followed by the calls it makes. Indent each call level by two spaces.

Start each line with `+` for new, `~` for changed, `-` for removed, or a space for unchanged. Then name the function or operation and cite its repository-relative file as `@ path:line`. For a file the change creates, use `**new** @ path` without a line number.

Keep the path concrete and bounded: at most 3 blocks and 12 lines per block.
