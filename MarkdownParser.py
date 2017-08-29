import re

mdlink = re.compile(r"\[(?P<brack>.*?)\]\s*?(\((?P<paren>.*?)\))?")
mdheader = re.compile(r"#+.+")

def string_sub(string, new, first, last):
    return string[:first] + new + string[last:]

def strip_line(content):
    linkmatch = mdlink.sub(content)
    headmatch = mdheader.search(content)
    if linkmatch and headmatch:
        # why?
        return ''
    elif linkmatch:
        pass
        # re.sub
    elif headmatch:
        pass
    else: 
        return content


def processMarkdown(content):
    content = content.split('\n')
    lines = []
    for l in content:
        l = strip_line(l)
    return '\n'.join(lines)



