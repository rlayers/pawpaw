## From:

* [stackoverflow question 75394318](https://stackoverflow.com/questions/75394318/python-text-parsing-to-split-list-into-chunks-including-preceding-delimiters)

## Description

Given the text:

```text
\na\n\nQ So I do first want to bring up exhibit No. 46, which is in the binder 
in front of\nyou.\n\nAnd that is a letter [to] Alston\n& Bird...
\n\nIs that correct?\n\nA This is correct.\n\nQ Okay
```

Split it into separate questions and answers.

* Each Question or Answer starts with ``'\nQ '``, ``'\nA '``, ``'\nQ_'`` or ``'\nA_'``.
* Sometimes the first item in the list may be neither a Question nor Answer, but just random text before the first ``'\Q'`` delimiter.
