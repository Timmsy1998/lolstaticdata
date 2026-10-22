import unittest
from unittest.mock import Mock, patch

import requests

from lolstaticdata.champions.pull_champions_wiki import LolWikiDataHandler


class SkinDataTests(unittest.TestCase):
    @patch("lolstaticdata.champions.pull_champions_wiki.requests.get")
    def test_reads_raw_lua_without_html_and_preserves_strings(self, get):
        get.return_value.text = '''-- <pre>
--[[ Module documentation with return { in a comment. ]]
  return
  {
    ["Aatrox"] = {
      ["id"] = 266, -- Champion ID
      ["skins"] = {
        ["Original"] = { ["id"] = 0, ["lore"] = "<tag> & -- text" },
      },
    },
  }
-- </pre>
'''

        data = LolWikiDataHandler()._get_skins()

        self.assertEqual(data["Aatrox"]["id"], 266)
        self.assertEqual(data["Aatrox"]["skins"]["Original"], {"id": 0, "lore": "<tag> & -- text"})
        get.assert_called_once_with(
            "https://wiki.leagueoflegends.com/en-us/Module:SkinData/data?action=raw", timeout=30
        )
        get.return_value.raise_for_status.assert_called_once_with()

    @patch("lolstaticdata.champions.pull_champions_wiki.requests.get")
    def test_rejects_unexpected_responses(self, get):
        for source in ("<html>Service unavailable</html>", "", "return {}", "return {1, 2}"):
            with self.subTest(source=source):
                get.return_value.text = source
                with self.assertRaisesRegex(ValueError, "Lua skin data table.*action=raw"):
                    LolWikiDataHandler()._get_skins()

    @patch("lolstaticdata.champions.pull_champions_wiki.requests.get")
    def test_http_errors_are_reported_before_parsing(self, get):
        get.return_value = Mock()
        get.return_value.raise_for_status.side_effect = requests.HTTPError("503 Service Unavailable")

        with self.assertRaises(requests.HTTPError):
            LolWikiDataHandler()._get_skins()


if __name__ == "__main__":
    unittest.main()
