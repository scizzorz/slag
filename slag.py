from datetime import datetime
import attr
import click
import jinja2
import markdown2
import os
import pygit2 as git
import shutil
import sys

slag_path, slag_file = os.path.split(__file__)
html_path = os.path.join(slag_path, 'html')
css_path = os.path.join(slag_path, 'css')

env = jinja2.Environment(
  loader=jinja2.FileSystemLoader(html_path),
  autoescape=jinja2.select_autoescape(['html', 'xml']),
)


def markdown_filter(src):
  return markdown2.markdown(src)


def datetime_filter(src, fmt='%b %e, %I:%M%P'):
  if isinstance(src, int):
    src = datetime.fromtimestamp(src)

  return src.strftime(fmt)


env.filters['markdown'] = markdown_filter
env.filters['datetime'] = datetime_filter


def pager(iterable, pagesize):
    page = []
    for i, item in enumerate(iterable):
        page.append(item)
        if ((i + 1) % pagesize) == 0:
            yield page
            page = []
    yield page


@attr.s
class Post:
  repo = attr.ib()
  title = attr.ib()
  body = attr.ib()
  intro = attr.ib()
  time = attr.ib()
  author = attr.ib()
  hash = attr.ib()


@attr.s
class Link:
  title = attr.ib()
  href = attr.ib()


def render(name, *args, **kwargs):
  temp = env.get_template(name)
  return temp.render(*args, **kwargs)


def find_posts(path='.'):
  repo = git.Repository(git.discover_repository(path))

  last = repo[repo.head.target]
  posts = []
  for commit in repo.walk(last.id, git.GIT_SORT_TIME):
    paras = commit.message.split('\n\n')
    title = paras[0]
    intro = ''
    body = ''

    if len(paras) > 1:
      intro = paras[1]
      body = '\n\n'.join(paras[1:])

    posts.append(Post(
      title=title,
      intro=intro,
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
@click.argument('paths', required=True, nargs=-1)
def render_all(paths=['.'], pagesize=16, baseurl=None, target=None, include=[]):
  if baseurl is None:
    baseurl = os.path.join(os.getcwd(), 'target')

  if target is None:
    target = os.path.join(os.getcwd(), 'target')

  include = list(include) + [css_path]
  for path in include:
    target_path = os.path.join(target, os.path.basename(path))
    if os.path.exists(target_path):
      shutil.rmtree(target_path)
    shutil.copytree(path, target_path)

  links = []
  repos = {}
  all_posts = []

  links.append(Link(
    title='/',
    href='index.html',
  ))

  for path in paths:
    posts = find_posts(path)
    name = os.path.basename(os.path.abspath(path))
    repos[name] = posts
    all_posts.extend(posts)
    links.append(Link(
      title=f'/{name}',
      href=f'{name}.html',
    ))

  all_posts.sort(key=lambda x: x.time, reverse=True)

  os.makedirs(target, exist_ok=True)

  def render_pages(posts, href_fn, title_fn):
    posts = list(posts)

    pages = []
    for i in range((len(posts) + (pagesize - 1)) // pagesize):
      pages.append(Link(
        title=f'{i + 1}',
        href=href_fn(i),
      ))

    for i, page in enumerate(pager(posts, pagesize)):
      filename = os.path.join(target, href_fn(i))
      with open(filename, 'w') as fp:
        fp.write(render(
          'list.html',
          title=title_fn(i),
          links=links,
          pages=pages,
          baseurl=baseurl,
          posts=page,
          current_page=href_fn(i),
        ))

  for name, posts in repos.items():
    render_pages(
      posts,
      lambda i: f'{name}.html' if i == 0 else f'{name}-{i + 1}.html',
      lambda i: f'/{name}' if i == 0 else f'/{name} #{i + 1}',
    )

  render_pages(
    all_posts,
    lambda i: 'index.html' if i == 0 else f'page-{i + 1}.html',
    lambda i: '/' if i == 0 else f'/ #{i + 1}',
  )

  for post in all_posts:
    filename = os.path.join(target, f'{post.hash}.html')
    with open(filename, 'w') as fp:
      fp.write(render(
        'single.html',
        title=post.title,
        links=links,
        baseurl=baseurl,
        post=post,
      ))

if __name__ == '__main__':
  render_all()
