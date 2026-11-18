#!/usr/bin/env python3
"""Export CRAN machine learning packages as Markdown (requires pyquery)."""

from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen

from pyquery import PyQuery

TASK_VIEW_URL = "https://cran.r-project.org/web/views/MachineLearning.html"


def load_page(url):
    with urlopen(url, timeout=30) as response:
        return PyQuery(response.read())


def collect_packages():
    """Fetch each CRAN package once, ignoring navigation and external links."""
    document = load_page(TASK_VIEW_URL)
    packages = []
    seen = set()
    for anchor in document("li a[href]").items():
        url = urljoin(TASK_VIEW_URL, anchor.attr("href"))
        location = urlsplit(url)
        if location.netloc != "cran.r-project.org":
            continue
        if not location.path.startswith("/web/packages/"):
            continue
        if not location.path.endswith("/index.html"):
            continue
        if location.path in seen:
            continue
        seen.add(location.path)
        name = anchor.text().strip()
        description = load_page(url)("h2").eq(0).text().strip()
        packages.append(" [%s](%s) - %s \n" % (name, url, description))
    return packages


def main():
    # Finish downloads before opening the output, preserving it on fetch errors.
    packages = collect_packages()
    Path("Packages.txt").write_text("".join(packages), encoding="utf-8")


if __name__ == "__main__":
    main()
