export function filterSkills(skills, { query = '', category = '', style = '' } = {}) {
  const words = query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  return skills.filter(skill => {
    const text = [skill.title, skill.description, skill.id, skill.category, ...skill.styles,
      ...skill.examples.flatMap(example => [example.title, example.description])].join(' ').toLocaleLowerCase();
    return (!category || skill.category === category) && (!style || skill.styles.includes(style)) && words.every(word => text.includes(word));
  });
}

export function formatDuration(seconds) {
  const total = Math.round(seconds);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, '0')}`;
}

export function safeUrl(value, base) {
  const url = new URL(value, base);
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Unsupported link protocol');
  return url.href;
}

async function startGallery() {
  const form = document.querySelector('#filters');
  const search = document.querySelector('#search');
  const category = document.querySelector('#category');
  const style = document.querySelector('#style');
  const results = document.querySelector('#results');
  const count = document.querySelector('#result-count');
  const reset = document.querySelector('#clear-filters');
  const empty = document.querySelector('#empty');
  try {
    const response = await fetch('catalog.json');
    if (!response.ok) throw new Error(`Catalog returned ${response.status}`);
    const catalog = await response.json();
    if (!Array.isArray(catalog.skills)) throw new Error('Missing skills');
    const repoUrl = safeUrl(catalog.repoUrl, document.baseURI);
    for (const id of ['repository-link', 'error-repository-link']) document.getElementById(id).href = repoUrl;
    for (const [field, values] of [[category, catalog.skills.map(skill => skill.category)], [style, catalog.skills.flatMap(skill => skill.styles)]]) {
      [...new Set(values)].sort((a, b) => a.localeCompare(b)).forEach(value => field.add(new Option(value, value)));
    }
    function render() {
      const selected = filterSkills(catalog.skills, { query: search.value, category: category.value, style: style.value });
      results.querySelectorAll('video').forEach(video => video.pause());
      results.replaceChildren();
      selected.forEach(skill => {
        const row = document.querySelector('#skill-template').content.cloneNode(true);
        row.querySelector('article').id = skill.id;
        row.querySelector('h3').textContent = skill.title;
        row.querySelector('.skill-description').textContent = skill.description;
        row.querySelector('.skill-key').textContent = `/${skill.id}`;
        [skill.category, ...skill.styles].forEach((tag, index) => {
          const span = document.createElement('span');
          span.className = index ? 'tag' : 'tag tag-category';
          span.textContent = tag;
          row.querySelector('.tags').append(span);
        });
        row.querySelector('.skill-link').href = safeUrl(skill.skillUrl, document.baseURI);
        const sumiLink = row.querySelector('.sumi-link');
        if (skill.sumiUrl) sumiLink.href = safeUrl(skill.sumiUrl, document.baseURI);
        else sumiLink.remove();
        skill.examples.forEach(example => {
          const film = document.querySelector('#example-template').content.cloneNode(true);
          film.querySelector('h4').textContent = example.title;
          film.querySelector('.example-description').textContent = example.description;
          film.querySelector('.example-specs').textContent = `${formatDuration(example.durationSeconds)}  /  ${example.aspectRatio}\n${example.audioLabel}`;
          const video = film.querySelector('video');
          const src = safeUrl(example.video, document.baseURI);
          video.src = src;
          video.poster = safeUrl(example.poster, document.baseURI);
          video.setAttribute('aria-label', example.title);
          if (/^\d+(?:\.\d+)?:\d+(?:\.\d+)?$/.test(example.aspectRatio)) video.style.setProperty('--video-ratio', example.aspectRatio.replace(':', ' / '));
          film.querySelector('.video-download').href = src;
          row.querySelector('.examples').append(film);
        });
        results.append(row);
      });
      const examples = selected.reduce((n, skill) => n + skill.examples.length, 0);
      count.textContent = `${selected.length} ${selected.length === 1 ? 'skill' : 'skills'} · ${examples} ${examples === 1 ? 'film' : 'films'}`;
      empty.hidden = selected.length > 0;
      reset.disabled = !search.value && !category.value && !style.value;
    }
    form.addEventListener('submit', event => event.preventDefault());
    search.addEventListener('input', render);
    category.addEventListener('change', render);
    style.addEventListener('change', render);
    form.addEventListener('reset', () => { search.value = ''; category.value = ''; style.value = ''; render(); });
    document.querySelector('#empty-reset').addEventListener('click', () => { form.reset(); search.focus(); });
    render();
  } catch (error) {
    count.textContent = 'Collection unavailable';
    form.hidden = true;
    results.replaceChildren();
    document.querySelector('#load-error').hidden = false;
    console.error('Unable to load skill gallery:', error);
  }
}

if (typeof document !== 'undefined') startGallery();
