"""Guard the editorial boundary and destructive-regeneration regression."""
import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate
import build
class PublicationTests(unittest.TestCase):
    def test_no_automatic_expansion_from_configuration(self):
        self.assertEqual(build.GUIDES, json.loads((ROOT / 'data/reviewed-guides.json').read_text()))
        self.assertNotIn('target_articles', build.SITE['content'])
    def test_incomplete_diagnostic_step_is_rejected(self):
        original = validate.data
        guides = deepcopy(original('reviewed-guides.json'))
        guides[0]['steps'][0]['undo'] = ''
        def fixture(name): return guides if name == 'reviewed-guides.json' else original(name)
        with patch.object(validate, 'data', fixture):
            with self.assertRaisesRegex(AssertionError, 'missing undo'): validate.validate_data()
    def test_unverified_or_non_primary_reference_is_rejected(self):
        original = validate.data
        guides = deepcopy(original('reviewed-guides.json'))
        guides[0]['sources'][0]['url'] = 'https://example.invalid/advice'
        with patch.object(validate, 'data', lambda name: guides if name == 'reviewed-guides.json' else original(name)):
            with self.assertRaisesRegex(AssertionError, 'Non-primary'): validate.validate_data()
    def test_retired_pages_cannot_load_services(self):
        retired = build.page('old/path', 'Retirada', 'Aviso', '<h1>Retirada</h1>', index=False)
        self.assertIn('noindex,follow', retired)
        self.assertNotIn('adsbygoogle', retired)
        self.assertNotIn('googletagmanager', retired)
        self.assertNotIn('application/ld+json', retired)
    def test_metadata_is_escaped(self):
        html = build.page('', '<img src=x>', 'a" onload="bad', '<h1>Contenido</h1>')
        self.assertIn('&lt;img src=x&gt;', html)
        self.assertNotIn('content="a" onload=', html)
if __name__ == '__main__': unittest.main()
