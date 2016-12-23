import markdown
import re
import os, os.path, errno
import json
from string import Template

markdown_extension = re.compile(r'\.(md|mdown|mkdown|markdown)$')

def slurp(*path, mode='r'):
    with open(os.path.join(*path), mode) as f:
        return f.read()

def write(path, data, mode='w'):
    # Equivalent to mkdir -p
    os.makedirs(os.path.dirname(path), exist_ok = True)
    with open(path, mode) as f:
        f.write(data)


def lazy(fn):
    '''
    Decorator that makes a property lazy-evaluated.
    See http://stevenloria.com/lazy-evaluated-properties-in-python/
    '''
    attr_name = '_lazy_' + fn.__name__

    def _getter(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    def _setter(self, value):
        setattr(self, attr_name, value)

    return property(fget=_getter, fset=_setter)

class Page(object):
    def __init__(self, ssg, source_path):
        self.ssg = ssg
        self.source_path = source_path

    def __repr__(self):
        return "(Page %s -> %s)" % (self.source_path, self.output_path())

    def output_path(self):
        ballpark = self.ssg.input_to_output_path(self.source_path)
        if os.path.basename(ballpark).startswith('index.'):
            return markdown_extension.sub('.html', ballpark)
        else:
            return markdown_extension.sub('/index.html', ballpark)

    def get_content(self):
        return slurp(self.source_path)

    @lazy
    def content(self):
        return slurp(self.source_path)

    @lazy
    def split(self):
        return self.content.split("\n---\n", 1)

    @lazy
    def frontmatter(self):
        split = self.split
        if len(split) < 2:
            return {}
        if len(split) == 2:
            return json.loads(split[0])

    @lazy
    def layout(self):
        return self.frontmatter.get('layout', 'page.html')

    @lazy
    def title(self):
        return self.frontmatter.get('title', os.path.basename(self.source_path))

    @property
    def template_data(self):
        '''
        Deliberately not overrideable directly. Can be modified by modifying
        frontmatter or top-level attributes like self.title.
        '''
        f = self.frontmatter
        return dict(f,
            content = markdown.markdown(self.md),
            title   = self.title,
        )

    @lazy
    def md(self):
        return self.split[-1]

    def __str__(self):
        try:
            layout = self.ssg.layouts[self.layout]
        except KeyError:
            raise KeyError("No such layout file: " + self.layout)
        return layout.substitute(**self.template_data)

class SSG(object):
    def __init__(self, input_dir = './input', output_dir = './output', layout_dir = '.'):
        self.input_dir  = input_dir
        self.output_dir = output_dir
        self.layout_dir = layout_dir
        
        self.layouts = {
            f: Template(slurp(self.layout_dir, f))
            for f in next(os.walk(layout_dir))[-1]
            if f.endswith('.html')
        }

        self.pages = []
        self.static = []
        for root, dirs, files in os.walk(self.input_dir):
            self.pages += [
                Page(self, os.path.join(root, f))
                for f in files
                if markdown_extension.search(f)
            ]
            self.static += [
                os.path.join(root, f)
                for f in files
                if not markdown_extension.search(f)
            ]

    def input_to_output_path(self, ip):
        relpath = os.path.relpath(ip, self.input_dir)
        return os.path.join(self.output_dir, relpath)

    def build(self):
        for p in self.pages:
            write(p.output_path(), str(p))

        for s in self.static:
            write(
                self.input_to_output_path(s),
                slurp(s, mode = 'rb'),
                mode = 'wb',
            )

