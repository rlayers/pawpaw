<!-- Back to top link -->
<a name="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Python][Python-shield]][Python-url]
[![Contributors][contributors-shield]][contributors-url]
[![Watchers][watchers-shield]][watchers-url]
[![Forks][forks-shield]][forks-url]
[![MIT License][license-shield]][license-url]
[![Stargazers][stars-social]][stars-url]
<br />

<!-- ![Pawpaw](svg/title.svg) -->

# Pawpaw  [![High Performance Text Segmentation, Parsing, & Query][byline-img]][repo]

Pawpaw is a high performance parsing & text segmentation framework that allows you to quickly and easily build complex, pipelined parsers.  Segments are automatically organized into tree graphs that can be serialized, traversed, and searched using a powerful structured query language called *plumule*.

<img align="right" width="30%" height="30%" alt="Botanical Drawing: Asimina triloba: the American papaw" src="https://raw.githubusercontent.com/rlayers/pawpaw/master/images/pawpaw.png" /> 

- Indexed string and substring representation
  - Efficient memory utilization
  - Fast processing
  - Pythonic relative indexing and slicing
  - Runtime & polymorphic value extraction
  - Tree graphs for all indexed text
- Search and Query
  - Search trees using plumule: a powerful structured query language similar to XPATH
  - Combined multiple axes, filters, and subqueries sequentially and recursively to any depth
  - Optionally pre-compile queries for increased performance
- Rules Pipelining Engine
  - Develop complex lexical parsers with just a few lines of code
  - Quickly and easily convert unstructured text into structured, indexed, & searchable tree graphs
  - Pre-process text for downstream NLP/AI/ML consumers
- XML Processing
  - Features a drop-in replacement for ElementTree.XmlParser
  - Full text indices for all elements, attributes, tags, text, etc.
  - Search the resulting XML using either XPATH and/or plumule
  - Extract *both* ElementTree and Pawpaw datastructures in one go; with cross-linked nodes between trees
