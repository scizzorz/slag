from datetime import datetime
import attr
import click
import jinja2
import markdown
import os
import pygit2 as git
import pygments
import pygments.formatters
import pygments.lexers
import shutil
import toml

slag_path, slag_file = os.path.split(__file__)
html_path = os.path.join(slag_path, 'html')
css_path = os.path.join(slag_path, 'css')

env = jinja2.Environment(
  loader=jinja2.FileSystemLoader(html_path),
  autoescape=jinja2.select_autoescape(['html', 'xml']),
)


@attr.s
class Post:
  repo = attr.ib()
  title = attr.ib()
  body = attr.ib()
  time = attr.ib()
  author = attr.ib()
  hash = attr.ib()


@attr.s
class Link:
  title = attr.ib()
  href = attr.ib()


@attr.s
class Code:
  path = attr.ib()
  real_path = attr.ib()
  is_markdown = attr.ib(default=False)

  @property
  def data(self):
    with open(self.real_path, 'rb') as fp:
      return fp.read()


def datetime_filter(src, fmt='%b %e, %I:%M%P'):
  '''Convert a datetime into a human-readable string.'''

  if isinstance(src, int):
    src = datetime.fromtimestamp(src)

  return src.strftime(fmt)


def text_render(src):
  '''Render a paragraph as markdown or an embedded file.'''

  if isinstance(src, Code):
    code = src.data.decode('utf-8')
    if src.is_markdown:
      return markdown.markdown(code)

    lexer = pygments.lexers.get_lexer_for_filename(os.path.basename(src.path))
    formatter = pygments.formatters.HtmlFormatter()
    return f'<strong>{src.path}</strong>\n' + pygments.highlight(code, lexer, formatter)

  return markdown.markdown(src)


env.filters['text'] = text_render
env.filters['datetime'] = datetime_filter


def pager(iterable, page_size):
  '''Slice an iterable into multiple pages, yielding each page as a list.'''

  page = []
  for i, item in enumerate(iterable):
    page.append(item)
    if ((i + 1) % page_size) == 0:
      yield page
      page = []
  yield page


def magic(path, para):
  '''Decide if a paragraph is "magic" or not, ie whether it's an embedded file.

  This could probably be done through a Python-Markdown extension, but...'''

  if para.startswith('!file') or para.startswith('!code'):
    file = para.split(maxsplit=1)[1].strip()
    return Code(
      path=file,
      real_path=os.path.abspath(os.path.join(path, file)),
    )

  if para.startswith('!md'):
    file = para.split(maxsplit=1)[1].strip()
    return Code(
      path=file,
      real_path=os.path.abspath(os.path.join(path, file)),
      is_markdown=True,
    )

  return para


def render_template(name, *args, **kwargs):
  '''Render a Jinja template.'''

  temp = env.get_template(name)
  return temp.render(*args, **kwargs)


def write_template(filename, template_name, *args, **kwargs):
  '''Render a Jinja template and write the results to a file.'''

  with open(filename, 'w') as fp:
    fp.write(render_template(template_name, *args, **kwargs))


def find_posts(path):
  '''Return a list of posts from a given repository.'''

  repo = git.Repository(git.discover_repository(path))

  last = repo[repo.head.target]
  posts = []
  for commit in repo.walk(last.id, git.GIT_SORT_TIME):
    paras = commit.message.split('\n\n')
    title = paras[0]
    body = [magic(path, para) for para in paras[1:]]

    posts.append(Post(
      title=title,
      body=body,
      author=commit.author,
      time=commit.commit_time,
      repo=os.path.basename(os.path.abspath(path)),
      hash=commit.hex,
    ))

  return posts


@click.command()
@click.option('--baseurl', '-u', default=None, help='base url for things')
@click.option('--target', '-t', default=None, help='directory to dump rendered HTML')
@click.option('--include', '-i', multiple=True, default=[], help='additional directory to include')
@click.option('--pagesize', '-s', default=16, help='number of posts per page')
@click.option('--maxparagraphs', '-g', default=1, help='number of paragraphs to display in lists')
@click.option('--config', '-c', default=None, help='config file to load')
@click.argument('paths', nargs=-1)
def render_all(config, **kwargs):
  # decide if the user gave us a config file or not
  # if they did, we'll print errors loading it
  # if not, we won't? seems reasonable to me
  config_given = config is not None
  if config is None:
    config = 'slag.toml'

  # load the config file and use it to update the kwargs
  try:
    with open(config) as fp:
      kwargs.update(toml.load(fp))
  except Exception as exc:
    if config_given:
      print(f'Error while reading {config!r}:')
      print(f'  {exc}')

  # get default kwargs
  baseurl = kwargs.get('baseurl', None)
  include = kwargs.get('include', [])
  page_size = kwargs.get('pagesize', 16)
  paths = kwargs.get('paths', ['.'])
  target = kwargs.get('target', None)
  max_paragraphs = kwargs.get('maxparagraphs', 1)

  if target is None:
    target = os.path.join(os.getcwd(), 'target')

  if baseurl is None:
    baseurl = target

  os.makedirs(target, exist_ok=True)

  # copy all of the included paths to the target
  include = list(include) + [css_path]
  for path in include:
    target_path = os.path.join(target, os.path.basename(path))
    if os.path.exists(target_path):
      shutil.rmtree(target_path)
    shutil.copytree(path, target_path)

  nav = []
  repos = {}
  root = []

  # root link
  nav.append(Link(
    title='/',
    href='',
  ))

  for path in paths:
    # add posts from this path to the repo list
    posts = find_posts(path)
    name = os.path.basename(os.path.abspath(path))
    repos[name] = posts

    # ...and the root list
    root.extend(posts)

    # ...and then add this path to the link
    nav.append(Link(
      title=f'/{name}',
      href=f'{name}.html',
    ))

  # sort root in descending chronological order
  root.sort(key=lambda x: x.time, reverse=True)

  # helper function to paginate a list of posts
  def render_pages(posts, filename_fn, href_fn, title_fn):
    posts = list(posts)

    # generate nav links for each page
    pages = []
    for i in range((len(posts) + (page_size - 1)) // page_size):
      pages.append(Link(
        title=f'{i + 1}',
        href=href_fn(i),
      ))

    # generate HTML for each page
    for i, page in enumerate(pager(posts, page_size)):
      filename = os.path.join(target, filename_fn(i))
      write_template(
        filename,
        'list.html',
        title=title_fn(i),
        nav=nav,
        pages=pages,
        baseurl=baseurl,
        posts=page,
        current_page=href_fn(i),
        max_paragraphs=max_paragraphs,
      )

  # generate pages for each repo
  for name, posts in repos.items():
    render_pages(
      posts,
      lambda i: f'{name}.html' if i == 0 else f'{name}-{i + 1}.html',
      lambda i: f'{name}.html' if i == 0 else f'{name}-{i + 1}.html',
      lambda i: f'/{name}' if i == 0 else f'/{name} #{i + 1}',
    )

  # generate pages for root
  render_pages(
    root,
    lambda i: 'index.html' if i == 0 else f'page-{i + 1}.html',
    lambda i: '' if i == 0 else f'page-{i + 1}.html',
    lambda i: '/' if i == 0 else f'/ #{i + 1}',
  )

  # generate HTML for each individual post
  for post in root:
    filename = os.path.join(target, f'{post.hash}.html')
    write_template(
      filename,
      'list.html',
      title=post.title,
      nav=nav,
      baseurl=baseurl,
      posts=[post],
    )
