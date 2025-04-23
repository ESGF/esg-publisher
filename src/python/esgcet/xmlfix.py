import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError
import re


def is_parseable_xml(s):
    try:
        tree = ET.fromstring(s)
        return True
    except ParseError:
        return False


def fixup_xml(s):
    """
    apply known tweaks to ensure parseable XML
    """
    if is_parseable_xml(s):
        return s

    # replace & with &amp; -- first try to preserve anything that looks like an HTML entity,
    # but if this doesn't work then just replace it unconditionally
    if "&" in s:
        s1 = re.sub("&(?![^\s]+;)", "&amp;", s)
        if is_parseable_xml(s1):
            s = s1
        else:
            s = s.replace('&', '&amp;')

    # add any more fixes here...
        
    if is_parseable_xml(s):
        return s
    else:
        raise Exception("Don't know a way to turn payload into parseable XML")
    
    
if __name__ == '__main__':
    for s in ('<doc><field name="foo">blah</field><field name="bar">blah &lt; blah</field></doc>',
              '<doc><field name="foo">bl & ah</field><field name="bar">blah &lt; blah</field></doc>',
              '<doc><field name="foo">bl & ah</field><field name="bar">blah &stuff; blah</field></doc>',
              '<doc><field name="foo">nohope'):
              print(s)
              print(is_parseable_xml(s))
              print(fixup_xml(s))
              print()
