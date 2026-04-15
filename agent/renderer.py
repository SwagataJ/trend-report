from __future__ import annotations
import os
from jinja2 import Environment, FileSystemLoader
from .models import TrendReport

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


class HTMLRenderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(os.path.abspath(TEMPLATE_DIR)),
            autoescape=True,
        )

    def render(self, report: TrendReport) -> str:
        template = self.env.get_template("report.html.j2")
        return template.render(report=report)

    def save(self, html: str, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  [renderer] Saved report → {path}")
