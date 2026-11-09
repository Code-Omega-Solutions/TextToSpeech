# Data model: Language selection

A speech request contains input text and an optional explicit supported
language. The resolved locale is an existing supported locale. When no language
is supplied, short input uses the configured default; otherwise supported
classifications select their locales and any other classification selects en-US.
No persisted data or schema changes are introduced.
