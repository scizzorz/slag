# slag

A fresh, static microblog system based on
[modern block chain technologies](https://git-scm.com).

`slag` uses a list of Git repositories to generate static HTML files. The
targeted serving platform is [GitHub Pages](https://pages.github.com), but you
can serve them however you want. An example can be seen
[here](https://scizzorz.github.io)
(repository [here](https://github.com/scizzorz/scizzorz.github.io)).

## Installation

    pip install slag

## Usage

    slag [OPTIONS] [PATHS]...

    Options:
      -u, --baseurl TEXT           Base URL for all internal links
      -t, --target TEXT            Directory to dump rendered HTML
      -i, --include TEXT           Additional directories to include
      -s, --pagesize INTEGER       Number of posts to display per page
      -g, --maxparagraphs INTEGER  Number of preview paragraphs to display
      -x, --hrefsuffix             Remove .html suffix from internal links
      -d, --datefmt TEXT           Format to pass to strftime() for dates
      -c, --config TEXT            Config file to load

Config files are specified in TOML. Any options specified on the command line
override the options specified in the config file. By default, a file named
`slag.toml` is loaded as the config.
