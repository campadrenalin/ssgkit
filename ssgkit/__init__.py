import markdown
import re
import os, os.path, errno
import json
from string import Template

markdown_extension = re.compile(r'\.(md|mdown|mkdown|markdown)$')

def slurp(*path):
    with open(os.path.join(*path)) as f:
        return f.read()

def write(path, data):
    # Equivalent to mkdir -p
    os.makedirs(os.path.dirname(path), exist_ok = True)
    with open(path, 'w') as f:
        f.write(data)

class Page(object):
    def __init__(self, ssg, source_path):
        self.ssg = ssg
        self.source_path = source_path
        self._split = None

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

    def split_content(self):
        return self.get_content().split("\n---\n", 1)

    def get_frontmatter(self):
        self._split = self._split or self.split_content()
        if len(self._split) < 2:
            return {}
        if len(self._split) == 2:
            return json.loads(self._split[0])

    @property
    def frontmatter(self):
        return self.get_frontmatter()

    @property
    def layout(self):
        return self.frontmatter.get('layout', 'page.html')

    @property
    def template_data(self):
        f = self.frontmatter
        return dict(f,
            content = markdown.markdown(self.get_md()), 
            title   = f.get('title', os.path.basename(self.source_path)),
        )

    def get_md(self):
        self._split = self._split or self.split_content()
        return self._split[-1]

    def get_html(self):
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
            write(p.output_path(), p.get_html())

        for s in self.static:
            write(
                self.input_to_output_path(s),
                slurp(s),
            )

