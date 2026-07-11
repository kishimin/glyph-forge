<div id="top"></div>

# glyph-forge

Generate glyph art images by filling a text-shaped frame with repeated text.

## Tech Stack

<p style="display: inline">
  <img src="https://img.shields.io/badge/-Python-3776AB.svg?logo=python&style=for-the-badge&logoColor=white">
  <img src="https://img.shields.io/badge/-FastAPI-009688.svg?logo=fastapi&style=for-the-badge&logoColor=white">
  <img src="https://img.shields.io/badge/-Pillow-000000.svg?style=for-the-badge">
  <img src="https://img.shields.io/badge/-pytest-0A9EDC.svg?logo=pytest&style=for-the-badge&logoColor=white">
</p>

## Table of Contents

1. [About the Project](#about-the-project)
2. [Environment](#environment)
3. [Directory Structure](#directory-structure)
4. [Getting Started](#getting-started)
5. [Usage](#usage)
6. [API Endpoints](#api-endpoints)
7. [Available Commands](#available-commands)
8. [Troubleshooting](#troubleshooting)

## About the Project

glyph-forge creates images where:

- `frame_text` defines the visible frame shape.
- `inner_text` fills the inside of that frame.
- `outer_text` fills the area outside the frame.

It can render a general glyph-art image, an X profile icon image, and an X
profile background image. The renderer keeps inner and outer text colors
separate, wraps frame text by a configurable character count, and uses packaged
Japanese font data for stable rendering.

<p align="right">(<a href="#top">back to top</a>)</p>

## Environment

| Language / Framework | Version |
| -------------------- | ------- |
| Python               | 3.12    |
| FastAPI              | 0.138.1 |
| Pillow               | 10.3.0  |
| pytest               | 7.4.4   |

See `requirements.txt` and `setup.py` for the full dependency and package
metadata.

<p align="right">(<a href="#top">back to top</a>)</p>

## Directory Structure

```text
.
├── .github
│   └── workflows
├── app
│   ├── main.py
│   └── schemas.py
├── src
│   └── glyph_forge
│       ├── fonts
│       └── services
├── tests
│   └── test_glyph_forge
├── LICENSE
├── README.md
├── requirements.txt
├── setup.py
└── pytest.ini
```

### Main Directories

| Directory                 | Description                                      |
| ------------------------- | ------------------------------------------------ |
| `app`                     | FastAPI application and request schemas          |
| `src/glyph_forge/fonts`   | Packaged font files used for image rendering     |
| `src/glyph_forge/services`| Glyph rendering, text grid, and threshold logic  |
| `tests/test_glyph_forge`  | Unit and API regression tests                    |
| `.github/workflows`       | Lint, test, and release workflow configuration   |

<p align="right">(<a href="#top">back to top</a>)</p>

## Getting Started

### Prerequisites

Install Python 3.12.

### Clone the Repository

```bash
git clone https://github.com/kishimin/glyph-forge.git
cd <repository-directory>
```

### Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .
```

### Run Tests

```bash
python -m pytest -q
```

### Start the API Server

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000/docs
```

<p align="right">(<a href="#top">back to top</a>)</p>

## Usage

### Python

```python
from glyph_forge.services.glyph_art_renderer import render_glyph_art_image
from glyph_forge.services.settings import GlyphForgeConfig

img = render_glyph_art_image(
    frame_text="FRAME",
    inner_text="INNER",
    outer_text="OUTER",
    config=GlyphForgeConfig(
        inner_color=(64, 128, 255),
        outer_color=(255, 128, 64),
    ),
)

img.save("output/sample.png")
```

### API Request

Use Python's standard library to avoid shell-specific quoting differences.

```python
import json
import urllib.request
from pathlib import Path

payload = {
    "frame_text": "FRAME",
    "inner_text": "INNER",
    "outer_text": "OUTER",
    "inner_color": [64, 128, 255],
    "outer_color": [255, 128, 64],
    "max_chars_per_line": 5,
}

request = urllib.request.Request(
    "http://localhost:8000/images",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json; charset=utf-8"},
    method="POST",
)

Path("output").mkdir(exist_ok=True)
with urllib.request.urlopen(request) as response:
    Path("output/sample.png").write_bytes(response.read())
```

<p align="right">(<a href="#top">back to top</a>)</p>

## API Endpoints

| Method | Path                 | Description                         |
| ------ | -------------------- | ----------------------------------- |
| `GET`  | `/health`            | Health check for monitoring         |
| `POST` | `/images`            | Generate a general glyph-art image  |
| `POST` | `/images/x-icon`     | Generate an X profile icon image    |
| `POST` | `/images/background` | Generate an X profile background    |

### Request Body

| Field                      | Required | Default | Description                                  |
| -------------------------- | -------- | ------- | -------------------------------------------- |
| `frame_text`               | Yes      | -       | Text used to create the frame shape          |
| `inner_text`               | Yes      | -       | Text rendered inside the frame               |
| `outer_text`               | Yes      | -       | Text rendered outside the frame              |
| `max_chars_per_line`       | No       | `5`     | Frame text wrapping size                     |
| `frame_font_size`          | No       | `20`    | Font size used to create the frame mask      |
| `output_font_size`         | No       | `20`    | Font size used for inner and outer text      |
| `frame_cell_padding_ratio` | No       | `0.0`   | Extra frame cell padding ratio               |
| `inner_color`              | No       | black   | RGB color for inner text                     |
| `outer_color`              | No       | black   | RGB color for outer text                     |

Invalid values return `422 Unprocessable Entity`.

<p align="right">(<a href="#top">back to top</a>)</p>

## Available Commands

| Command                          | Description                         |
| -------------------------------- | ----------------------------------- |
| `pip install -r requirements.txt`| Install dependencies                |
| `pip install -e .`               | Install the package in editable mode|
| `python -m pytest -q`            | Run tests                           |
| `autoflake --check --recursive .`| Check unused imports and variables  |
| `isort --check-only .`           | Check import ordering               |
| `black --check .`                | Check formatting                    |
| `flake8 .`                       | Run style checks                    |
| `mypy src`                       | Run type checks                     |
| `uvicorn app.main:app --reload`  | Start the local API server          |

<p align="right">(<a href="#top">back to top</a>)</p>

## Troubleshooting

### `ModuleNotFoundError: glyph_forge`

Install the package in editable mode.

```bash
pip install -e .
```

### `fastapi.testclient` requires `httpx2`

Install dependencies from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### Japanese text is not rendered as expected

Make sure the package is installed with package data included. The renderer uses
the bundled font under `src/glyph_forge/fonts`.

```bash
pip install -e .
```

### The release workflow cannot create a GitHub Release

The release job needs `contents: write` permission when using
`ncipollo/release-action` with `GITHUB_TOKEN`.

<p align="right">(<a href="#top">back to top</a>)</p>
