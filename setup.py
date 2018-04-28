import setuptools
import os

def walk(path):
  files = [os.path.join(path, f) for f in os.listdir(path)]
  return (path, files)


setuptools.setup(
  name='slag',
  version="0.1.3",
  description='A distributed micro-blog social network on the block chain.',
  long_description=open('README.md').read().strip(),
  author='John Weachock',
  author_email='jweachock@gmail.com',
  url='https://github.com/scizzorz/slag',
  py_modules=['slag'],
  scripts=['bin/slag'],
  data_files=[
    walk('html'),
    walk('css'),
  ],
  install_requires=list(l.strip() for l in open('requirements.txt') if l),
  include_package_data=True,
  license='MIT License',
  zip_safe=False,
  keywords='git blog',
)
