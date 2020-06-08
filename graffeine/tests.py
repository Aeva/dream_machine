
import unittest
from template_tools import *


class VariousTests(unittest.TestCase):
    def test_rewrite(self):
        before = "{ 「 {{ {「{ }」} }} 」 }"
        after = "{{ { {{{{ {{{{{ }}}}} }}}} } }}"
        got = rewrite(before)
        self.assertEqual(got, after)


    def test_indent(self):
        before = "\n\t\n\ta\na\n\n"
        after = "\n\n\t\ta\n\ta\n\n"
        got = indent(before)
        self.assertEqual(got, after)


    def test_cpp_block_1(self):
        got = cpp_block("prefix", "body", "suffix")
        expected = "prefix\n{\n\tbody\n}suffix"
        self.assertEqual(got, expected)


    def test_cpp_block_2(self):
        got = cpp_block("prefix", ["statement1", "statement2"], "suffix")
        expected = "prefix\n{\n\tstatement1\n\tstatement2\n}suffix"
        self.assertEqual(got, expected)
        

if __name__ == '__main__':
    unittest.main()
