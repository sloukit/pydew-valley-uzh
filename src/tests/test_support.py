import os
import unittest
from unittest import mock

import src.support as support


class TestLoadTranslations(unittest.TestCase):

    @mock.patch.dict(
        os.environ,
        {"GAME_LANGUAGE": "en"},
        clear=True,
    )
    def test_english(self):
        tr = support.load_translations()
        self.assertEqual(tr['enter_play_token'], "Please enter token:")

    @mock.patch.dict(
        os.environ,
        {"GAME_LANGUAGE": "de"},
        clear=True,
    )
    def test_german(self):
        tr = support.load_translations()
        self.assertEqual(tr['enter_play_token'], "Bitte Token eingeben:")
