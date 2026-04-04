# Atoms

Atoms are indices for words or special values.

The atom starting with $ is a variable.

# Tuples

Tuple is a dictionary of key-value atoms.

## match args

Matches the keys with supplied args with variable substitution. If value is not a variable, then values should also match.
If matching is strict then length of tuple and args size should be equal

Examples:
- `{a:1, b:$x} with args {a:1, b:2} => {$x,1}`
- `{a:1, b:$x} with args {a:3, b:2} => None (no match)`
- `{a:1, b:2} with args {a:1, b:2} => {}`
- `{a:1, b:2} with args {a:1} => None (strict) or {} (not strict)`

## get targets

Selects a values filtered by supplied targets.

Example: `{a:1, b:$x, c:$y} with targets [a, b, d] => {a:1, b:$x, d:None}`

## getvars

Returns a list of variables selected from values.

Example: `{a:1, b:$x, c:$y} => [$x, $y]`

# Facts

Fact is a tuple without variables.

# Rules

Rule is a combination of *definition* and *expression*.

Definition is a tuple and expression is a list of tuples. The variables are the same among definition and expression.