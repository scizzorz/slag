# slag

A fresh, static microblog system based on
[modern block chain technologies](https://git-scm.com).

`slag` uses a list of Git repositories ("streams") to generate static HTML
files. The targeted serving platform is
[GitHub Pages](https://pages.github.com), but you can serve them however you
want. [Here](https://scizzorz.github.io) is an example slag
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

## Streams

Each source repository is used as a different "stream" of posts. Slag generates
a "post" from each commit in the stream repositories. A chronologically
descending list of posts is generated for each individual stream as well as a
single combined list of all streams.

Each post pulls its author, timestamp, URL slug, title, and body from the
commit information. The first line of the commit message is used as the post
title, while the rest are used as the post body. Content is formatted using
[Python Markdown](https://pypi.org/project/Markdown/). A number of paragraphs
(specified by `--maxparagraphs`, defaults to `1`) are used as 'preview'
paragraphs in the list views.

### Markdown Extensions

Slag supports some "extensions" (I guess you can call them that?) to work
around some of the features of Git that aren't super ideal
in a blogging system.

#### `!file` or `!code`

If a paragraph starts with `!file` or `!code` followed by a file path that
exists in that commit's repository, Slag will expand the `!file` declaration
into a [syntax-highlighted](http://pygments.org) code block. Slag uses the
version of the file at its current `HEAD` rather than the version of the file
in that commit. This works around Git's ~inability to edit the history~
immutable history feature.

#### `!md`

Like the `!file` extension, if a paragraph starts with `!md` and a file path,
the paragraph is expanded to the contents of the given file and then rendered as
Markdown. Again, Slag uses the version of the file at its current `HEAD`,
enabling you edit posts without having to change your URLs. However, the act of
editing a file will require a commit to the repository, which will then be used
as a new post... so it's not a totally fool-proof workaround. Tough.

## Motivation

Slag started as a personal shitpost project but it actually doesn't seem
terrible. Some features of Git are fairly amenable to use in a blog engine like
this, like me not having to write some database schema or clever file system
layout to generate content from. Plus, it's easy to pull on guest authors or
even include someone else's content in your own slag by adding it as a
submodule.  Neat.
