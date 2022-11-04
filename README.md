<!-- Back to top link -->
<a name="readme-top"></a>


<!-- PROJECT SHIELDS -->
[![Python][Python.org]][Python-url]
[![Contributors][contributors-shield]][contributors-url]
[![Stargazers][stars-shield]][stars-url]
[![Watchers][watchers-shield]][watchers-url]
[![MIT License][license-shield]][license-url]
<!--
[![Forks][forks-shield]][forks-url]
[![Issues][issues-shield]][issues-url]
-->

<!-- PROJECT LOGO -->
<!--
<br />
<div align="center">
  <a href="https://github.com/rlayers/3">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>
</div>
-->

<h1 align="center">ito-segments</h1>
<div align="center"><strong>High Performance Text Processing & Segmentation Framework</strong></div>


<!-- Overivew -->
## Overview
- Indexed str and substr representation
  - Efficient memory utilization
  - Fast processing
  - Pythonic relative indexing and slicing of segments
  - Runtime & polymorphic value extraction
  - All non-modifying str and regex methods duplicated within framework    
  - Extensive use of Python generators
- Efficient pickling and JSON persistance
  - Security option enables persistance of index-only data, with refrence strings re-injected during de-serialziation 
- Rules Pipelining Engine
  - Quickly and easily convert unstructured text into structed, indexed, & searchable collections
  - Develop complex text parsers with just a few lines of code
  - Easily pre-process text for downstream NLP/AI/ML consumers
- Search and Query
  - Hierarchical data structure for all indexed text
  - Search using extensive structured query language
  - Optionally pre-compile queries for reuse to improvement performance
- XML Processing
  - Features a drop-in replacement for ElementTree.XmlParser
  - Full text indexes for all Elements, Attributes, Tags, Text, etc. within a document
  - Search the resulting XML using both XPATH and the included, structured query language
- Stable
  - Over 2,000 unit tests and counting!

<div align="center">
  <a href="https://github.com/rlayers/ito-segments/tree/master/docs">Explore the docs</a>
  &nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="https://github.com/rlayers/ito-segments/issues">Report Bug</a>
  &nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="https://github.com/rlayers/ito-segments/issues">Request Feature</a>
</div>

```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li><a href="#usage">Overivew</a></li>
    <li><a href="#usage">About</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#roadmap"Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>


<!-- USAGE EXAMPLES -->
## Usage

Use this space to show useful examples of how a project can be used. Additional screenshots, code examples and demos work well in this space. You may also link to more resources.

_For more examples, please refer to the [Documentation](docs)_

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```

### Installation

_Below is an example of how you can instruct your audience on installing and setting up your app. This template doesn't rely on any external dependencies or services._

1. Get a free API Key at [https://example.com](https://example.com)
2. Clone the repo
   ```sh
   git clone https://github.com/your_username_/Project-Name.git
   ```
3. Install NPM packages
   ```sh
   npm install
   ```
4. Enter your API in `config.js`
   ```js
   const API_KEY = 'ENTER YOUR API';
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- ROADMAP -->
## Roadmap

- [ ] Feature 1
- [ ] Feature 2
- [ ] Feature 3
    - [ ] Nested Feature

See the [open issues](issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Robert L. Ayers: <a alt="e-mail" href="email@a.nov.guy@gmail.com">a.nov.guy@gmail.com</a>

Project Link: [https://github.com/rlayers/ito-segments](https://github.com/rlayers/ito-segments)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Matthew Barnett's regex](https://bitbucket.org/mrabarnett/mrab-regex)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[Python.org]: https://img.shields.io/badge/python-3.10-blue.svg?style=for-the-badge&logo=angular&logoColor=white
[Python-url]: https://www.python.org
[contributors-shield]: https://img.shields.io/github/contributors/rlayers/ito-segments.svg?style=for-the-badge
[contributors-url]: https://github.com/rlayers/ito-segments/graphs/contributors
[stars-shield]: https://img.shields.io/github/stars/rlayers/ito-segments.svg?style=for-the-badge
[stars-url]: https://github.com/rlayers/ito-segments/stargazers
[issues-shield]: https://img.shields.io/github/issues/rlayers/segments.svg?style=for-the-badge
[watchers-shield]: https://img.shields.io/github/watchers/rlayers/ito-segments.svg?style=for-the-badge
[watchers-url]: https://github.com/rlayers/ito-segments/watchers
[license-shield]: https://img.shields.io/github/license/rlayers/ito-segments.svg?style=for-the-badge
[license-url]: https://github.com/rlayers/ito-segments/blob/master/LICENSE


[forks-shield]: https://img.shields.io/github/forks/rlayers/ito-segments.svg?style=for-the-badge
[forks-url]: https://github.com/rlayers/ito-segments/network/members
[issues-url]: https://github.com/rlayers/ito-segments/issues
[product-screenshot]: images/screenshot.png

[Anaconda-shield]: https://anaconda.org/conda-forge/mlconjug/badges/version.svg
[Anaconda-url]: https://anaconda.org
[PyCharm-shield]: https://img.shields.io/badge/PyCharm-000000.svg?&style=for-the-badge&logo=PyCharm&logoColor=white
[PyCharm-url]: https://www.jetbrains.com/pycharm/
