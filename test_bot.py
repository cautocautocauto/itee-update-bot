import unittest
from pathlib import Path

from bot import WATCHES, change_excerpt, normalized_content


ATTACHMENTS = Path(r"C:\Users\caucc\.codex\attachments")


class MonitorTests(unittest.TestCase):
    def test_home_news_fixture(self):
        path = ATTACHMENTS / "0f637583-3d51-4d46-9993-e047ffe22531" / "Testo incollato.txt"
        content = normalized_content(path.read_text(encoding="utf-8"), WATCHES[0])
        self.assertIn("Securities valuation results", content)
        self.assertIn("https://itee.dieti.unina.it/", content)

    def test_admission_fixture(self):
        path = ATTACHMENTS / "8b362f19-7c18-4070-a010-3eed1a01ec00" / "Testo incollato.txt"
        content = normalized_content(path.read_text(encoding="utf-8"), WATCHES[1])
        self.assertIn("Ammissione XLII ciclo", content)
        self.assertNotIn("Visite:", content)

    def test_diff_only_reports_changed_lines(self):
        result = change_excerpt("a\nb", "a\nc")
        self.assertIn("-b", result)
        self.assertIn("+c", result)


if __name__ == "__main__":
    unittest.main()
