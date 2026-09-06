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
├── .dockerignore
├── Dockerfile
├── LICENSE
├── README.md
├── requirements-prod.txt
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

### Run the Production Container

Build the Linux image used by Sakura Cloud AppRun:

```bash
docker build --platform linux/amd64 -t glyph-forge:local .
```

Start the API on port 8080:

```bash
docker run --rm -p 8080:8080 glyph-forge:local
```

Confirm that the container is healthy:

```bash
curl http://localhost:8080/health
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
| `frame_text`               | Yes      | -       | Frame text, up to 64 characters              |
| `inner_text`               | Yes      | -       | Inner text, up to 128 characters             |
| `outer_text`               | Yes      | -       | Outer text, up to 128 characters             |
| `frame_font_size`          | No       | `20`    | Frame font size from 8 through 128           |
| `output_font_size`         | No       | `20`    | Output font size from 10 through 64          |
| `inner_color`              | No       | black   | RGB color for inner text                     |
| `outer_color`              | No       | black   | RGB color for outer text                     |

`frame_text` must contain a visible character. `inner_text` or `outer_text`
may contain only whitespace, but they cannot both contain only whitespace.

Invalid values return `422 Unprocessable Entity`.

Generated images are limited to 2,048 px in width, 2,048 px in height, and
4,194,304 total pixels. Requests that would exceed a limit return
`422 Unprocessable Entity` before the output image is allocated.

Uploaded frame images are limited to 2 MiB, 204 px in width and height, and
41,616 total pixels. PNG, JPEG, and WebP are accepted; animated images are
rejected. The complete multipart request is limited to the 2 MiB file plus
64 KiB of form overhead and accepts one file. Limits and the actual image
format are checked before decoding.

Image generation endpoints are intended for internal use and do not apply an
IP-based rate limit. Each application process runs one image generation at a
time, queues up to 4 requests for 10 seconds, and returns `503` with
`Retry-After` when capacity is unavailable. `/health` is exempt. Image
generation runs in a child process that is stopped after 30 seconds.

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
| `docker build --platform linux/amd64 -t glyph-forge:local .` | Build the production image |

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
