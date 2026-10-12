"""Catch broken placeholders and template expressions before installing PO files."""
import re
from pathlib import Path
import polib
from lxml import etree

count = 0
for path in (Path(__file__).parent / 'translations').glob('*.po'):
    for entry in polib.pofile(str(path)):
        assert entry.msgstr, (path.name, entry.msgid)
        def placeholders(text):
            return sorted(re.findall(r'%(?:\([^)]+\))?[sdf]|\{\{.*?\}\}', text))
        assert placeholders(entry.msgid) == placeholders(entry.msgstr), (path.name, entry.msgid, 'placeholders')
        if '<' in entry.msgid and '>' in entry.msgid:
            try:
                original = etree.fromstring(('<root>' + entry.msgid + '</root>').encode())
            except etree.XMLSyntaxError:
                continue  # Ordinary text with comparisons is not an XML template.
            translated = etree.fromstring(('<root>' + entry.msgstr + '</root>').encode())
            def expressions(root):
                return sorted((key, value) for element in root.iter() for key, value in element.attrib.items() if key.startswith('t-'))
            assert expressions(original) == expressions(translated), (path.name, entry.msgid, 'template expressions')
        count += 1
print('Validated translation placeholders and template expressions:', count)
