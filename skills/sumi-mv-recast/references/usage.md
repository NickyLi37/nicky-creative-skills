# Installation and helper usage

## Sumi Studio

Create a personal skill named `sumi-mv-recast` with the frontmatter name/description and Markdown body from SKILL.md. Add `references/`, `scripts/`, `tests/` and `agents/` next to it using the workspace text-file tools. Read back the installed files and check `list_user_skills` for parse errors or name shadowing. Supporting paths in SKILL.md are relative to that skill directory.

Invoke `/sumi-mv-recast` with the source interval, approved cast and your budget/fidelity preferences. Existing session instructions remain valid; supplying a budget does not spend it immediately. This skill supplies planning and execution guidance. Sumi generation still requires a connected account, model access, accepted reference assets and an approved quote. Local helper execution also requires a host with Python/FFmpeg; storage of a script in Sumi is not evidence that its runtime can execute it.

Public market publication is separate from personal installation and requires the user's explicit MIT publication agreement. Do not bundle project media with the skill.

## Codex or another filesystem skill host

Copy this complete `sumi-mv-recast` directory into the host's configured skills folder. For Codex, this is normally `$CODEX_HOME/skills` or `~/.codex/skills`. Avoid overwriting another installed version without comparing it. Start a new session if the host does not reload its skill catalog automatically. Invoke `$sumi-mv-recast` with your source and references.

## Helper commands

From the skill directory, with Python 3.10+ and FFmpeg/ffprobe on PATH:

```sh
python3 scripts/media.py --help
python3 scripts/media.py extract full-depth.mp4 shot-depth.mp4 \
  --fps 24000/1001 --start-frame 1200 --end-frame 1296
python3 scripts/media.py inspect final.mp4 \
  --fps 24000/1001 --frames 96 --aspect 4:3 \
  --report final-qa.json
python3 scripts/media.py inspect later-visual-revision.mp4 \
  --fps 24 --frames 240 --aspect 4:3 \
  --audio-baseline approved-master.mp4 --report revision-qa.json
python3 tests/test_media.py
```

Input and output names are examples, not bundled assets. Confirm `--help` for available options. `extract` selects zero-based, end-exclusive decoded frames, rejects overwrite and unsupported timing, and emits silent H.264/yuv420p MP4 at the native geometry/SAR. It decodes from the beginning for correctness; first extract the chosen overall interval, then make shot cuts from that shorter file. It does not preserve floating-point/metric depth values.

`inspect` performs full decode, verifies frame timing/count, dimensions/display aspect and requested constraints, and optionally compares exact AAC payloads plus normalized timing and skip metadata against an approved audio baseline. It cannot judge faces, pose fidelity, choreography, rights or real-player behavior. An `audio-baseline` comparison is appropriate after an audio stream-copy operation, not after deliberately re-encoding the sound.

The synthetic tests generate their own test video/audio in a temporary directory. No MV, identity images, online requests or paid generation are required. Atomic no-overwrite installation relies on local filesystem hard-link support and fails rather than overwriting on unsupported filesystems.
