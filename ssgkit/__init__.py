import markdown
import re
import os, os.path
import json

from ssgkit.util import *
from ssgkit.timeseries import TimeSeries
import ssgkit.template

markdown_extension = re.compile(r'\.(md|mdown|mkdown|markdown)$')
class Page(object):
    def __init__(self, ssg, source_path):
        self.ssg = ssg
        self.source_path = source_path

    def __repr__(self):
        return "(Page %s -> %s)" % (self.source_path, self.output_path())

    def output_path(self):
        ballpark = self.ssg.input_to_output_path(self.source_path)
        if self.should_tuck_into_subdir():
            return markdown_extension.sub('/index.html', ballpark)
        else:
            return markdown_extension.sub('.html', ballpark)

    def should_tuck_into_subdir(self):
        basename = os.path.basename(self.source_path)
        default  = not (basename.startswith('index.') or basename.startswith('404.'))
        return self.frontmatter.get('subdirize', default)

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

    @lazy
    def date(self):
        return self.frontmatter.get('date', self.title)

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
        return self.ssg.renderer.render(self.layout, **self.template_data)

class SSG(object):
    def __init__(self, input_dir = './input', output_dir = './output', layout_dir = '.',
            render_class = ssgkit.template.Renderer):
        self.input_dir  = input_dir
        self.output_dir = output_dir
        self.layout_dir = layout_dir
        self.renderer   = render_class(layout_dir)

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

    def timeseries(self, criteria = lambda x: True):
        return TimeSeries(page for page in self.pages if criteria(page))

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

