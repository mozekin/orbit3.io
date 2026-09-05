# Project J.A.R.V.I.S.

*Just A Rather Very Intelligent System* - a personal voice assistant tailored for
**Mr. Martin Ozekin**. Cultured, unfailingly polite, quietly amused, and always
addresses its principal as "Mr. Ozekin".

```
╭──────────────────────────────────────────────────────────────────────────────╮
│   J.A.R.V.I.S.      STARK INDUSTRIES  //  Just A Rather Very Intelligent System   │
│   PRINCIPAL Mr. Ozekin   MODE LIVE · Gmail + Open-Meteo   VOICE AUTO         │
╰──────────────────────────────────────────────────────────────────────────────╯
◉ All systems nominal.
```

Every run delivers a spoken briefing with three sections:

| Section | Source | What J.A.R.V.I.S. does |
|---|---|---|
| **Auravest signups** | Gmail, `support@auravest.ai` | Parses operational signup notifications (key/value, JSON, HTML table or subject-only formats) into name, email, company, plan and time |
| **Orbit3 task digest** | Gmail, `martin@orbit3.io` | Extracts outstanding tasks (checklists, numbered items, "could you…" requests, TODO subjects) with due dates and priority, and flags urgent communications with the reason |
| **Sydney weather** | Open-Meteo (no key) | Live current conditions and a 3-day forecast for Sydney, NSW, with umbrella advice |

The script is spoken through **ElevenLabs** (British voice, streamed) with an automatic
fallback chain to the host's local text-to-speech and finally a transcript-only mode,
and rendered on a Stark Industries styled console HUD.

## Quick start (no API keys)

```bash
cd jarvis
pip install -r requirements.txt
python -m jarvis --mock
```

`--mock` runs entirely on the bundled fixtures in `mock_data/` (a realistic inbox and
an Open-Meteo payload). No network, no credentials. Use `--no-anim` to skip the boot
animation and typewriter, `--no-hud` for plain text, and `--json` for machine output.

Install as a command with `pip install -e .` and it is available as `jarvis`.

## Live setup

1. **Copy the environment file** and fill in what you have:
   ```bash
   cp .env.example .env
   ```
