import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pyquery import PyQuery

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pull_R_packages.py"
spec = importlib.util.spec_from_file_location("pull_r_packages", SCRIPT)
scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scraper)


class ScraperTests(unittest.TestCase):
    def test_all_package_links_are_collected_once(self):
        page = PyQuery('''<ul><li>No link</li><li>
          <a href="https://example.org">External</a>
          <a href="../packages/one/index.html"><b>one</b></a>
          <a href="../packages/two/index.html">two</a>
          <a href="../packages/one/index.html">one</a>
          <a href="../views/Other.html">Other view</a>
        </li></ul>''')
        with patch.object(scraper, "load_page", side_effect=[
            page, PyQuery('<h2>one: A &amp; B</h2>'),
            PyQuery('<h2>two: Unicode café</h2>'),
        ]) as load:
            rows = scraper.collect_packages()
        self.assertEqual(rows, [
            ' [one](https://cran.r-project.org/web/packages/one/index.html) - one: A & B \n',
            ' [two](https://cran.r-project.org/web/packages/two/index.html) - two: Unicode café \n',
        ])
        self.assertEqual(load.call_count, 3)

    def test_download_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "Packages.txt"
            output.write_text("existing output", encoding="utf-8")
            with patch.object(scraper, "collect_packages", side_effect=OSError("offline")):
                with patch.object(scraper, "Path", return_value=output):
                    with self.assertRaises(OSError):
                        scraper.main()
            self.assertEqual(output.read_text(encoding="utf-8"), "existing output")

    def test_download_uses_python3_api_and_closes_response(self):
        with patch.object(scraper, "urlopen") as open_url:
            response = open_url.return_value.__enter__.return_value
            response.read.return_value = b'<h2>Package title</h2>'
            self.assertEqual(scraper.load_page(scraper.TASK_VIEW_URL)("h2").text(), "Package title")
            open_url.assert_called_once_with(scraper.TASK_VIEW_URL, timeout=30)
            open_url.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
