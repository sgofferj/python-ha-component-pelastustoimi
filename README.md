# Pelastustoimi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Home Assistant integration that monitors Finnish emergency service missions (Pelastustoimi) by polling the [Peto-media RSS feed](https://www.peto-media.fi/tiedotteet/rss.xml). Creates sensor entities per municipality and fires events when new alarms are detected.

## Features

- **RSS polling** — polls the official Pelastustoimi RSS feed at a configurable interval (minimum 1 minute)
- **Municipality filtering** — select one or more Finnish municipalities to monitor; only alarms matching selected municipalities are tracked
- **Sensor entities** — one sensor per municipality showing the number of stored alarms with full alarm details in attributes
- **Event-driven** — fires `pelastustoimi_new_alarm` when a new alarm appears in any configured municipality
- **Full UI configuration** — set up entirely via the Home Assistant integration flow without YAML
- **Reconfigurable** — update interval and municipality list via the Configure button at any time

## Installation

### HACS (recommended)

1. Add this repository as a custom repository in HACS (type: Integration).
2. Search for "Pelastustoimi" and install.
3. Restart Home Assistant.

### Manual

1. Copy `custom_components/pelastustoimi/` to your Home Assistant `custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for "Pelastustoimi" and select it.
3. Configure:
   - **Update interval** — how often to poll the RSS feed (minutes, minimum 1)
   - **Municipalities** — select one or more Finnish municipalities from the list

After setup, you can reconfigure any option via **Configure** on the integration card.

## Sensor Attributes

Each municipality sensor displays:
- **State**: number of stored alarms
- **Attributes**:
  - `alarms` — list of alarm objects, each containing:
    - `title` — RSS item title
    - `description` — RSS item description (timestamp, municipality, incident type)
    - `pub_date` — publication date from RSS
    - `municipality` — combined label (`NAMEFIN/NAMESWE`)
    - `municipality_fi` — municipality name in Finnish
    - `municipality_se` — municipality name in Swedish
    - `incident_type` — type of incident (e.g. "palohälytys", "tieliikenneonnettomuus: pieni")

## Events

### `pelastustoimi_new_alarm`

Fired when a new alarm is detected for any configured municipality. Event data:

```json
{
  "municipality": "Espoo/Esbo",
  "municipality_fi": "Espoo",
  "municipality_se": "Esbo",
  "title": "Espoo/Esbo, palohälytys",
  "description": "20.07.2026 10:39:16 Espoo/Esbo palohälytys",
  "pub_date": "Mon, 20 Jul 2026 10:39:16 +0300",
  "incident_type": "palohälytys"
}
```

## Data Sources

- **RSS feed**: [Peto-media](https://www.peto-media.fi/tiedotteet/rss.xml) — Pelastustoimen mediapalvelu's first-alert feed
- **Municipality list**: extracted from the National Land Survey of Finland's municipality division shapefile (`SuomenKuntajako_2026_10k.shp`, 308 municipalities with Finnish and Swedish names)

## Development

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Lint and type-check
black custom_components/pelastustoimi/
mypy custom_components/pelastustoimi/
pylint custom_components/pelastustoimi/
```

## Disclaimer

This is **not an official product** of the Finnish Emergency Services (Pelastustoimi) or Peto-media.
The author is not affiliated with, endorsed by, or connected to these organizations.
This integration is provided "as is" without warranty of any kind, express or implied.
Always verify critical information from official sources.

## AI Use Disclosure

This project was developed with assistance from AI coding tools. See [AI_DISCLOSURE.md](AI_DISCLOSURE.md) for details.

## License

MIT
