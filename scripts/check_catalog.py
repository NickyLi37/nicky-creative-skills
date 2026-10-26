"""Validate the local gallery catalogue without contacting external services."""
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f'{label}: expected nonempty text')
    return value


def https_url(value, label):
    text(value, label)
    parts = urlsplit(value)
    require(parts.scheme == 'https' and bool(parts.hostname) and not parts.username
            and not parts.password and not any(c.isspace() for c in value),
            f'{label}: expected an HTTPS URL without credentials')


def local_file(base, relative, label):
    decoded = unquote(relative)
    require(not decoded.startswith('/') and '\\' not in decoded
            and '..' not in Path(decoded).parts, f'{label}: unsafe relative path')
    target = (base / decoded).resolve()
    require(target.is_relative_to(base.resolve()), f'{label}: path escapes its directory')
    require(target.is_file(), f'{label}: missing file {relative}')


def media(value, site, label):
    text(value, label)
    parts = urlsplit(value)
    if parts.scheme or parts.netloc:
        https_url(value, label)
    else:
        require(not parts.query and not parts.fragment, f'{label}: local media must be a file path')
        local_file(site, parts.path, label)


def validate_catalog(root):
    root = Path(root)
    data = json.loads((root / 'site/catalog.json').read_text(encoding='utf-8'))
    require(isinstance(data, dict), 'catalogue: expected an object')
    text(data.get('title'), 'title')
    https_url(data.get('repoUrl'), 'repoUrl')
    skills = data.get('skills')
    require(isinstance(skills, list) and bool(skills), 'skills: expected a nonempty list')
    seen_skills, seen_cases = set(), set()
    for skill in skills:
        require(isinstance(skill, dict), 'skill: expected an object')
        slug = text(skill.get('id'), 'skill.id')
        require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', slug), f'{slug}: invalid skill id')
        require(slug not in seen_skills, f'{slug}: duplicate skill id')
        seen_skills.add(slug)
        local_file(root / 'skills', f'{slug}/SKILL.md', slug)
        for key in ('title', 'description', 'category'):
            text(skill.get(key), f'{slug}.{key}')
        styles = skill.get('styles')
        require(isinstance(styles, list), f'{slug}.styles: expected a list')
        for style in styles:
            text(style, f'{slug}.styles')
        require(len(styles) == len(set(styles)), f'{slug}: duplicate style')
        https_url(skill.get('skillUrl'), f'{slug}.skillUrl')
        if skill.get('sumiUrl') not in (None, ''):
            https_url(skill['sumiUrl'], f'{slug}.sumiUrl')
        examples = skill.get('examples')
        require(isinstance(examples, list), f'{slug}.examples: expected a list')
        for example in examples:
            require(isinstance(example, dict), f'{slug}.example: expected an object')
            case_id = text(example.get('id'), f'{slug}.example.id')
            require(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', case_id), f'{case_id}: invalid case id')
            require(case_id not in seen_cases, f'{case_id}: duplicate case id')
            seen_cases.add(case_id)
            for key in ('title', 'description', 'audioLabel'):
                text(example.get(key), f'{case_id}.{key}')
            duration = example.get('durationSeconds')
            require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0,
                    f'{case_id}.durationSeconds: expected a finite positive number')
            ratio = text(example.get('aspectRatio'), f'{case_id}.aspectRatio')
            require(re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*', ratio), f'{case_id}: invalid aspect ratio')
            for key in ('video', 'poster'):
                media(example.get(key), root / 'site', f'{case_id}.{key}')
    return {'skills': len(seen_skills), 'examples': len(seen_cases)}


if __name__ == '__main__':
    try:
        result = validate_catalog(Path(__file__).resolve().parents[1])
    except (OSError, ValueError, TypeError) as error:
        print(f'Catalogue validation failed: {error}', file=sys.stderr)
        sys.exit(1)
    print(f'Catalogue valid: {result["skills"]} skills, {result["examples"]} examples. '
          'Remote resources and media playback were not checked.')
