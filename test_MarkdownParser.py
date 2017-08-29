from MarkdownParser import *
import unittest

test_content = """
I hope you'll find this book useful. It's _not_ meant to be a comprehensive
guide to Vimscript. It's meant to get you comfortable enough with the language
to mold Vim to your taste, write some simple plugins for other users, read
other people's code (with regular side-trips to `:help`), and recognize some
of the common pitfalls.

Good luck!

[Next »](/acknowledgements.html)

Made by [Steve Losh](http://stevelosh.com). [License](/license.html). Built
with [Bookmarkdown](http://bitbucket.org/sjl/bookmarkdown/).

# [Learn Vimscript the Hard Way](/)

# Acknowledgements

First I'd like to thank [Zed Shaw](http://zedshaw.com/) for writing [Learn
Python the Hard Way](http://learnpythonthehardway.org/) and making it freely
available. This book's format and writing style is directly inspired by it.

I'd also like to thank the following GitHub and Bitbucket users who sent pull
requests, pointed out typos, raised issues, and otherwise contributed:

  * [aperiodic](https://github.com/aperiodic)
  * [billturner](https://github.com/billturner)
"""


class TestLinkRemoval(unittest.TestCase):

    def test_mdlink(self):
        content = """
Good luck!

[Next »](/acknowledgements.html)

Paragraph
here
""" 
        result = """
Good luck!


Paragraph
here
"""
        proc = RemoveLinks(content)
        print(proc)
        assert proc == result


if __name__ == '__main__':
    unittest.main()
