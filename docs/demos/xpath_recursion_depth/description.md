## From

* [stackoverflow question 51034706](https://stackoverflow.com/questions/51034706/breaking-the-lxml-etree-html-xpath-max-parsing-depth-limit)

## Description

The XPATH parser for lxml.etree has a max depth limit, which can be seen with the following code:

```python
import lxml.etree as etree

# Setup HTML tabs
x = "<span>"
x_ = "</span>"

# Set recursion depth to 255
depth = 255 

# Fails with depth >= 255:
print(etree.HTML(x * depth + "<p>text to be extracted</p >" + x_* depth).xpath("//p//text()"))
```