2. **Google OAuth2 (Gmail read-only)**
   - In [Google Cloud Console](https://console.cloud.google.com/) create or pick a project,
     enable the **Gmail API**, and create an OAuth 2.0 client of type **Desktop app**
     (APIs & Services → Credentials). Add `martin@orbit3.io` as a test user if the consent
     screen is in testing mode.
   - Download the client JSON and save it as `credentials.json` (or point
     `GOOGLE_CREDENTIALS_PATH` at it).
   - Run the consent flow once. A browser opens; the refresh token is stored in `token.json`
     and reused silently afterwards:
     ```bash
     python -m jarvis --auth
     ```
   Only the `gmail.readonly` scope is requested. `credentials.json`, `token.json` and `.env`
   are git-ignored.
3. **ElevenLabs** - set `ELEVENLABS_API_KEY`. The default voice is *Daniel*, a measured
   British voice. To find a dedicated butler voice in your library:
   ```bash
   python -m jarvis --list-voices     # butler / British voices are listed first
   ```
   then set `ELEVENLABS_VOICE_ID`. Audio is streamed from the `/text-to-speech/{voice}/stream`
   endpoint straight into `ffplay`, `mpv` or `mpg123` (auto-detected; override with
   `JARVIS_AUDIO_PLAYER`). Use `--save-audio briefing.mp3` to keep the file instead.
4. **Run it**
   ```bash
   python -m jarvis                      # full live briefing
   python -m jarvis --sections weather   # just the weather
   python -m jarvis --voice local        # skip ElevenLabs
   python -m jarvis --say "The car is ready."
   python -m jarvis --check              # effective config and auth status
   ```

### Voice fallback chain

`--voice auto` (default) tries, in order: **ElevenLabs** (if a key is set and not in mock
mode) → **local TTS** (`say -v Daniel` on macOS, `espeak-ng`/`espeak` with `en-gb`,
`pyttsx3`, or Windows SAPI) → **transcript only**. Each fallback is reported on the HUD.
No key, no player, no local engine? The briefing is still rendered and the transcript shown.

## Layout

```
jarvis/
├── jarvis/
│   ├── cli.py                 # argparse entry point (python -m jarvis / jarvis)
│   ├── config.py              # Settings from env / .env
│   ├── persona.py             # the J.A.R.V.I.S. voice: greetings, wit, narration
│   ├── briefing.py            # assembles sections; isolates connector failures
│   ├── models.py              # dataclasses shared everywhere
│   ├── connectors/
│   │   ├── google_auth.py     # OAuth2 installed-app flow, token cache
│   │   ├── gmail.py           # Gmail API connector + MockMailSource (Gmail query subset)
│   │   └── weather.py         # Open-Meteo client + MockWeatherClient, WMO code table
│   ├── modules/
│   │   ├── auravest.py        # signup notification parser
│   │   ├── orbit3_digest.py   # task / urgency heuristics
│   │   └── weather_report.py  # never-raising weather wrapper
│   ├── voice/
│   │   ├── speaker.py         # ElevenLabs streaming, LocalSpeaker, FallbackSpeaker
│   │   └── players.py         # ffplay / mpv / mpg123 / afplay detection
│   └── hud/console.py         # Stark Industries HUD (rich) + plain fallback
├── mock_data/                 # emails.json, weather.json fixtures
├── tests/                     # pytest suite (90+ tests)
├── .env.example
├── pyproject.toml
└── requirements.txt
```

## Build phases

| Phase | Scope | Where |
|---|---|---|
| 1 | Persona, salutation, settings, models, project scaffold | `persona.py`, `config.py`, `models.py` |
| 2 | Google OAuth2 + Gmail connector, mock mail source, Auravest signup parser | `connectors/google_auth.py`, `connectors/gmail.py`, `modules/auravest.py` |
| 3 | Orbit3 task digest: outstanding tasks and urgent communications | `modules/orbit3_digest.py` |
| 4 | Sydney weather via Open-Meteo, current + 3-day | `connectors/weather.py`, `modules/weather_report.py` |
| 5 | Voice output: ElevenLabs streaming with local fallback chain | `voice/` |
| 6 | Console HUD, briefing assembler, CLI, mock mode, unit tests, CI | `hud/`, `briefing.py`, `cli.py`, `tests/` |

## Tests

```bash
cd jarvis
python -m pytest
```

Everything runs offline: connectors are exercised through fake HTTP sessions and the
bundled fixtures. The GitHub Actions workflow `jarvis-tests.yml` runs the suite on
every push that touches `jarvis/`.

## How the heuristics work

- **Signup parsing** tries an embedded JSON event, `Key: value` lines and rendered HTML
  table rows, then falls back to the subject (`New signup: Name (email)`). Naive timestamps
  are read in Sydney time; `AEST`/`AEDT` suffixes are honoured. Duplicates are collapsed by
  email.
- **Urgency** comes from `Importance: high` / `X-Priority: 1` headers, then keywords in the
  subject, then the first 600 characters of the body (urgent, ASAP, immediately, outage,
  critical/P1/SEV1, overdue, imminent deadlines, security incidents). Newsletters and
  bulk mail (`List-Unsubscribe`, Gmail categories, no-reply senders) are ignored; monitoring
  alerts are not.
- **Tasks** are checklist / numbered lines, "could you / please / we need you to" requests,
  and `TODO:` subjects. Priority is *urgent* when the item itself is urgent (or it is the
  only item in an urgent message), *high* when due today/tomorrow/COB, otherwise *normal*.
  "No rush" demotes. List items inherit a due date only from the sentence that introduces
  the list.
