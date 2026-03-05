"""
TDLib auto-installer for zsys.telegram.
Downloads pre-built TDLib binaries or builds from source.
"""
import os
import sys
import platform
import subprocess
import tarfile
import zipfile
import urllib.request
import shutil
from pathlib import Path

TDLIB_VERSION = "1.8.0"
TDLIB_DIR = Path.home() / ".zsys" / "tdlib"
LIBTG_DIR = Path(__file__).parent / "lib"

# Pre-built binary URLs (GitHub releases)
PREBUILT_URLS = {
    ("Linux", "x86_64"): f"https://github.com/nickoala/td-prebuilt/releases/download/v{TDLIB_VERSION}/libtdjson-linux-amd64.tar.gz",
    ("Linux", "aarch64"): f"https://github.com/nickoala/td-prebuilt/releases/download/v{TDLIB_VERSION}/libtdjson-linux-arm64.tar.gz",
    ("Darwin", "x86_64"): f"https://github.com/nickoala/td-prebuilt/releases/download/v{TDLIB_VERSION}/libtdjson-macos-amd64.tar.gz",
    ("Darwin", "arm64"): f"https://github.com/nickoala/td-prebuilt/releases/download/v{TDLIB_VERSION}/libtdjson-macos-arm64.tar.gz",
    ("Windows", "AMD64"): f"https://github.com/nickoala/td-prebuilt/releases/download/v{TDLIB_VERSION}/libtdjson-win-amd64.zip",
}

def get_platform_key():
    """Get platform key for pre-built binaries."""
    system = platform.system()
    machine = platform.machine()
    return (system, machine)

def get_lib_extension():
    """Get library extension for current platform."""
    system = platform.system()
    if system == "Windows":
        return ".dll"
    elif system == "Darwin":
        return ".dylib"
    return ".so"

def find_tdjson():
    """Find libtdjson in common locations."""
    ext = get_lib_extension()
    lib_name = f"libtdjson{ext}"
    search_paths = [
        TDLIB_DIR / "lib" / lib_name,
        TDLIB_DIR / lib_name,
        LIBTG_DIR / lib_name,
        Path("/usr/local/lib") / lib_name,
        Path("/usr/lib") / lib_name,
        Path("/usr/lib64") / lib_name,
    ]
    if "TDLIB_PATH" in os.environ:
        search_paths.insert(0, Path(os.environ["TDLIB_PATH"]) / lib_name)
    for path in search_paths:
        if path.exists():
            return path
    return None

def find_libtg():
    """Find libtg in common locations."""
    ext = get_lib_extension()
    lib_name = f"libtg{ext}"
    search_paths = [
        LIBTG_DIR / lib_name,
        Path(__file__).parent / "c" / "build" / lib_name,
        TDLIB_DIR / "lib" / lib_name,
    ]
    for path in search_paths:
        if path.exists():
            return path
    return None

def download_file(url: str, dest: Path) -> bool:
    """Download file with progress."""
    try:
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, dest)
        return True
    except Exception as e:
        print(f"Download failed: {e}")
        return False

def extract_archive(archive: Path, dest: Path):
    """Extract tar.gz or zip archive."""
    dest.mkdir(parents=True, exist_ok=True)
    if archive.suffix == ".gz" or str(archive).endswith(".tar.gz"):
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(dest)
    elif archive.suffix == ".zip":
        with zipfile.ZipFile(archive, "r") as zip_ref:
            zip_ref.extractall(dest)

def download_prebuilt() -> bool:
    """Download pre-built TDLib binaries."""
    key = get_platform_key()
    if key not in PREBUILT_URLS:
        print(f"No pre-built binaries for {key}")
        return False
    url = PREBUILT_URLS[key]
    TDLIB_DIR.mkdir(parents=True, exist_ok=True)
    archive_name = url.split("/")[-1]
    archive_path = TDLIB_DIR / archive_name
    if not download_file(url, archive_path):
        return False
    print("Extracting...")
    extract_archive(archive_path, TDLIB_DIR / "lib")
    archive_path.unlink()
    # Verify
    if find_tdjson():
        print(f"✓ TDLib installed to {TDLIB_DIR}")
        return True
    return False

def build_from_source() -> bool:
    """Build TDLib from source using install script."""
    script = Path(__file__).parent / "scripts" / "install_tdlib.sh"
    if not script.exists():
        print(f"Install script not found: {script}")
        return False
    print("Building TDLib from source (this may take 10-15 minutes)...")
    env = os.environ.copy()
    env["TDLIB_DIR"] = str(TDLIB_DIR)
    try:
        subprocess.run(["bash", str(script)], env=env, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def build_libtg() -> bool:
    """Build libtg C wrapper."""
    c_dir = Path(__file__).parent / "c"
    if not c_dir.exists():
        print(f"C source directory not found: {c_dir}")
        return False
    build_dir = c_dir / "build"
    build_dir.mkdir(exist_ok=True)
    tdjson = find_tdjson()
    if not tdjson:
        print("TDLib not found, cannot build libtg")
        return False
    print("Building libtg...")
    env = os.environ.copy()
    env["TDLIB_PATH"] = str(tdjson.parent)
    try:
        subprocess.run(
            ["cmake", "..", f"-DTDLIB_PATH={tdjson.parent}"],
            cwd=build_dir, env=env, check=True
        )
        subprocess.run(["make", "-j4"], cwd=build_dir, check=True)
        # Copy to lib/
        LIBTG_DIR.mkdir(exist_ok=True)
        ext = get_lib_extension()
        built_lib = build_dir / f"libtg{ext}"
        if built_lib.exists():
            shutil.copy(built_lib, LIBTG_DIR / f"libtg{ext}")
            print(f"✓ libtg installed to {LIBTG_DIR}")
            return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
    return False

def ensure_tdlib() -> Path | None:
    """Ensure TDLib is installed, download if needed."""
    tdjson = find_tdjson()
    if tdjson:
        return tdjson
    print("TDLib not found. Installing...")
    # Try pre-built first
    if download_prebuilt():
        return find_tdjson()
    # Fall back to source build
    print("Pre-built not available, building from source...")
    if build_from_source():
        return find_tdjson()
    return None

def ensure_libtg() -> Path | None:
    """Ensure libtg is built."""
    libtg = find_libtg()
    if libtg:
        return libtg
    # Need TDLib first
    if not ensure_tdlib():
        return None
    # Build libtg
    if build_libtg():
        return find_libtg()
    return None

def setup():
    """Full setup: ensure TDLib + libtg are available."""
    print("=== zsys.telegram setup ===")
    tdjson = ensure_tdlib()
    if not tdjson:
        print("✗ Failed to install TDLib")
        print("Try manual install: zsys/telegram/scripts/install_tdlib.sh")
        return False
    libtg = ensure_libtg()
    if not libtg:
        print("✗ Failed to build libtg")
        print("Try manual build: cd zsys/telegram/c && mkdir build && cd build && cmake .. && make")
        return False
    print("\n✓ Setup complete!")
    print(f"  TDLib: {tdjson}")
    print(f"  libtg: {libtg}")
    return True

if __name__ == "__main__":
    success = setup()
    sys.exit(0 if success else 1)
