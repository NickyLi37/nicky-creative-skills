"""Catalogue trust-boundary tests using temporary text fixtures only."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('check_catalog', Path(__file__).resolve().parents[1] / 'scripts/check_catalog.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'site/media').mkdir(parents=True)
        for name in ('preview.mp4', 'poster.jpg'):
            (self.root / 'site/media' / name).write_text('path-existence fixture only')
        self.skill = {
            'id': 'first-skill', 'title': 'First skill', 'description': 'A reusable process.',
            'category': 'music-video', 'styles': ['anime'],
            'skillUrl': 'https://github.com/example/skills/blob/main/skills/first-skill/SKILL.md',
            'sumiUrl': '', 'examples': [{
                'id': 'first-case', 'title': 'First case', 'description': 'A workflow demonstration.',
                'video': 'media/preview.mp4', 'poster': 'media/poster.jpg',
                'durationSeconds': 132.54, 'aspectRatio': '4:3', 'audioLabel': 'Silent preview'
            }]
        }
        self.data = {'title': 'Creative skills', 'repoUrl': 'https://github.com/example/skills', 'skills': [self.skill]}
        self.add_skill_dir('first-skill')

    def add_skill_dir(self, slug):
        path = self.root / 'skills' / slug
        path.mkdir(parents=True)
        (path / 'SKILL.md').write_text('---\nname: fixture\ndescription: fixture\n---\n')

    def check(self):
        (self.root / 'site/catalog.json').write_text(json.dumps(self.data))
        return CHECK.validate_catalog(self.root)

    def test_multiple_skills_cases_and_optional_market_link(self):
        second = copy.deepcopy(self.skill)
        second.update(id='second-skill', styles=[], sumiUrl='https://sumistudio.ai/en/skills/example')
        second['examples'][0].update(id='second-case', video='https://media.example.test/film.mp4')
        self.data['skills'].append(second)
        self.add_skill_dir('second-skill')
        self.assertEqual(self.check(), {'skills': 2, 'examples': 2})
        second['examples'] = []
        self.assertEqual(self.check(), {'skills': 2, 'examples': 1})

    def test_duplicate_skill_and_global_case_ids(self):
        second = copy.deepcopy(self.skill)
        self.data['skills'].append(second)
        with self.assertRaisesRegex(ValueError, 'duplicate skill'):
            self.check()
        second['id'] = 'second-skill'
        self.add_skill_dir('second-skill')
        with self.assertRaisesRegex(ValueError, 'duplicate case'):
            self.check()

    def test_traversal_and_symlink_escape(self):
        for value in ('../outside.mp4', '%2e%2e/outside.mp4', '/outside.mp4', 'media\\..\\outside.mp4'):
            with self.subTest(value=value):
                self.skill['examples'][0]['video'] = value
                with self.assertRaises(ValueError):
                    self.check()
        (self.root / 'private.mp4').write_text('not public')
        (self.root / 'site/media/link.mp4').symlink_to(self.root / 'private.mp4')
        self.skill['examples'][0]['video'] = 'media/link.mp4'
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.check()

    def test_missing_files_and_bad_urls(self):
        for value in ('media/missing.mp4', 'javascript:alert(1)', 'http://media.example.test/a.mp4', '//media.example.test/a.mp4', 'https://name:secret@example.test/a.mp4'):
            with self.subTest(value=value):
                self.skill['examples'][0]['video'] = value
                with self.assertRaises(ValueError):
                    self.check()
        self.skill['examples'][0]['video'] = 'media/preview.mp4'
        (self.root / 'skills/first-skill/SKILL.md').unlink()
        with self.assertRaisesRegex(ValueError, 'missing file'):
            self.check()

    def test_invalid_metadata(self):
        for value in (0, -1, True, float('inf'), '132'):
            with self.subTest(value=value):
                self.skill['examples'][0]['durationSeconds'] = value
                with self.assertRaisesRegex(ValueError, 'durationSeconds'):
                    self.check()


if __name__ == '__main__':
    unittest.main()
