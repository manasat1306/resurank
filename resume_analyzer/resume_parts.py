import re

from .resume_quality import detect_sections, SKILL_KEYS, EXPERIENCE_KEYS

BULLETS = ('•', '-', '–', '●', '▪', '*')
MONTH = r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*'
DATE_RANGE = re.compile(
    r'(?:' + MONTH + r')?(?:19|20)\d{2}\s*(?:-|–|—|to)\s*'
    r'(?:(?:' + MONTH + r')?(?:19|20)\d{2}|present|current|ongoing)',
    re.I,
)
YEAR = re.compile(r'\b(?:19|20)\d{2}\b')
DEGREE = re.compile(
    r'\b(b\.?\s?tech|b\.?\s?e|b\.?\s?sc|bca|bba|b\.?\s?com|m\.?\s?tech|m\.?\s?sc|'
    r'mca|mba|m\.?\s?e|ph\.?d|bachelor|master|diploma|intermediate|12th|10th|hsc|ssc)\b',
    re.I,
)
GRADE = re.compile(
    r'(?:(?:cgpa|gpa)\s*[:\-]?\s*\d+(?:\.\d+)?(?:\s*/\s*10)?)|(?:\d+(?:\.\d+)?\s*%)',
    re.I,
)
TECH_LINE = re.compile(r'^(tech(nologies)?(\s+stack)?|built with|tools)\s*[:\-]', re.I)
MONTH_YEAR = re.compile(r'(?:' + MONTH + r')?(?:19|20)\d{2}', re.I)
URL = re.compile(r'https?://[^\s|·]+')
TECH_ANY = re.compile(r'tech(?:nologies)?(?:\s+stack)?\s*:\s*(.+)$', re.I)
SPACE_FIX = re.compile(r'\b(of|in|and|using|with|for)(?=[A-Z])')


def _is_bullet(line):
    return line.strip().startswith(BULLETS)

def _fix(text):
    text = SPACE_FIX.sub(r'\1 ', text)
    return re.sub(r'(?<=\w)&(?=\s)', ' &', text)


def _clean(line):
    return _fix(line.strip().lstrip('•-–●▪* ').strip())


def _strip_dates(text):
    text = DATE_RANGE.sub('', text)
    text = MONTH_YEAR.sub('', text)
    text = text.replace('()', '')
    return text.strip(' |,-–—')


def _collect(sections, keys):
    lines = []
    for key in keys:
        lines.extend(sections.get(key, []))
    return lines


def _split_items(text):
    items = []
    for part in re.split(r'[,;|•]', text):
        part = part.strip(' -–')
        if part and len(part) <= 30 and part not in items:
            items.append(part)
    return items


def _group_entries(lines):
    entries = []
    current = None
    for raw in lines:
        if _is_bullet(raw):
            if current is None:
                current = {'lines': [], 'bullets': []}
                entries.append(current)
            current['bullets'].append(_clean(raw))
            continue
        text = raw.strip()
        if current is not None and current['bullets']:
            if text[:1].islower():  # wrapped line of the last bullet
                current['bullets'][-1] += ' ' + text
                continue
            current = None
        if current is None:
            current = {'lines': [], 'bullets': []}
            entries.append(current)
        current['lines'].append(text)
    return entries


def _title_parts(lines):
    joined = ' | '.join(lines)
    match = DATE_RANGE.search(joined)
    dates = match.group(0).strip() if match else ''
    cleaned = [DATE_RANGE.sub('', l).replace('()', '').strip(' |,-–—') for l in lines]
    cleaned = [l for l in cleaned if l]
    title = cleaned[0] if cleaned else ''
    subtitle = ' · '.join(cleaned[1:])
    return title, subtitle, dates


def parse_experience(sections):
    result = []
    for e in _group_entries(_collect(sections, EXPERIENCE_KEYS)):
        title, company, dates = _title_parts(e['lines'])
        if title:
            result.append({'title': title, 'company': company,
                           'dates': dates, 'bullets': e['bullets']})
    return result

def parse_projects(sections):
    result = []
    for e in _group_entries(sections.get('projects', [])):
        name, note, _ = _title_parts(e['lines'])
        name = _fix(name)
        if not name:
            continue
        tech = []
        links = []
        if '|' in name:
            name, rest = name.split('|', 1)
            tech = _split_items(rest)
            name = name.strip()
        bullets = []
        for line in ([note] if note else []) + e['bullets']:
            line = _fix(line)
            found = TECH_ANY.search(line)
            if found:
                tech = _split_items(found.group(1)) or tech
                line = line[:found.start()]
            for url in URL.findall(line):
                url = url.rstrip('.,)')
                label = 'GitHub' if 'github.com' in url else 'Live demo'
                links.append({'label': label, 'url': url})
            line = URL.sub('', line)
            line = re.sub(r'\b(live demo|github|demo|link)\s*:', '', line, flags=re.I)
            line = line.strip(' |·,-–—')
            if line:
                bullets.append(line)
        result.append({'name': name, 'tech': tech, 'links': links, 'bullets': bullets})
    return result


def parse_education(sections):
    entries = []
    pending = ''
    for raw in sections.get('education', []):
        text = _clean(raw)
        if not text:
            continue
        if DEGREE.search(text):
            date_match = DATE_RANGE.search(text)
            grade = GRADE.search(text)
            entries.append({
                'degree': _strip_dates(GRADE.sub('', text)),
                'institution': pending,
                'dates': date_match.group(0).strip() if date_match else ', '.join(YEAR.findall(text)),
                'grade': grade.group(0).strip() if grade else '',
            })
            pending = ''
        elif entries:
            last = entries[-1]
            if not last['institution']:
                last['institution'] = _strip_dates(GRADE.sub('', text))
            if not last['dates']:
                date_match = DATE_RANGE.search(text)
                last['dates'] = date_match.group(0).strip() if date_match else ', '.join(YEAR.findall(text))
            if not last['grade']:
                grade = GRADE.search(text)
                last['grade'] = grade.group(0).strip() if grade else ''
        else:
            pending = _strip_dates(text)
    return entries

def parse_certifications(sections):
    result = []
    for raw in sections.get('certifications', []):
        text = _clean(raw)
        if not text:
            continue
        if _is_bullet(raw) and result:
            result[-1]['details'].append(text)
            continue
        found = MONTH_YEAR.search(text)
        result.append({
            'name': _strip_dates(text),
            'date': found.group(0).strip() if found else '',
            'details': [],
        })
    return result


def parse_technologies(sections, required=None, preferred=None):
    required = [str(s).lower().strip() for s in (required or [])]
    preferred = [str(s).lower().strip() for s in (preferred or [])]

    def mark(name):
        low = name.lower().strip()
        status = 'required' if low in required else ('preferred' if low in preferred else '')
        return {'name': name, 'status': status}

    groups = []
    other = []
    for raw in _collect(sections, SKILL_KEYS):
        text = _clean(raw)
        if ':' in text:
            label, rest = text.split(':', 1)
            items = _split_items(rest)
            if items:
                groups.append({'category': label.strip().title(),
                               'items': [mark(i) for i in items]})
        else:
            other.extend(_split_items(text))
    if other:
        groups.append({'category': 'Other', 'items': [mark(i) for i in other]})
    return groups


def extract_resume_parts(text, required=None, preferred=None):
    sections = detect_sections(text)
    return {
        'education': parse_education(sections),
        'experience': parse_experience(sections),
        'projects': parse_projects(sections),
        'certifications': parse_certifications(sections),
        'technologies': parse_technologies(sections, required, preferred),
    }