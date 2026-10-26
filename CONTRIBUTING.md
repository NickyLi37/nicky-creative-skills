# Add a skill or an example

Keep the repository useful as the collection grows: one self-contained skill folder, one catalog entry, real reviewed examples.

## Add a skill

1. Create `skills/<lowercase-kebab-name>/SKILL.md` with `name` and `description` YAML frontmatter. Explain when to use it, the useful decisions and the actual workflow. Keep supporting prompts, scripts and references in that folder.
2. Test nontrivial helpers and exercise the skill against a realistic request. Record what was and was not verified. Do not describe a successful model request as visually accepted footage.
3. Add an entry to `site/catalog.json`. Use the same `id` as the folder name. Supply a title, description, category, styles, GitHub skill URL, and a published Sumi URL when available (`sumiUrl` may be empty before publication).
4. Add real examples or an empty `examples` array; don't invent a demo. Each example uses a unique `id`, title, description, `video`, `poster`, `durationSeconds`, `aspectRatio` and `audioLabel`.
5. Run the README checks and review the Gallery at desktop and phone widths. Check video start, seek and natural completion. Open a pull request describing the skill and its validation.

Example categories: `Music video`, `Advertising`, `Short film`, `Product demo`, `Animation`, `Image`, `Audio`. Styles describe appearance, such as `Anime`, `Cinematic`, `Photorealistic`, `Stop motion` or `Graphic`. Reuse existing spellings where appropriate. The catalog accepts new meaningful labels; these are examples, not a closed list.

## Add a film to an existing skill

Append to that entry's `examples` array; do not create another copy of the skill. Local media paths are relative to `site/`, for example `media/my-film-preview.mp4`. Stable HTTPS media URLs are also supported. Do not use temporary signed links, secret-bearing URLs or authenticated personal storage.

For a first small demo, keep each committed file below 50 MiB. As the collection grows, host new videos on a suitable stable media service and use their public URLs; avoid accumulating large revised videos in Git history. Preserve the aspect ratio and accurately label silent or shortened previews. Keep high-resolution masters outside this repository.

Only submit media you are entitled to publish. State media attribution and its own reuse terms in `site/media/README.md`; the repository's MIT license does not automatically apply to preview films or posters. Never commit private production reports, credentials, account information, private task/asset IDs or source footage by accident.

## Publish a Sumi listing

The repository and Sumi market are separate publications. Create/update the skill in Sumi, write its supporting files, read them back, then publish under the user's agreed MIT terms. Add the resulting listing URL to `sumiUrl`. A GitHub push does not automatically republish the market listing.

When changing an existing skill, update both destinations deliberately and keep their instructions consistent. Gallery-only changes do not require republishing the skill. The initial skill was published by Nicky Li; contributors should use their own authorized workspace.

## Local development

This is plain HTML/CSS/JavaScript plus Python-standard-library helpers. Use the commands in README; no dependency installation or build is necessary for the Gallery. `site/catalog.json` is the only machine-readable catalog. The short README table is an overview, not a second configuration file.

Contributions to original instructions, documentation and code are under MIT. Media is separately covered by its stated terms.