- NLP Support:
  - Pawpaw is ideal for both a) *preprocessing* unstructured text for downstream NLP consumption and b) *storing and searching* NLP generated content
  - Works with other libraries, such as [NLTK](https://www.nltk.org/)
- Efficient pickling and JSON persistence
  - Security option enables persistence of index-only data, with reference strings re-injected during de-serialization 
- Stable & Defect Free
  - Over 4,500 unit tests and counting!
  - Pure python, with only one external dependency: [regex](https://github.com/mrabarnett/mrab-regex)

<div align="center">
  <a href="https://github.com/rlayers/pawpaw/tree/master/docs">Explore the docs</a>
  &nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="https://github.com/rlayers/pawpaw/issues">Request a feature or report a bug</a>
  &nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="https://github.com/rlayers/pawpaw/tree/master/pawpaw">Explore the code</a>
</div>

<!-- EXAMPLE -->
## Example

With Pawpaw, you can start with flattened text like this: 

```
ARTICLE I
Section 1: Congress
All legislative Powers herein granted shall be vested in a Congress of the United States,
which shall consist of a Senate and House of Representatives.

Section 2: The House of Representatives
The House of Representatives shall be composed of Members chosen every second Year by the
People of the several States, and the Electors in each State shall have the Qualifications
requisite for Electors of the most numerous Branch of the State Legislature.

No Person shall be a Representative who shall not have attained to the Age of twenty five
Years, and been seven Years a Citizen of the United States, and who shall not, when elected,
be an Inhabitant of that State in which he shall be chosen.
```

and quickly and easily produce a tree that look like this:

```mermaid
graph TD;
  A1["[article]<br/>#quot;ARTICLE I…#quot;"]:::dark_brown --> A1_k["[key]<br/>#quot;I#quot;"]:::dark_brown;
  A1--->Sc1["[section]<br/>#quot;Section 1…#quot;"]:::light_brown;
  Sc1-->Sc1_k["[key]<br/>#quot;1#quot;"]:::light_brown
  Sc1--->Sc1_p1["[paragraph]<br/>#quot;All legislative Powers…#quot;"]:::peach
  Sc1_p1-->Sc1_p1_s1["[sentence]<br/>#quot;All legislative Powers…#quot;"]:::dark_green
  Sc1_p1_s1-->Sc1_p1_s1_w1["[word]<br/>#quot;All#quot;"]:::light_green
  Sc1_p1_s1-->Sc1_p1_s1_w2["[word]<br/>#quot;legislative#quot;"]:::light_green
  Sc1_p1_s1-->Sc1_p1_s1_w3["[word]<br/>#quot;Powers#quot;"]:::light_green
  Sc1_p1_s1-->Sc1_p1_s1_w4["..."]:::ellipsis

  A1--->Sc2["[section]<br/>#quot;Section 2#quot;"]:::light_brown;
  Sc2-->Sc2_k["[key]<br/>#quot;2#quot;"]:::light_brown
  Sc2--->Sc2_p1["[paragraph]<br/>#quot;The House of…#quot;"]:::peach
  Sc2_p1---->Sc2_p1_s1["[sentence]<br/>#quot;The House of…#quot;"]:::dark_green
  Sc2_p1_s1-->Sc2_p1_s1_w1["[word]<br/>#quot;The#quot;"]:::light_green
  Sc2_p1_s1-->Sc2_p1_s1_w2["[word]<br/>#quot;House#quot;"]:::light_green
  Sc2_p1_s1-->Sc2_p1_s1_w3["[word]<br/>#quot;of#quot;"]:::light_green
  Sc2_p1_s1-->Sc2_p1_s1_w4["..."]:::ellipsis
  Sc2--->Sc2_p2["[paragraph]<br/>#quot;No Person shall…#quot;"]:::peach
  Sc2_p2---->Sc2_p2_s1["[sentence]<br/>#quot;No Person shall…#quot;"]:::dark_green
  Sc2_p2_s1-->Sc2_p2_s1_w1["[word]<br/>#quot;No#quot;"]:::light_green
  Sc2_p2_s1-->Sc2_p2_s1_w2["[word]<br/>#quot;Person#quot;"]:::light_green
  Sc2_p2_s1-->Sc2_p2_s1_w3["[word]<br/>#quot;shall#quot;"]:::light_green
  Sc2_p2_s1-->Sc2_p2_s1_w4["..."]:::ellipsis

  classDef dark_brown fill:#533E30,stroke:#000000,color:#FFFFFF;
  classDef light_brown fill:#D2AC70,stroke:#000000,color:#000000;
  classDef peach fill:#E4D1AE,stroke:#000000,color:#000000;
  classDef dark_green fill:#517D3D,stroke:#000000,color:#FFFFFF;
  classDef light_green fill:#90C246,stroke:#000000,color:#FFFFFF;

  classDef ellipsis fill:#FFFFFF,stroke:#FFFFFF,color:#000000;
```

You can then search your tree using plumule: a powerful structured query language:

 ```python
'**[d:section]{**[d:word] & [lcs:power,right]}'  # Plumule query to find sections that containing words 'power' or 'right'
 ```

Try out [this demo](docs/demos/us_constitution) yourself, which shows how easy it is to parse, visualize, and query the US Constitution using Pawpaw.

<!-- USAGE EXAMPLES -->
## Usage

Pawpaw has extensive features and capabilities you can read about in the [Docs](/Docs).  As a quick example, say you have some text that would like to perform nlp-like segmentation on. 

```python
>>> s = 'nine 9 ten 10 eleven 11 TWELVE 12 thirteen 13'
```

You can use a regular expression for segmentation as follows:

```python
>>> import regex 
>>> re = regex.compile(r'(?:(?P<phrase>(?P<word>(?P<char>\w)+) (?P<number>(?P<digit>\d)+))\s*)+')
```
 
You can then use this regex to feed **Pawpaw**:

 ```python
>>> import pawpaw 
>>> doc = pawpaw.Ito.from_match(re.fullmatch(s))
 ```

With this single line of code, Pawpaw generates a fully hierarchical, tree of phrases, words, chars, numbers, and digits.  You can visualize the tree:

```python
>>> tree_vis = pawpaw.visualization.pepo.Tree()
>>> print(tree_vis.dumps(doc))
(0, 45) '0' : 'nine 9 ten 10 eleven…ELVE 12 thirteen 13'
├──(0, 6) 'phrase' : 'nine 9'
│  ├──(0, 4) 'word' : 'nine'
│  │  ├──(0, 1) 'char' : 'n'
│  │  ├──(1, 2) 'char' : 'i'
│  │  ├──(2, 3) 'char' : 'n'
│  │  └──(3, 4) 'char' : 'e'
│  └──(5, 6) 'number' : '9'
│     └──(5, 6) 'digit' : '9'
├──(7, 13) 'phrase' : 'ten 10'
│  ├──(7, 10) 'word' : 'ten'
│  │  ├──(7, 8) 'char' : 't'
│  │  ├──(8, 9) 'char' : 'e'
│  │  └──(9, 10) 'char' : 'n'
│  └──(11, 13) 'number' : '10'
│     ├──(11, 12) 'digit' : '1'
│     └──(12, 13) 'digit' : '0'
├──(14, 23) 'phrase' : 'eleven 11'
│  ├──(14, 20) 'word' : 'eleven'
│  │  ├──(14, 15) 'char' : 'e'
│  │  ├──(15, 16) 'char' : 'l'
│  │  ├──(16, 17) 'char' : 'e'
│  │  ├──(17, 18) 'char' : 'v'
│  │  ├──(18, 19) 'char' : 'e'
│  │  └──(19, 20) 'char' : 'n'
│  └──(21, 23) 'number' : '11'
│     ├──(21, 22) 'digit' : '1'
│     └──(22, 23) 'digit' : '1'
├──(24, 33) 'phrase' : 'TWELVE 12'
│  ├──(24, 30) 'word' : 'TWELVE'
│  │  ├──(24, 25) 'char' : 'T'
│  │  ├──(25, 26) 'char' : 'W'
│  │  ├──(26, 27) 'char' : 'E'
│  │  ├──(27, 28) 'char' : 'L'
│  │  ├──(28, 29) 'char' : 'V'
│  │  └──(29, 30) 'char' : 'E'
│  └──(31, 33) 'number' : '12'
│     ├──(31, 32) 'digit' : '1'
│     └──(32, 33) 'digit' : '2'
└──(34, 45) 'phrase' : 'thirteen 13'
   ├──(34, 42) 'word' : 'thirteen'
   │  ├──(34, 35) 'char' : 't'
   │  ├──(35, 36) 'char' : 'h'
   │  ├──(36, 37) 'char' : 'i'
   │  ├──(37, 38) 'char' : 'r'
   │  ├──(38, 39) 'char' : 't'
   │  ├──(39, 40) 'char' : 'e'
   │  ├──(40, 41) 'char' : 'e'
   │  └──(41, 42) 'char' : 'n'
   └──(43, 45) 'number' : '13'
      ├──(43, 44) 'digit' : '1'
      └──(44, 45) 'digit' : '3'
```
 
And you can search the tree using Pawpaw's *plumule*, a powerful XPATH-like structured query language:

 ```python
 >>> print(*doc.find_all('**[d:digit]'), sep=', ')  # all digits
9, 1, 0, 1, 1, 1, 2, 1, 3
 >>> print(*doc.find_all('**[d:number]{</*[s:i]}'), sep=', ')  # all numbers with 'i' in their name
9, 13
 ```

This example uses regular expressions as a source, however, Pawpaw is able to work with many other input types.  For example, you can use libraries such as [NLTK](https://www.nltk.org/) to grow Pawpaw trees, or, you can use Pawpaw's included parser framework to build your own sophisticated parsers quickly and easily.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Pawpaw has been written and tested using Python 3.10.  The only dependency is
``regex``, which will be fetched and installed automatically if you install Pawpaw
with pip or conda.

### Installation Options

There are lots of ways to install Pawpaw.  Versioned instances that have passed all automated tests are available from [PyPI](https://pypi.org/project/pawpaw/):

1. Install with pip from PyPI:  
   ```
   pip install pawpaw
   ```
   
2. Install with conda from PyPI:
   ```
   conda activate myenv
   conda install git pip
   pip install pawpaw
   ```

Alternatively, you can pull from the main branch at GitHub.  This will ensure that you have the latest code, however, the main branch can potentially have internal inconsistencies and/or failed tests:

1. Install with pip from GitHub:
   ```
   pip install git+https://github.com/rlayers/pawpaw.git
   ```

2. Install with conda from GitHub:
   ```
   conda activate myenv
   conda install git pip
   pip install git+https://github.com/rlayers/pawpaw.git
   ```

3. Clone the repo with git from GitHub:
   ```
   git clone https://github.com/rlayers/pawpaw
   ```
   
### Verify Installation

Whichever way you fetch Pawpaw, you can easily verify that it is installed correctly.  Just open Python prompt and type:

```python
>>> from pawpaw import Ito
>>> Ito('Hello, World!')
Ito(span=(0, 13), desc='', substr='Hello, World!')
```
  
If your last line looks like this, you are up and running with Pawpaw!

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- HISTORY & ROADMAP -->
## History & Roadmap

Pawpaw is a rewrite of *desponia*, a now-deprecated Python 2.x segmentation framework that was itself based on a prior framework called *Ito*.  Currently in release-candidate status, many components and features are production ready.  However, documentation is still being written and some newer features are still undergoing work.  A rough outline of which components are finalized is as follows:

- [x] arborform
  - [x] itorator
    - [x] Desc
    - [x] Extract
    - [x] Reflect
    - [x] Split
    - [x] ValueFunc
  - [x] postorator
    - [x] StackedReduce
    - [x] WindowedJoin
- [x] core
  - [x] Errors
  - [x] Infix
  - [x] Ito
  - [x] ItoChildren
  - [x] nuco
  - [x] Span
  - [x] Types
- [ ] documentation & examples
- [x] query
  - [x] radicle query engine
  - [x] plumule
- [ ] nlp
- [x] visualization
  - [x] ascibox
  - [x] highlighter
  - [x] pepo
  - [x] sgr
- [x] xml
  - [x] XmlHelper
  - [x] XmlParser

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
## Contributing

Contributions to Pawpaw are **greatly appreciated** - please refer to the [contributing guildelines](/contributing.md) for details.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LICENSE -->
## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACTS -->
## Contacts

Robert L. Ayers:&nbsp;&nbsp;<a alt="e-mail" href="email@a.nov.guy@gmail.com">a.nov.guy@gmail.com</a>
<!-- &nbsp;&nbsp;&nbsp;[☕ Buy me a coffee](https://ko-fi.com/jlawrence) -->

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- REFERENCES -->
## References

* [Matthew Barnett's regex](https://github.com/mrabarnett/mrab-regex)
* [NLTK](https://www.nltk.org/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

<!-- Palette Info:
  "Oriental Beauty"
  533E30	D2AC70	E4D1AE	517D3D	90C246
  https://www.schemecolor.com/oriental-beauty-color-combination.php
-->

[repo]: https://github.com/rlayers/pawpaw

[byline-img]: https://img.shields.io/badge/-High%20Performance%20Text%20Segmentation%2C%20Parsing%2C%20%26%20Query-FFFFFF

[byline2-img]: https://readme-typing-svg.demolab.com?font=Fira+Code&weight=800&duration=500&pause=1500&color=533E30&vCenter=true&width=375&height=25&lines=High+Performance+Text+Segmentation

[Python-shield]: https://img.shields.io/badge/python-≥3.10-517D3D.svg?style=flat
[Python-url]: https://www.python.org

[contributors-shield]: https://img.shields.io/github/contributors/rlayers/pawpaw.svg?color=90C246&style=flat
[contributors-url]: https://github.com/rlayers/pawpaw/graphs/contributors

[watchers-shield]: https://img.shields.io/github/watchers/rlayers/pawpaw.svg?color=E4D1AE&style=flat
[watchers-url]: https://github.com/rlayers/pawpaw/watchers

[issues-shield]: https://img.shields.io/github/issues/rlayers/pawpaw.svg?style=flat
[issues-url]: https://github.com/rlayers/pawpaw/issues

[forks-social]: https://img.shields.io/github/forks/rlayers/pawpaw.svg?style=social
[forks-shield]: https://img.shields.io/github/forks/rlayers/pawpaw.svg?color=D2AC70&style=flat
[forks-url]: https://github.com/rlayers/pawpaw/network/members

[license-shield]: https://img.shields.io/github/license/rlayers/pawpaw.svg?color=533E30&style=flat
[license-url]: https://github.com/rlayers/pawpaw/blob/master/LICENSE

[stars-social]: https://img.shields.io/github/stars/rlayers/pawpaw.svg?style=social
[stars-shield]: https://img.shields.io/github/stars/rlayers/pawpaw.svg?style=flat
[stars-url]: https://github.com/rlayers/pawpaw/stargazers

[PyCharm-shield]: https://img.shields.io/badge/PyCharm-000000.svg?&style=flat&logo=PyCharm&logoColor=white
[PyCharm-url]: https://www.jetbrains.com/pycharm/
