# monday-summary-app

A small reusable Python application that retrieves a concise summary of a single monday.com board, prints it to the terminal, and can optionally generate a static HTML file and open it in the default browser.

---

## Files

| File | Purpose |
|---|---|
| [`monday_summary_app/cli.py`](monday_summary_app/cli.py) | Main reusable CLI module and application logic. |
| [`summary.py`](summary.py) | Backward-compatible script entry point. |
| [`pyproject.toml`](pyproject.toml) | Packaging metadata and CLI entry point definition. |
| [`requirements.txt`](requirements.txt) | Minimal runtime dependency list. |
| [`README.md`](README.md) | Setup and usage guide. |
| [`sample-output.html`](sample-output.html) | Static sample of the HTML output format for reference. |
| `dist/monday-summary.exe` | Standalone Windows executable (no Python required). |

---

## Configuration

The app accepts its required settings either as **CLI flags** or **environment variables**. Flags take priority when both are provided.

| CLI flag | Environment variable | Description |
|---|---|---|
| `--token TOKEN` | `MONDAY_API_TOKEN` | Your monday.com personal API token. |
| `--board-id ID` | `MONDAY_BOARD_ID` | The numeric ID of the board to summarise. |

### Passing credentials as flags (quickest for one-off use)

```bash
monday-summary --token your_token_here --board-id 1234567890
```

### Setting environment variables (recommended for repeated use)

#### Linux or macOS

```bash
export MONDAY_API_TOKEN=your_token_here
export MONDAY_BOARD_ID=1234567890
```

#### Windows PowerShell

```powershell
$env:MONDAY_API_TOKEN = "your_token_here"
$env:MONDAY_BOARD_ID = "1234567890"
```

If either value is missing from both sources, the app exits immediately with a clear error message.

---

## Standalone executable (no Python required)

If you just want to run the tool on Windows without installing Python, use the pre-built executable in `dist/`.

```powershell
# Run from the dist\ folder
.\dist\monday-summary.exe --token your_token_here --board-id 1234567890

# Generate an HTML report
.\dist\monday-summary.exe --token your_token_here --board-id 1234567890 --html --open
```

That's it — no installation, no Python, no dependencies.

### Rebuilding the executable

If you modify the source and want to rebuild `dist/monday-summary.exe`, you need Python 3.13 and PyInstaller:

```powershell
py -3.13 -m pip install pyinstaller requests
py -3.13 -m PyInstaller --onefile --name monday-summary --distpath dist summary.py
```

---

## Install

From inside [`monday-summary-app/`](.) install the dependencies.

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If you want the packaged CLI command, install the project in editable mode:

### Linux or macOS

```bash
python -m pip install -e .
```

### Windows PowerShell

```powershell
python -m pip install -e .
```

---

## Run the application

You can run the app as a script, as a Python module, or as an installed CLI command.

### Linux or macOS

```bash
# Pass credentials as flags
python summary.py --token your_token_here --board-id 1234567890

# Use environment variables (set once, omit flags)
python summary.py

# Python module entry point
python -m monday_summary_app --token your_token_here --board-id 1234567890

# Installed CLI entry point
monday-summary --token your_token_here --board-id 1234567890

# Generate HTML in monday-summary-app/summary.html
python summary.py --html

# Generate HTML and open it in the default browser
python summary.py --html --open

# Limit recent updates
python summary.py --updates 5
```

### Windows PowerShell

```powershell
# Pass credentials as flags
python .\summary.py --token your_token_here --board-id 1234567890

# Use environment variables (set once, omit flags)
python .\summary.py

# Python module entry point
python -m monday_summary_app --token your_token_here --board-id 1234567890

# Installed CLI entry point
monday-summary --token your_token_here --board-id 1234567890

# Generate HTML in monday-summary-app\summary.html
python .\summary.py --html

# Generate HTML and open it in the default browser
python .\summary.py --html --open

# Limit recent updates
python .\summary.py --updates 5
```

The generated [`summary.html`](summary.html) file is always written to the [`monday-summary-app/`](.) directory regardless of where you launch the command from.

---

## Sample output

[`sample-output.html`](sample-output.html) is a pre-generated static HTML file committed to this folder. It shows the same HTML structure and layout that [`--html`](summary.py) produces. You can open it in any browser without API credentials to preview the output format.

---

## Validation

Check for syntax errors without calling the API:

### Linux or macOS

```bash
python -m py_compile summary.py monday_summary_app/cli.py
```

### Windows PowerShell

```powershell
python -m py_compile .\summary.py .\monday_summary_app\cli.py
```

Validate the module and installed CLI entry points:

### Linux or macOS

```bash
python -m monday_summary_app --help
monday-summary --help
```

### Windows PowerShell

```powershell
python -m monday_summary_app --help
monday-summary --help
```
