import unittest

import src.utils as utils


class TestJSONWithCommentsDecoder(unittest.TestCase):
    def setUp(self):
        pass

    def test_normal_json(self):
        text = """
        {
            "test":[
                ["foo", "bar"],
                ["baz", "qux"]
            ]
        }
        """
        expected = {"test": [["foo", "bar"], ["baz", "qux"]]}
        actual = utils.json_loads(text)
        self.assertEqual(expected, actual)

    def test_json_with_lines_commented_out(self):
        text = """
        {
            "test":[
                // ["foo", "bar"],
                ["baz", "qux"]
            ]
        }
        """
        expected = {"test": [["baz", "qux"]]}
        actual = utils.json_loads(text)
        self.assertEqual(expected, actual)

    def test_json_with_trailing_comments(self):
        text = """
        {  // test
            "test":[
                ["foo", "bar"], // trailing comment
                ["baz", "qux"]  // another comment
            ]
        }
        """
        expected = {"test": [["foo", "bar"], ["baz", "qux"]]}
        actual = utils.json_loads(text)
        self.assertEqual(expected, actual)
