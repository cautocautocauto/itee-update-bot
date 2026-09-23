import unittest

from bot import WATCHES, change_excerpt, normalized_content

class MonitorTests(unittest.TestCase):
    def test_home_news_fixture(self):
        page = '<div class="sp-module news-cycle"><div class="sp-module-content"><a href="/news/1">Securities valuation results</a></div></div>'
        content = normalized_content(page, WATCHES[0])
        self.assertIn("Securities valuation results", content)
        self.assertIn("https://itee.dieti.unina.it/", content)

    def test_admission_fixture(self):
        page = '<article class="item-page"><dl class="article-info"><dd>Visite: 12</dd></dl><h2>Ammissione XLII ciclo</h2><p>Informazioni candidati</p></article>'
        content = normalized_content(page, WATCHES[1])
        self.assertIn("Ammissione XLII ciclo", content)
        self.assertNotIn("Visite:", content)

    def test_diff_only_reports_changed_lines(self):
        result = change_excerpt("a\nb", "a\nc")
        self.assertIn("Rimosso:\nb", result)
        self.assertIn("Aggiunto:\nc", result)

    def test_unina_sections_are_separate(self):
        page = """
        <div id="sezione-3"><h2>Scorrimento graduatorie</h2><a href="/documento-1">Scorrimento n. 1</a></div>
        <div id="sezione-4"><h2>Modalità d'iscrizione</h2><a href="/modulo">Con borsa</a></div>
        """
        rankings = normalized_content(page, WATCHES[2])
        enrollment = normalized_content(page, WATCHES[3])
        self.assertIn("Scorrimento n. 1", rankings)
        self.assertNotIn("Con borsa", rankings)
        self.assertIn("Con borsa", enrollment)
        self.assertNotIn("Scorrimento n. 1", enrollment)


if __name__ == "__main__":
    unittest.main()
