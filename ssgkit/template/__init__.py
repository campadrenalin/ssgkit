# Default implementation uses string.Template in stdlib
from ssgkit.util import slurp
from string import Template
import os

class Renderer(dict):
    def __init__(self, layout_dir):
        filenames = next(os.walk(layout_dir))[-1]
        for f in filenames:
            if not f.endswith('.html'):
                continue
            self[f] = Template(slurp(layout_dir, f))

    def render(self, layout, **kwargs):
        try:
            template = self[layout]
        except KeyError:
            raise KeyError("No such layout file: " + layout)
        return template.substitute(**kwargs)
