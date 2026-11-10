"""Download the official starter once, keeping it out of the published repo."""
import hashlib
import http.client
import io
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "berkeley_pacman"
SOURCE = "https://inst.eecs.berkeley.edu/~cs188/sp26/assets/projects/search.zip"
SHA256 = "d212f664b97ee38548dd868dfc5ce187f1a2147cfb90b0469e4fffe6e0a160c3"
REQUIRED = ("pacman.py", "game.py", "search.py", "searchAgents.py", "layouts/tinyMaze.lay")
# Offline fallback: search.zip downloaded with a web browser and placed in the project folder.
LOCAL_ZIPS = (ROOT / "search.zip", ROOT / "berkeley_search.zip")
MAX_BYTES = 2_000_000


def install_archive(data, target=ENGINE):
    """Verify before extraction; never overwrite a student's existing work."""
    target = Path(target)
    if target.exists():
        raise ValueError(f"{target} already exists. Setup never overwrites student work.")
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("The Berkeley download changed. Ask your instructor to update the download checksum.")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pacman-setup-", dir=target.parent) as temp:
        stage = Path(temp) / "berkeley"
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for item in archive.infolist():
                path = Path(item.filename)
                if not path.parts or path.parts[0] != "search" or ".." in path.parts or path.is_absolute():
                    raise ValueError("The download contains an unexpected path.")
                relative = Path(*path.parts[1:])
                if relative == Path("."):
                    continue
                destination = stage / relative
                if item.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                else:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(archive.read(item))
        if not all((stage / name).is_file() for name in REQUIRED):
            raise ValueError("The Berkeley starter is incomplete.")
        shutil.move(str(stage), str(target))


def _ssl_contexts():
    """Certificate-verified options only. python.org's Mac Python has no root
    certificates until "Install Certificates.command" runs, so also try other
    trusted certificate bundles that may already be on the computer."""
    yield ssl.create_default_context()
    try:
        import certifi  # Optional; used only if it is already installed.
        yield ssl.create_default_context(cafile=certifi.where())
    except Exception:
        pass
    for bundle in ("/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt"):
        if os.path.isfile(bundle):
            try:
                yield ssl.create_default_context(cafile=bundle)
            except (OSError, ssl.SSLError):
                pass


def _download_with_python(url):
    last = None
    for context in _ssl_contexts():
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "pacman-lab-setup"})
            with urllib.request.urlopen(request, timeout=30, context=context) as response:
                return response.read(MAX_BYTES + 1)
        except urllib.error.HTTPError:
            raise
        except (urllib.error.URLError, ssl.SSLError) as exc:
            last = exc
            if not isinstance(getattr(exc, "reason", exc), ssl.SSLError):
                break  # Not a certificate problem; another bundle will not help.
    raise last


def _download_with_curl(url):
    """curl ships with macOS and Windows 10+ and uses the system's trusted certificates."""
    curl = shutil.which("curl")
    if not curl:
        raise OSError("curl is not available")
    completed = subprocess.run([curl, "--fail", "--silent", "--show-error", "--location",
                                "--max-time", "60", "--max-filesize", str(MAX_BYTES), url],
                               capture_output=True, timeout=90)
    if completed.returncode:
        raise OSError(completed.stderr.decode("utf-8", "replace").strip() or "curl failed")
    return completed.stdout


def download(url=SOURCE, attempts=3):
    """Return the archive bytes, retrying short network hiccups."""
    last = None
    for attempt in range(attempts):
        for method in (_download_with_python, _download_with_curl):
            try:
                data = method(url)
                if len(data) > MAX_BYTES:
                    raise ValueError("The download is unexpectedly large.")
                return data
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    raise ValueError("Berkeley moved the starter file; ask your instructor. " + manual_help()) from exc
                last = exc
            except (OSError, http.client.HTTPException, subprocess.SubprocessError) as exc:
                last = exc
        if attempt + 1 < attempts:
            time.sleep(2 * (attempt + 1))
    reason = getattr(last, "reason", last)
    raise ValueError(f"Could not download Berkeley's starter ({reason}). " + manual_help())


def manual_help():
    return ("Check your internet connection and run install again. Or open " + SOURCE +
            " in your web browser, move the downloaded search.zip (or the unzipped search folder)"
            " into the project folder next to start_pacman.py, and run install again.")


def ensure_engine(quiet=False):
    if all((ENGINE / name).is_file() for name in REQUIRED):
        return ENGINE
    if ENGINE.exists():
        raise ValueError("berkeley_pacman is incomplete. Rename that folder to keep a backup, then run install again.")
    for local in LOCAL_ZIPS:
        if local.is_file():
            if not quiet:
                print(f"Installing from {local.name}…", flush=True)
            install_archive(local.read_bytes(), ENGINE)
            return ENGINE
    unpacked = ROOT / "search"  # Safari unzips downloads automatically.
    if all((unpacked / name).is_file() for name in REQUIRED):
        if not quiet:
            print("Installing from the search folder…", flush=True)
        shutil.copytree(unpacked, ENGINE)
        return ENGINE
    if not quiet:
        print("Downloading Berkeley's official starter (once)…", flush=True)
    install_archive(download(), ENGINE)
    return ENGINE
