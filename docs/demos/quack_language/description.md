# Quack

A demonstration of a pawpaw-based language lexer for a programming language I created called 'Quack'.

## Language Features

* an [off-side rule language](https://en.wikipedia.org/wiki/Off-side_rule)
* strongly typed with implicit type detection
* intrisic types:
  * ``bool``
  * ``int``
  * ``float``
  * ``complex``
  * ``char``
  * ``str``

## Expression Boundaries

Like Python, Quack uses indentation to define blocks.  However, whereas Python uses end-of-line (EOL) markers to identify naked[^naked_expression] expression boundaries, Quack uses a combination of EOL and indentation.  This allows an expression to continue on the next line without a continuation operator ('\').

Here is the same, multi-line expression in C, Python, and Quack:

**C**
```C
a = 1 + 2
  + 3;  # semicolon required
```

**Python**
```python
a = 1 + 2 \  # continuation op required
  + 3
```

**Quack**
```python
a = 1 + 2
  + 3  # Ok
```

Expressions start with a non-blank line whose indentation is less than or equal to the prior non-blank line:

Expressions end with when a successive non-blank line is encountered whose indentation less than or equal to the expression's starting line.

This allows long, multi-line expressions to be clearly written:

```quack  
1 + 2      # expr_1
3 + 4      # expr_2
  + 5 + 6  # expr_2 continued
  + 7      # expr_2 continued
8          # expr_3
```

Because an expression's starting line defines the required indent level, successive lines of the same expression can have differing indents:

```quack  
x = 1 + a + f()  # expr_1 start
      + b        # expr_1 continued
  + 2     + g()  # expr_1 continued
  + 3 + c        # expr_1 continued
x = 2 * x        # expr_2
```

Long member chaining can be visually clear:

```quack  
x = [1..20]
    .filter(even)
    .map(lambda i: i * i)
    .reduce(sum)
```


## Code Blocks

Code blocks are always delimited with a semicolon (``:``), after which the next non-blank line *must* have a higher indentation level.  The code block then continues until a non-blank line with indent less than or equal to code block's starting line:

```quack
while(a < b):
  ++a  # in code block
b = a  # not in code block
```

A naked colon is legal, and can be used to define scope boundaries.

```quack
:
  a = 1 + 2
b = 3
```

Code blocks are locally scoped

```quack
:
  a = 1 + 2
b = a  # Error - 'a' not in scope
```
## Control structures

A control structure (CS) boundary starts with a colon (``:``), which must be followed by at least one non-blank line with a relative indent.  The CS ends with the first non-blank line without the relative indent

* Remember that "indent" refers to the indentation at the **start** of the expression defining a CS:

```quack
while a
  and b:   # CS-start
  c        # in CS
d          # CS-stop; outside CS
```

Likewise:

```quack
while a
  and b:    # CS start
    c       # OK; in CS

while a
    and b:  # CS-start
  c         # OK; in CS
```

A naked CS is allowed, which can be used to define scope:

```quack
a = 1
:        # CS-start
  b = a  # in CS
  f(b)   # in CS
--a      # CS-stop; outside CS
```

### if, elif, else

```quack
if a > 3:
  a += a
elif a < 0:
  a = -a
else:
  a *= a
```

### case

Evaluates a value against a one or more values via comparators, executing the first matching block.  When ommitted, the equals comparitor (``==``) is assumed:

**Implicit equals comparitor:**
```quack
case a:
  2:
    ...
  3:
    ...
  else:
    ...
```

**Explicit, mixed operators:**
```quack
case a:
  <= 2:
    ...
  in 3, 4:
    ...
  else:
    ...
```

**Tuple, implicit & explicit operators:**
```quack
case a, b:
  (1, 2):  # implicit '=='
    ...
  in c:    # explicit 'in'
    ...
  else:
    ...
```

### for

```quack  
for a in b:
  ...
```

### while

```quack
while a:
  ...
```

### do while

```quack  
do:
  ...
while a
```

[^naked_expression]: An expression not enclosed in parentheses, brackets, etc.