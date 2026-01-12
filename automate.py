#!/usr/bin/env python3
"""
Automated DAT download and Retool processing script.

This script:
1. Downloads Redump .dat files from redump.org to daily-virgin-dat/redump/ directory
2. Downloads No-Intro .dat files from datomatic.no-intro.org to daily-virgin-dat/no-intro/ directory
3. Downloads/sets up the latest Retool
4. Processes all .dat files from daily-virgin-dat/redump/ and daily-virgin-dat/no-intro/ directories through Retool
   for each configuration (Hearto, McLean, PropeR) with their respective filter settings
5. Exports processed DATs to daily-processed-dat/{config}/{collection}/ directories
6. Exports reports to report/{config}/{collection}/ directories
"""

import re
import requests
import zipfile
import subprocess
import shutil
import sys
import os
import json
from pathlib import Path
from io import BytesIO
from time import sleep

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = SCRIPT_DIR / "config"
REDUMP_DIR = SCRIPT_DIR / "daily-virgin-dat" / "redump"
NO_INTRO_DIR = SCRIPT_DIR / "daily-virgin-dat" / "no-intro"
RETOOL_DIR = SCRIPT_DIR / "retool"
RETOOL_REPO_URL = "https://github.com/unexpectedpanda/retool.git"
RETOOL_RELEASES_API = "https://api.github.com/repos/unexpectedpanda/retool/releases/latest"
RETOOL_CONFIG_DIR = RETOOL_DIR / "config"

# Collection URLs
REDUMP_URL = "http://redump.org"
NO_INTRO_URL = "https://datomatic.no-intro.org"


# Skip downloading/updating Redump DAT files (use existing files in daily-virgin-dat/redump/ directory)
SKIP_REDUMP_DOWNLOAD = False

# Skip downloading/updating No-Intro DAT files (use existing files in daily-virgin-dat/no-intro/ directory)
SKIP_NO_INTRO_DOWNLOAD = False

# DAT collections to process (redump, no-intro, etc.)
DAT_COLLECTIONS = ["redump", "no-intro"]

# Always reprocess DAT files through Retool, even if processed version already exists
ALWAYS_REPROCESS = False

# Retool dependencies
RETOOL_DEPENDENCIES = [
    "alive-progress",
    "darkdetect",
    "lxml",
    "psutil",
    "pyside6",
    "strictyaml",
    "validators"
]

# Regex patterns for parsing redump downloads page
regex = {
    "datfile": r'<a href="/datfile/(.*?)">',
    "date": r"\) \((.*?)\)\.",
    "name": r'filename="(.*?) Datfile',
    "filename": r'filename="(.*?)"',
}



# ============================================================================
# Utility Functions
# ============================================================================

def print_step(description: str, emoji: str = "⚙️"):
    """Print a step indicator."""
    print(f"\n{emoji} {description}")
    print("  " + "─" * 66)


def check_git_available() -> bool:
    """Check if git is available on the system."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


# ============================================================================
# Retool Setup Functions
# ============================================================================

def clone_retool_if_needed(retool_dir: Path) -> bool:
    """Clone Retool repository if it doesn't exist or is not a git repository."""
    retool_script = retool_dir / "retool.py"
    
    # If retool.py exists, assume Retool is already set up
    if retool_script.exists():
        print(f"  ✅ Retool already exists")
        print(f"     Location: {retool_dir}")
        return True
    
    # Check if git is available
    if not check_git_available():
        print(f"  ❌ Git is not available. Cannot clone Retool.", file=sys.stderr)
        return False
    
    # Check if it's a git repository (might be a partial clone)
    is_git_repo = (retool_dir / ".git").exists()
    
    try:
        # Remove directory if it exists but isn't a valid Retool installation
        if retool_dir.exists() and not is_git_repo:
            print(f"  🗑️  Removing invalid Retool directory...")
            shutil.rmtree(retool_dir)
        
        # Clone Retool if directory doesn't exist or was removed
        if not retool_dir.exists():
            print(f"  📥 Cloning Retool from GitHub...")
            print(f"     Repository: {RETOOL_REPO_URL}")
            result = subprocess.run(
                ["git", "clone", RETOOL_REPO_URL, str(retool_dir)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                print(f"  ❌ Failed to clone Retool: {result.stderr}", file=sys.stderr)
                return False
            
            print(f"  ✅ Retool cloned successfully")
            print(f"     Location: {retool_dir}")
        else:
            print(f"  ✅ Retool directory already exists")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error setting up Retool: {e}", file=sys.stderr)
        return False


def update_retool_main(retool_dir: Path) -> bool:
    """Update retool directory using git pull."""
    if not (retool_dir / ".git").exists():
        print(f"  ⚠️  Not a git repository, skipping update")
        return True
    
    # Check if git is available
    if not check_git_available():
        print(f"  ⚠️  Git is not available, skipping Retool update")
        return True
    
    print(f"  🔄 Checking for Retool updates...")
    try:
        result = subprocess.run(
            ["git", "pull"],
            cwd=retool_dir,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            if "Already up to date" in result.stdout:
                print(f"  ✅ Retool is already up to date")
            else:
                print(f"  ✅ Retool updated successfully")
            return True
        else:
            print(f"  ⚠️  Git pull warning: {result.stderr}", file=sys.stderr)
            return True
    except Exception as e:
        print(f"  ⚠️  Error updating retool: {e}", file=sys.stderr)
        return True


def copy_user_config(config_name: str, user_config_source: Path) -> bool:
    """Copy user-config.yaml to Retool config directory for a specific configuration."""
    if not user_config_source.exists():
        print(f"  ⚠️  User config not found for {config_name}")
        print(f"     Expected: {user_config_source}")
        print(f"     🚫 Retool will use default configuration")
        return True
    
    try:
        # Ensure config directory exists
        RETOOL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        retool_config_dest = RETOOL_CONFIG_DIR / "user-config.yaml"
        shutil.copy2(user_config_source, retool_config_dest)
        
        print(f"  ✅ User config copied for {config_name}")
        print(f"     From: {user_config_source}")
        print(f"     To:   {retool_config_dest}")
        return True
        
    except Exception as e:
        print(f"  ⚠️  Warning: Could not copy user config for {config_name}: {e}", file=sys.stderr)
        return True  # Continue anyway - Retool will use defaults


def load_filters_config(config_dir: Path) -> tuple[list[str], str]:
    """Load filters.py for a configuration and return (flags, exclude_string)."""
    filters_file = config_dir / "filters.py"
    
    if not filters_file.exists():
        raise FileNotFoundError(f"filters.py not found in {config_dir}")
    
    try:
        # Import the filters module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location("filters", filters_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load filters.py from {config_dir}")
        
        filters_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(filters_module)
        
        # Get exclude and flags from the module (required)
        exclude = getattr(filters_module, "exclude", None)
        flags = getattr(filters_module, "flags", None)
        
        if exclude is None:
            raise ValueError(f"filters.py in {config_dir} must define 'exclude'")
        if flags is None:
            raise ValueError(f"filters.py in {config_dir} must define 'flags'")
        
        # Ensure exclude is a string
        if isinstance(exclude, list):
            exclude = "".join(exclude)
        
        # Ensure flags is a list
        if not isinstance(flags, list):
            raise ValueError(f"filters.py in {config_dir} must define 'flags' as a list")
        
        return flags, exclude
        
    except Exception as e:
        print(f"  ❌ Error loading filters.py from {config_dir}: {e}", file=sys.stderr)
        raise


def discover_configs() -> list[tuple[str, Path]]:
    """Discover all configuration directories in config/."""
    configs = []
    
    if not CONFIG_DIR.exists():
        print(f"  ⚠️  Config directory not found: {CONFIG_DIR}")
        return configs
    
    for config_path in CONFIG_DIR.iterdir():
        if config_path.is_dir():
            config_name = config_path.name
            user_config = config_path / "user-config.yaml"
            filters_config = config_path / "filters.py"
            
            # Check if both required files exist
            if user_config.exists() and filters_config.exists():
                configs.append((config_name, config_path))
            else:
                print(f"  ⚠️  Skipping {config_name}: missing user-config.yaml or filters.py")
    
    return sorted(configs)


def preload_config_settings(configs: list[tuple[str, Path]], collections: list[str]) -> dict[str, dict]:
    """
    Preload all configuration settings (filters, paths) for all configs and collections.
    Returns a dict mapping (config_name, collection) -> {flags, exclude, config_dir, user_config_path, daily_dir, report_dir}
    """
    config_settings = {}
    
    print_step("Preloading configuration settings", "⚙️")
    
    for config_name, config_dir in configs:
        # Load filter settings (same for all collections)
        retool_flags, retool_exclude = load_filters_config(config_dir)
        
        # Set up paths for each collection
        user_config_path = config_dir / "user-config.yaml"
        
        for collection in collections:
            key = (config_name, collection)
            daily_output_dir = SCRIPT_DIR / "daily-processed-dat" / config_name / collection
            report_output_dir = SCRIPT_DIR / "report" / config_name / collection
            
            config_settings[key] = {
                "flags": retool_flags,
                "exclude": retool_exclude,
                "config_dir": config_dir,
                "user_config_path": user_config_path,
                "daily_dir": daily_output_dir,
                "report_dir": report_output_dir,
                "collection": collection
            }
        
        print(f"  ✅ {config_name}:")
        print(f"     Exclude flags: {retool_exclude}")
        print(f"     Command flags: {' '.join(retool_flags)}")
        for collection in collections:
            print(f"     Output: daily-processed-dat/{config_name}/{collection}/")
            print(f"     Reports: report/{config_name}/{collection}/")
    
    return config_settings


def install_retool_dependencies() -> bool:
    """Install Retool dependencies."""
    print(f"  📦 Installing {len(RETOOL_DEPENDENCIES)} package(s)...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + RETOOL_DEPENDENCIES,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"  ✅ Dependencies installed successfully")
            return True
        else:
            print(f"  ⚠️  Warning installing dependencies: {result.stderr}", file=sys.stderr)
            return True  # Continue anyway
    except Exception as e:
        print(f"  ⚠️  Error installing dependencies: {e}", file=sys.stderr)
        return True  # Continue anyway


def update_retool_clone_lists(retool_dir: Path) -> bool:
    """Run retool.py --update to get latest clone lists."""
    retool_script = retool_dir / "retool.py"
    
    if not retool_script.exists():
        print(f"  ⚠️  Retool script not found: {retool_script}")
        return True
    try:
        result = subprocess.run(
            [sys.executable, str(retool_script), "--update"],
            cwd=retool_dir,
            input="y\ny\ny\n",
            text=True,
            check=False,
            capture_output=True
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"  ⚠️  Warning: retool.py --update exited with code {result.returncode}", file=sys.stderr)
            return True  # Continue anyway
    except Exception as e:
        print(f"  ⚠️  Error updating clone lists: {e}", file=sys.stderr)
        return True  # Continue anyway


# ============================================================================
# Redump DAT Download Functions
# ============================================================================

def find_all_redump_dats():
    """Find all available Redump DAT files from the downloads page."""
    print(f"  🌐 Connecting to Redump.org...")
    downloads_url = f"{REDUMP_URL}/downloads/"
    print(f"     URL: {downloads_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        download_page = requests.get(downloads_url, headers=headers, timeout=150)
        download_page.raise_for_status()
        
        dat_files = re.findall(regex["datfile"], download_page.text)
        print(f"  ✅ Found {len(dat_files)} DAT files")
        return dat_files
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error fetching downloads page: {e}", file=sys.stderr)
        return []


def get_redump_dat_info(dat_name: str) -> tuple[str | None, str | None]:
    """Get DAT file info (filename and date) from Redump without downloading."""
    dat_url = f"{REDUMP_URL}/datfile/{dat_name}"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Use HEAD request to get metadata without downloading
        response = requests.head(dat_url, headers=headers, timeout=150, allow_redirects=True)
        response.raise_for_status()
        
        content_header = response.headers.get("Content-Disposition", "")
        
        # Extract filename from Content-Disposition header
        original_filename = None
        if 'filename=' in content_header:
            filename_match = re.findall(regex["filename"], content_header)
            if filename_match:
                original_filename = filename_match[0]
        
        # Extract date from Content-Disposition header
        dat_date = None
        if 'filename=' in content_header:
            date_match = re.findall(regex["date"], content_header)
            if date_match:
                dat_date = date_match[0]
        
        # If no filename in header, use dat_name
        if not original_filename:
            original_filename = dat_name
        
        return original_filename, dat_date
        
    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  Could not get info for {dat_name}: {e}", file=sys.stderr)
        return None, None


def download_redump_dat(dat_name: str, output_dir: Path, skip_if_exists: bool = True) -> tuple[Path | None, bool]:
    """Download a single Redump DAT file, optionally skipping if file already exists."""
    dat_url = f"{REDUMP_URL}/datfile/{dat_name}"
    
    try:
        # First, get file info to determine the actual filename
        original_filename, remote_date = get_redump_dat_info(dat_name)
        
        if not original_filename:
            original_filename = dat_name
        
        # Determine expected output filename
        if original_filename.endswith(".zip"):
            # For zip files, we need to download to see what's inside
            # We can't check ahead of time what the extracted .dat filename will be
            # So we'll download and check after extraction
            pass
        else:
            # Direct .dat file - check if exact filename already exists
            datfile_name = original_filename
            if not datfile_name.endswith('.dat'):
                datfile_name = f"{datfile_name}.dat"
            
            output_path = output_dir / datfile_name
            
            # Simple check: if file with exact name exists, skip it
            if skip_if_exists and output_path.exists():
                print(f"    ❎  Skipping {dat_name} (file already exists: {datfile_name})")
                return output_path, True  # Return True to indicate it was skipped
        
        # File doesn't exist or is outdated, download it
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(dat_url, headers=headers, timeout=150)
        response.raise_for_status()
        
        content_header = response.headers.get("Content-Disposition", "")
        
        # Re-extract filename in case HEAD and GET differ
        if 'filename=' in content_header:
            filename_match = re.findall(regex["filename"], content_header)
            if filename_match:
                original_filename = filename_match[0]
        
        if not original_filename:
            original_filename = dat_name
        
        # Determine if it's a zip or dat file
        if original_filename.endswith(".zip"):
            # Extract datfile from zip
            zipdata = BytesIO()
            zipdata.write(response.content)
            archive = zipfile.ZipFile(zipdata)
            
            # Find .dat file in zip
            dat_files = [f for f in archive.namelist() if f.endswith('.dat')]
            if not dat_files:
                print(f"    ⚠️  No .dat file found in zip archive")
                return None, False
            
            datfile_name = dat_files[0]
            
            # Check if extracted .dat file already exists
            output_path = output_dir / datfile_name
            if skip_if_exists and output_path.exists():
                print(f"    ❎  Skipping {dat_name} (file already exists: {datfile_name})")
                return output_path, True  # Return True to indicate it was skipped
            
            dat_content = archive.read(datfile_name)
            
            # Save extracted .dat file
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(dat_content)
            
            return output_path, False  # Return False to indicate it was downloaded
        else:
            # Direct .dat file
            datfile_name = original_filename
            if not datfile_name.endswith('.dat'):
                datfile_name = f"{datfile_name}.dat"
            
            output_path = output_dir / datfile_name
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return output_path, False  # Return False to indicate it was downloaded
        
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Error downloading {dat_name}: {e}", file=sys.stderr)
        return None, False
    except Exception as e:
        print(f"    ❌ Unexpected error downloading {dat_name}: {e}", file=sys.stderr)
        return None, False


def cleanup_old_redump_dat(new_dat_path: Path, output_dir: Path) -> int:
    """
    Remove old Redump DAT files for the same system when a new one is downloaded.
    Matches by system name only (ignoring dates).
    Returns the number of old files removed.
    """
    if not new_dat_path.exists():
        return 0
    
    # Extract system name from the new file
    new_system_name = extract_system_name(new_dat_path.stem, "redump")
    
    # Find all DAT files in the directory
    all_dats = list(output_dir.glob("*.dat"))
    removed_count = 0
    
    for old_dat in all_dats:
        # Skip the newly downloaded file itself
        if old_dat == new_dat_path:
            continue
        
        # Extract system name from the old file
        old_system_name = extract_system_name(old_dat.stem, "redump")
        
        # If system names match, remove the old version
        if old_system_name == new_system_name:
            try:
                old_dat.unlink()
                removed_count += 1
            except Exception as e:
                pass  # Ignore errors
    
    return removed_count


def download_all_redump_dats(output_dir: Path) -> list[Path]:
    """Download all Redump DAT files, skipping those that already exist."""
    print_step("Finding all Redump DAT files", "🔍")
    dat_list = find_all_redump_dats()
    
    if not dat_list:
        print("  ❌ No DAT files found!")
        return []
    
    print_step(f"Downloading {len(dat_list)} Redump DAT files (skipping existing ones)", "⬇️")
    
    downloaded_dats = []
    skipped_count = 0
    cleaned_count = 0
    for i, dat in enumerate(dat_list, 1):
        print(f"  [{i}/{len(dat_list)}] Checking {dat}...")
        dat_path, was_skipped = download_redump_dat(dat, output_dir, skip_if_exists=True)
        if dat_path:
            downloaded_dats.append(dat_path)
            if was_skipped:
                skipped_count += 1
            else:
                print(f"    ✅ Saved: {dat_path.name}")
                # Clean up old versions of the same system
                removed = cleanup_old_redump_dat(dat_path, output_dir)
                if removed > 0:
                    cleaned_count += removed
        else:
            print(f"    ❌ Failed to download {dat}")
        
        # Small delay to be respectful to the server (only if we actually downloaded)
        if not was_skipped and i < len(dat_list):
            sleep(2)
    
    print(f"\n  ✅ Successfully processed {len(downloaded_dats)}/{len(dat_list)} Redump DAT files")
    if skipped_count > 0:
        print(f"  ❎  Skipped {skipped_count} existing files (saved time and bandwidth)")
    if cleaned_count > 0:
        print(f"  🗑️  Removed {cleaned_count} old version(s) of updated systems")
    return downloaded_dats


# ============================================================================
# No-Intro DAT Download Functions
# ============================================================================

def download_no_intro_dats(output_dir: Path) -> list[Path]:
    """Download all No-Intro DAT files from datomatic.no-intro.org using Playwright."""
    if not PLAYWRIGHT_AVAILABLE:
        print("  ❌ Playwright is not available. Install it with: pip install playwright")
        print("     Then run: playwright install chromium")
        return []
    
    print_step("Downloading No-Intro DAT files", "⬇️")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir.parent / "temp_no_intro"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            context.set_default_timeout(30000)  # 30 second timeout
            page = context.new_page()
            
            # Navigate and navigate to Daily
            page.goto(NO_INTRO_URL, wait_until="networkidle", timeout=30000)
            page.locator("text=DOWNLOAD").first.click()
            sleep(0.5)
            page.locator("text=Daily").first.click()
            page.wait_for_load_state("networkidle", timeout=30000)
            sleep(1)
            
            # Uncheck options
            print("  ⚙️  Unchecking: Source Code, Unofficial, Non-Redump")
            options_to_uncheck = ["Source Code", "Unofficial", "Non-Redump"]
            for option in options_to_uncheck:
                all_labels = page.locator("label")
                for i in range(all_labels.count()):
                    label = all_labels.nth(i)
                    label_text = label.inner_text().strip()
                    if option == label_text or (label_text.startswith(option) and len(label_text.split()) <= 2):
                        label_for = label.get_attribute("for")
                        checkbox = page.locator(f"input#{label_for}[type='checkbox']").first if label_for else label.locator("input[type='checkbox']").first
                        if checkbox.count() > 0 and checkbox.is_checked():
                            checkbox.uncheck()
                            print(f"     ✗ Unchecked: {option}")
                        break
            
            # Request and download
            page.locator("button:has-text('Request'), input[value='Request']").first.click()
            sleep(1)
            
            download_button = page.locator("button:has-text('Download!!'), input[value='Download!!']").first
            download_button.wait_for(state="visible", timeout=30000)
            
            print("  ⬇️  Downloading from No-Intro...")
            with page.expect_download(timeout=120000) as download_info:  # 2 minute timeout
                download_button.click()
            
            download = download_info.value
            zip_path = temp_dir / download.suggested_filename
            download.save_as(zip_path)
            download.path()  # Wait for completion
            
            if zip_path.exists():
                file_size = zip_path.stat().st_size
                size_mb = file_size / (1024 * 1024)
                print(f"  ✅ Download complete: {zip_path.name} ({size_mb:.2f} MB)")
            else:
                print("  ❌ Download failed")
                browser.close()
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                return []
            
            browser.close()
        
        # Extract ZIP and find No-Intro folder
        print("  📦 Extracting ZIP file...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find No-Intro folder
        no_intro_folder = None
        for item in temp_dir.rglob("No-Intro"):
            if item.is_dir():
                no_intro_folder = item
                break
        
        if not no_intro_folder:
            # Fallback: look for .dat files directly
            dat_files = list(temp_dir.rglob("*.dat"))
            if not dat_files:
                print("  ❌ No .dat files found in ZIP")
                shutil.rmtree(temp_dir)
                return []
            no_intro_folder = temp_dir  # Use temp_dir as the source
        
        # Get list of .dat files
        dat_files = list(no_intro_folder.glob("*.dat"))
        if not dat_files:
            print("  ❌ No .dat files found")
            shutil.rmtree(temp_dir)
            return []
        
        print(f"  ✅ Extracted {len(dat_files)} No-Intro DAT file(s)")
        
        # Clean up old DAT files
        if output_dir.exists():
            existing_dats = list(output_dir.glob("*.dat"))
            if existing_dats:
                print(f"  🗑️  Removing {len(existing_dats)} previous DAT file(s)...")
                for old_dat in existing_dats:
                    old_dat.unlink()
        
        # Copy .dat files to output directory
        print(f"  📋 Copying {len(dat_files)} fresh No-Intro DAT file(s)...")
        extracted_dats = []
        for dat_file in dat_files:
            shutil.copy2(dat_file, output_dir / dat_file.name)
            extracted_dats.append(output_dir / dat_file.name)
        
        shutil.rmtree(temp_dir)
        print(f"  ✅ Successfully processed {len(extracted_dats)}/{len(dat_files)} No-Intro DAT file(s)")
        return extracted_dats
        
    except PlaywrightTimeoutError as e:
        print(f"  ❌ Timeout error downloading No-Intro DAT files: {e}", file=sys.stderr)
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return []
    except Exception as e:
        print(f"  ❌ Error downloading No-Intro DAT file(s): {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return []


# ============================================================================
# Retool Processing Functions
# ============================================================================

def extract_retool_error(output: str) -> str:
    """
    Try to extract a single, human-friendly error message from Retool output.
    Handles wrapped lines and cases where the error includes a quoted file path.
    """
    if not output:
        return "Retool failed (no output captured)."

    # Normalize newlines and strip nulls
    text = output.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "").strip()
    
    # Strip ANSI escape codes (color codes) that might cause inconsistent display
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    def strip_bullet_point(msg: str) -> str:
        """Strip leading bullet point (•) and whitespace from message."""
        return re.sub(r"^•\s*", "", msg).strip()

    # Fast-path for the exact error you showed (and similar)
    m = re.search(r"No valid titles in input DAT file\..*", text, flags=re.IGNORECASE)
    if m:
        # Capture potentially wrapped continuation lines too
        start = m.start()
        tail = text[start:]
        lines = []
        for line in tail.split("\n"):
            if not line.strip():
                break
            if re.match(r"^[A-Z]:\\", line.strip()):  # e.g., "C:\Users\joemc>"
                break
            lines.append(line.strip())
        result = " ".join(lines)
        return strip_bullet_point(result)

    # General case: find Retool's "• Error:" section and read the next lines
    idx = text.find("• Error:")
    if idx != -1:
        after = text[idx + len("• Error:"):].lstrip()
        lines = []
        for line in after.split("\n"):
            s = line.strip()
            if not s:
                break
            if re.match(r"^[A-Z]:\\", s):  # shell prompt
                break
            # Stop if another major section starts
            if s.startswith("• ") and not s.startswith("• Error:"):
                break
            lines.append(s)

        joined = " ".join(lines)

        # If it looks like:  "<path>". The actual message...
        # extract just the message part after the last quote + period.
        m2 = re.search(r'"\s*[^"]+"\.\s*(.+)$', joined)
        if m2:
            result = m2.group(1).strip()
            return strip_bullet_point(result)

        # Otherwise just return the cleaned block
        if joined:
            result = re.sub(r"\s+", " ", joined).strip()
            return strip_bullet_point(result)

    # Fallback: last non-empty line that isn't a prompt/banner-ish
    candidates = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for ln in reversed(candidates):
        if not re.match(r"^[A-Z]:\\", ln) and "Retool" not in ln:
            return strip_bullet_point(ln)

    return "Retool failed (unable to parse error message)."


def run_retool(input_dat: Path, retool_dir: Path, output_dat_dir: Path, report_dir: Path, 
               retool_flags: list[str], retool_exclude: str, collection: str, config_name: str = "") -> tuple[Path | None, Path | None, str, str | None]:
    """
    Run Retool to filter a .dat file.
    Returns (output_dat_path, report_txt_path, status, error_message) where:
    - output_dat_path: Path to created DAT file, or None
    - report_txt_path: Path to report file, or None
    - status: "success", "not_required", or "failed"
    - error_message: Human-friendly error message if failed, None otherwise
    """
    retool_script = retool_dir / "retool.py"
    
    if not retool_script.exists():
        print(f"  ❌ Retool script not found: {retool_script}", file=sys.stderr)
        return None, None, "failed", "Retool script not found."
    
    # Create temporary output directory for Retool (it needs a directory)
    temp_output_dir = output_dat_dir / input_dat.stem
    temp_output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable,
        str(retool_script),
        str(input_dat),
    ] + retool_flags + ["--exclude", retool_exclude] + ["--output", str(temp_output_dir)]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=retool_dir,
            input="y\ny\ny\n",
            text=True,
            check=False,
            capture_output=True
        )
        
        # Find output .dat file in temp directory
        output_files = list(temp_output_dir.glob("*.dat"))
        output_dat = None
        if output_files:
            temp_dat = max(output_files, key=lambda p: p.stat().st_mtime)
            # Extract system name (without date) from input DAT for constant filename
            system_name = extract_system_name(input_dat.stem, collection)
            # Build constant output filename: "System Name (Fresh1G1R - config).dat"
            if config_name:
                new_name = f"{system_name} (Fresh1G1R - {config_name}){temp_dat.suffix}"
            else:
                new_name = f"{system_name}{temp_dat.suffix}"
            
            # Move DAT to final output directory with constant name
            final_dat_path = output_dat_dir / new_name
            # Remove existing file if it exists (will be replaced)
            if final_dat_path.exists():
                final_dat_path.unlink()
            shutil.move(str(temp_dat), str(final_dat_path))
            output_dat = final_dat_path
            
            # Update metadata to track this input->output mapping
            metadata = load_metadata(output_dat_dir)
            # Store just the filename (not absolute path) so it works across different machines
            # The filename uniquely identifies the DAT file
            input_filename = input_dat.name
            
            metadata[system_name] = {
                "input_filename": input_filename,
                "output_path": new_name
            }
            save_metadata(output_dat_dir, metadata)
        
        # Find report .txt file in temp directory
        report_files = list(temp_output_dir.glob("*.txt"))
        report_txt = None
        if report_files:
            temp_report = max(report_files, key=lambda p: p.stat().st_mtime)
            # Keep report filename as Retool generated it (includes date and Retool metadata)
            # Just move it to the report directory without renaming
            report_dir.mkdir(parents=True, exist_ok=True)
            final_report_path = report_dir / temp_report.name
            shutil.move(str(temp_report), str(final_report_path))
            report_txt = final_report_path
        
        # Clean up temp directory
        try:
            if temp_output_dir.exists():
                shutil.rmtree(temp_output_dir)
        except Exception:
            pass  # Ignore cleanup errors
        
        # Determine status
        # Build combined output: stdout + stderr
        retool_output = (result.stdout or "") + "\n" + (result.stderr or "")
        
        no_titles_match = (
            "No titles in the input DAT match your preferences" in retool_output or
            "No DAT file has been created" in retool_output
        )
        
        no_valid_titles = "No valid titles in input DAT file" in retool_output
        
        if result.returncode != 0:
            # Check for specific error conditions first (even if returncode != 0)
            if no_valid_titles:
                err_msg = extract_retool_error(retool_output)
                return None, report_txt, "no_games", err_msg
            elif no_titles_match:
                err_msg = extract_retool_error(retool_output)
                return None, report_txt, "not_required", err_msg
            # Retool failed to run
            err_msg = extract_retool_error(retool_output)
            return output_dat, report_txt, "failed", err_msg
        elif output_dat:
            # Retool ran successfully and produced output
            return output_dat, report_txt, "success", None
        elif no_titles_match:
            # Retool ran successfully but no titles matched preferences (everything filtered out)
            # Extract the error message from Retool output
            err_msg = extract_retool_error(retool_output)
            return None, report_txt, "not_required", err_msg
        elif no_valid_titles:
            # No valid titles in input DAT file
            err_msg = extract_retool_error(retool_output)
            return None, report_txt, "no_games", err_msg
        else:
            # Retool completed but produced no output and no known "filtered out" message
            err_msg = extract_retool_error(retool_output)
            return None, report_txt, "failed", err_msg
        
    except Exception as e:
        print(f"  ❌ Error running Retool: {e}", file=sys.stderr)
        return None, None, "failed", str(e)


def extract_system_name(filename_stem: str, collection: str) -> str:
    """
    Extract just the system name from a filename, removing dates and other metadata.
    
    For No-Intro: Extracts everything before the date pattern (YYYYMMDD-HHMMSS)
    For Redump: Extracts everything before the date pattern (YYYY-MM-DD HH-MM-SS)
    
    Examples:
    - No-Intro: "Acorn - Archimedes (20231029-220453)" -> "Acorn - Archimedes"
    - Redump: "Sony - PlayStation (2025-10-23 18-11-28) - Datfile (77)" -> "Sony - PlayStation"
    """
    # Remove Fresh1G1R suffix if present
    filename_stem = re.sub(r' \(Fresh1G1R - [^)]+\)$', '', filename_stem)
    
    if collection == "no-intro":
        # No-Intro: Extract everything before (YYYYMMDD-HHMMSS)
        date_pattern = r'\(\d{8}-\d{6}\)'
        date_match = re.search(date_pattern, filename_stem)
        if date_match:
            return filename_stem[:date_match.start()].strip()
        return filename_stem
    else:
        # Redump: Remove "- Datfile (number)" and extract everything before date
        normalized = re.sub(r' - Datfile \(\d+\)', '', filename_stem)
        # Remove date pattern: (YYYY-MM-DD HH-MM-SS) or (YYYY-MM-DD HH:MM:SS)
        date_pattern = r'\(\d{4}-\d{2}-\d{2} \d{2}[-:]\d{2}[-:]\d{2}\)'
        date_match = re.search(date_pattern, normalized)
        if date_match:
            return normalized[:date_match.start()].strip()
        # Remove any remaining Retool metadata
        normalized = re.sub(r' \(Retool.*$', '', normalized)
        return normalized.strip()


def get_metadata_path(output_dat_dir: Path) -> Path:
    """Get the path to the metadata file for a given output directory."""
    return output_dat_dir / ".metadata.json"


def load_metadata(output_dat_dir: Path) -> dict:
    """
    Load metadata mapping system names to input DAT information.
    Returns dict: {system_name: {"input_path": str, "input_date": str, "output_path": str}}
    """
    metadata_path = get_metadata_path(output_dat_dir)
    if not metadata_path.exists():
        return {}
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_metadata(output_dat_dir: Path, metadata: dict):
    """Save metadata to file."""
    metadata_path = get_metadata_path(output_dat_dir)
    output_dat_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"  ⚠️  Warning: Could not save metadata: {e}", file=sys.stderr)


def check_if_already_processed(input_dat: Path, output_dat_dir: Path, collection: str) -> Path | None:
    """
    Check if a processed DAT file already exists for the given input DAT.
    Uses metadata file to track which input DATs have been processed.
    Returns the existing processed DAT path if found, None otherwise.
    """
    if not output_dat_dir.exists():
        return None
    
    # Extract system name from input DAT
    input_name = input_dat.stem
    system_name = extract_system_name(input_name, collection)
    
    # Load metadata
    metadata = load_metadata(output_dat_dir)
    
    # Check if this system has been processed
    if system_name in metadata:
        entry = metadata[system_name]
        output_path = output_dat_dir / entry["output_path"]
        
        # Check if the output file still exists
        if output_path.exists():
            # Check if it's the same input DAT (by comparing filename)
            # If input filename matches, it's the same DAT (skip)
            # If input filename differs, it's a different version (reprocess)
            # Handle both new format (input_filename) and old format (input_path) for backward compatibility
            stored_input_filename = entry.get("input_filename")
            if not stored_input_filename and "input_path" in entry:
                # Old format: extract filename from absolute path
                stored_input_filename = Path(entry["input_path"]).name
            if stored_input_filename and input_dat.name == stored_input_filename:
                return output_path
            # Different input DAT for same system - will be reprocessed
    
    return None


def process_all_dats_with_retool(dat_files: list[Path], retool_dir: Path, output_dat_dir: Path, 
                                 report_dir: Path, retool_flags: list[str], retool_exclude: str, 
                                 collection: str = "redump", config_name: str = "") -> dict:
    """Process all downloaded DAT files through Retool with specific filter settings."""
    print_step(f"Processing {len(dat_files)} DAT files through Retool", "🔧")
    print(f"  📋 Exclude flags: {retool_exclude}")
    print(f"  📋 Command flags: {' '.join(retool_flags)}")
    
    results = {
        "successful": [],
        "not_required": [],
        "no_games": [],
        "failed": [],
        "skipped": []
    }
    
    # Format collection name for display (capitalize properly)
    collection_display = collection.replace("-", "-").title() if "-" in collection else collection.title()
    if collection == "no-intro":
        collection_display = "No-Intro"
    elif collection == "redump":
        collection_display = "Redump"
    
    for i, dat_file in enumerate(dat_files, 1):
        print(f"\n  {collection_display} [{i}/{len(dat_files)}] Processing {dat_file.name}...")
        
        # Check if already processed (unless ALWAYS_REPROCESS is True)
        if not ALWAYS_REPROCESS:
            existing_processed = check_if_already_processed(dat_file, output_dat_dir, collection=collection)
            if existing_processed:
                print(f"    ❎  Skipping: This specific DAT already has a processed equivalent present.")
                results["skipped"].append({
                    "input": dat_file,
                    "output": existing_processed
                })
                continue
        
        output_dat, report_txt, status, err_msg = run_retool(
            dat_file, retool_dir, output_dat_dir, report_dir, 
            retool_flags, retool_exclude, collection=collection, config_name=config_name
        )
        
        if status == "success" and output_dat:
            results["successful"].append({
                "input": dat_file,
                "output": output_dat,
                "report": report_txt
            })
            print(f"    ✅ Success: {output_dat.name}")
        elif status == "not_required":
            results["not_required"].append({
                "input": dat_file,
                "error": err_msg or "No titles in the input DAT match your preferences. No DAT file has been created."
            })
            error_display = err_msg if err_msg else dat_file.name
            print(f"    🚫  Not Required: {error_display}")
        elif status == "no_games":
            results["no_games"].append({
                "input": dat_file,
                "error": err_msg or "No valid titles in input DAT file."
            })
            error_display = err_msg if err_msg else dat_file.name
            print(f"    🎮 No Games: {error_display}")
        else:
            results["failed"].append({
                "input": dat_file,
                "error": err_msg or "Retool failed."
            })
            print(f"    ❎  Failed: {err_msg or dat_file.name}")
    
    skipped_count = len(results['skipped'])
    no_games_count = len(results['no_games'])
    summary_parts = [
        f"{len(results['successful'])} successful",
        f"{len(results['not_required'])} not required"
    ]
    if no_games_count > 0:
        summary_parts.append(f"{no_games_count} no games")
    summary_parts.append(f"{len(results['failed'])} failed")
    if skipped_count > 0:
        summary_parts.append(f"{skipped_count} skipped (already processed)")
    print(f"\n  📊 Summary: {', '.join(summary_parts)}")
    return results


# ============================================================================
# Main Function
# ============================================================================

def cleanup_old_files(directory: Path, pattern: str, keep_count: int = 7, collection: str = "redump") -> int:
    """
    Keep only the most recent files matching the pattern, grouped by system name + date.
    Deletes older files, keeping `keep_count` files per system+date combination.
    
    Groups reports by system name and date (e.g., all "System Name (20231029-220453) (Retool ...)" 
    reports for the same system+date are grouped together).
    """
    if not directory.exists():
        return 0
    
    files = list(directory.glob(pattern))
    if len(files) == 0:
        return 0
    
    # Group files by system name + date (for reports which keep their Retool-generated names)
    files_by_system: dict[str, list[Path]] = {}
    for file_path in files:
        # Extract system name + date from report filename
        # Reports have format: "System Name (date) (Retool ...).txt"
        stem = file_path.stem
        # Remove Fresh1G1R suffix if present
        stem = re.sub(r' \(Fresh1G1R - [^)]+\)$', '', stem)
        
        if collection == "no-intro":
            # Extract up to and including date: (YYYYMMDD-HHMMSS)
            date_pattern = r'\(\d{8}-\d{6}\)'
            date_match = re.search(date_pattern, stem)
            if date_match:
                normalized_system = stem[:date_match.end()]
            else:
                normalized_system = stem
        else:
            # Redump: Remove Retool metadata, keep system name + date
            normalized = re.sub(r' \(Retool.*$', '', stem)
            normalized_system = normalized
        
        if normalized_system not in files_by_system:
            files_by_system[normalized_system] = []
        files_by_system[normalized_system].append(file_path)
    
    # For each system, keep only the most recent `keep_count` files
    deleted_count = 0
    for system_name, system_files in files_by_system.items():
        if len(system_files) <= keep_count:
            continue
        
        # Sort by modification time (most recent first)
        system_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Delete older files
        for file_to_delete in system_files[keep_count:]:
            try:
                file_to_delete.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not delete {file_to_delete.name}: {e}")
    
    return deleted_count


def cleanup_previous_dats(output_dir: Path, config_name: str, collection: str, preserve_files: set[str] = None):
    """Remove previous DAT files from daily-processed-dat/{config_name}, keeping only the latest set."""
    if not output_dir.exists():
        return
    
    if preserve_files is None:
        preserve_files = set()
    
    # Remove existing .dat files, but preserve ones that match current input DATs
    dat_files = list(output_dir.glob("*.dat"))
    files_to_remove = [f for f in dat_files if f.name not in preserve_files]
    
    if files_to_remove:
        print(f"  🗑️  Removing {len(files_to_remove)} old DAT file(s) from {config_name}...")
        # Load metadata to clean up entries for removed files
        metadata = load_metadata(output_dir)
        for dat_file in files_to_remove:
            try:
                dat_file.unlink()
                # Remove metadata entry if it exists for this file
                # Extract system name from output filename (which has constant format)
                # Format: "System Name (Fresh1G1R - config).dat"
                system_name_match = re.match(r'^(.+?) \(Fresh1G1R - [^)]+\)\.dat$', dat_file.name)
                if system_name_match:
                    system_name = system_name_match.group(1)
                    if system_name in metadata and metadata[system_name].get("output_path") == dat_file.name:
                        del metadata[system_name]
            except Exception as e:
                print(f"  ⚠️  Could not remove {dat_file.name}: {e}")
        
        # Save updated metadata
        if metadata:
            save_metadata(output_dir, metadata)
        elif get_metadata_path(output_dir).exists():
            # Remove metadata file if empty
            try:
                get_metadata_path(output_dir).unlink()
            except Exception:
                pass
    
    if preserve_files and len(preserve_files) > 0:
        print(f"  ✅ Preserved {len(preserve_files)} existing processed file(s) that match current input DATs")


def main():
    """Main entry point."""
    print("=" * 70)
    print("🤖 Automated DAT Download and Retool Processing")
    print("=" * 70)
    
    # Discover all configurations
    print_step("Discovering configurations", "🔍")
    configs = discover_configs()
    
    if not configs:
        print("  ❌ No valid configurations found!")
        print(f"     Expected config directories in: {CONFIG_DIR}")
        print("     Each config directory should contain:")
        print("       - user-config.yaml")
        print("       - filters.py")
        sys.exit(1)
    
    print(f"  ✅ Found {len(configs)} configuration(s): {', '.join([c[0] for c in configs])}")
    
    # Create directory structure
    REDUMP_DIR.mkdir(parents=True, exist_ok=True)
    NO_INTRO_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Download/collect DAT files for each collection
    collection_dats = {}
    
    # Process Redump collection
    if "redump" in DAT_COLLECTIONS:
        print_step("Processing Redump collection", "📦")
        if SKIP_REDUMP_DOWNLOAD:
            print_step("Skipping Redump DAT download (using existing files)", "❎")
            redump_dats = list(REDUMP_DIR.glob("*.dat"))
            if not redump_dats:
                print("  ⚠️  No DAT files found in daily-virgin-dat/redump/ directory")
            else:
                print(f"  ✅ Found {len(redump_dats)} existing Redump DAT file(s)")
                collection_dats["redump"] = redump_dats
        else:
            redump_dats = download_all_redump_dats(REDUMP_DIR)
            if redump_dats:
                collection_dats["redump"] = redump_dats
            else:
                print("  ⚠️  No Redump DAT files downloaded")
    
    # Process No-Intro collection
    if "no-intro" in DAT_COLLECTIONS:
        print_step("Processing No-Intro collection", "📦")
        if SKIP_NO_INTRO_DOWNLOAD:
            print_step("Skipping No-Intro DAT download (using existing files)", "❎")
            no_intro_dats = list(NO_INTRO_DIR.glob("*.dat"))
            if not no_intro_dats:
                print("  ⚠️  No DAT files found in daily-virgin-dat/no-intro/ directory")
            else:
                print(f"  ✅ Found {len(no_intro_dats)} existing No-Intro DAT file(s)")
                collection_dats["no-intro"] = no_intro_dats
        else:
            no_intro_dats = download_no_intro_dats(NO_INTRO_DIR)
            if no_intro_dats:
                collection_dats["no-intro"] = no_intro_dats
            else:
                print("  ⚠️  No No-Intro DAT files downloaded")
    
    # Check if we have any DATs to process
    total_dats = sum(len(dats) for dats in collection_dats.values())
    if total_dats == 0:
        print("\n  ❌ No DAT files found to process. Exiting.")
        sys.exit(1)
    
    # Step 2: Setup Retool (once for all configs)
    print_step("Setting up Retool", "🔧")
    if not clone_retool_if_needed(RETOOL_DIR):
        print("  ❌ Failed to setup Retool. Exiting.")
        sys.exit(1)
    
    print_step("Installing Retool dependencies", "📦")
    install_retool_dependencies()
    
    print_step("Updating Retool", "🔄")
    update_retool_main(RETOOL_DIR)
    
    print_step("Updating Retool clone lists", "📥")
    update_retool_clone_lists(RETOOL_DIR)
    
    # Step 3: Preload all configuration settings
    config_settings = preload_config_settings(configs, DAT_COLLECTIONS)
    
    # Step 4: Process all DATs through Retool for each configuration and collection
    all_results = {}
    
    for (config_name, collection), settings in config_settings.items():
        # Skip if this collection has no DATs
        if collection not in collection_dats or not collection_dats[collection]:
            continue
        print("\n" + "=" * 70)
        print(f"📦 Processing configuration: {config_name} | Collection: {collection}")
        print("=" * 70)
        
        # Copy user config for this config
        print_step(f" Configuring Retool for {config_name}", "⚙️")
        copy_user_config(config_name, settings["user_config_path"])
        
        # Set up output directories for this config
        daily_output_dir = settings["daily_dir"]
        report_output_dir = settings["report_dir"]
        daily_output_dir.mkdir(parents=True, exist_ok=True)
        report_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get DATs for this collection
        collection_dat_files = collection_dats[collection]
        
        # Check for existing processed files BEFORE cleanup (if not always reprocessing)
        # This way we can preserve files that match current input DATs
        existing_processed_files = set()
        if not ALWAYS_REPROCESS:
            print_step(f"Checking for existing processed files for {config_name}/{collection}", "🔍")
            for dat_file in collection_dat_files:
                existing = check_if_already_processed(dat_file, daily_output_dir, collection=collection)
                if existing:
                    existing_processed_files.add(existing.name)
            if existing_processed_files:
                print(f"  ✅ Found {len(existing_processed_files)} existing processed file(s) that match current input DATs")
            else:
                print(f"  ℹ️  No existing processed files found - all {len(collection_dat_files)} DAT file(s) will be processed")
        
        # Clean up previous DATs for this config/collection (but preserve files we'll skip)
        print_step(f"Cleaning up previous DAT files for {config_name}/{collection}", "🧹")
        cleanup_previous_dats(daily_output_dir, f"{config_name}/{collection}", collection, preserve_files=existing_processed_files)
        
        # Clean up old reports (keep only last 7 per system)
        if report_output_dir.exists():
            deleted_reports = cleanup_old_files(report_output_dir, "*.txt", keep_count=7, collection=collection)
            if deleted_reports > 0:
                print(f"  🗑️  Removed {deleted_reports} old report file(s) (keeping last 7 per system)")
        
        # Process all DATs through Retool with this config's settings
        results = process_all_dats_with_retool(
            collection_dat_files, RETOOL_DIR, daily_output_dir, report_output_dir,
            settings["flags"], settings["exclude"], collection=collection, config_name=config_name
        )
        
        all_results[(config_name, collection)] = results
    
    # Clean up user-config.yaml from Retool config directory
    retool_config_file = RETOOL_CONFIG_DIR / "user-config.yaml"
    if retool_config_file.exists():
        try:
            retool_config_file.unlink()
            print("\n  🗑️  Cleaned up user-config.yaml from Retool config directory")
        except Exception as e:
            print(f"\n  ⚠️  Could not remove user-config.yaml: {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ Processing Complete")
    print("=" * 70)
    
    # Summary by collection
    for collection in DAT_COLLECTIONS:
        if collection in collection_dats:
            count = len(collection_dats[collection])
            if collection == "redump" and not SKIP_REDUMP_DOWNLOAD:
                print(f"  📥 Downloaded: {count} {collection} DAT file(s)")
            elif collection == "no-intro" and not SKIP_NO_INTRO_DOWNLOAD:
                print(f"  📥 Downloaded: {count} {collection} DAT file(s)")
            else:
                print(f"  📁 Using: {count} {collection} DAT file(s)")
    
    print(f"\n  📊 Results by configuration and collection:")
    
    for (config_name, collection), results in all_results.items():
        skipped_count = len(results.get('skipped', []))
        print(f"\n  📦 {config_name} / {collection}:")
        print(f"     ✅ Processed: {len(results['successful'])} DAT files to daily-processed-dat/{config_name}/{collection}/")
        print(f"     📄 Reports: {len(results['successful'])} report files to report/{config_name}/{collection}/")
        print(f"     🚫 Not Required: {len(results['not_required'])} DAT files (everything filtered out)")
        if len(results['no_games']) > 0:
            print(f"     🎮 No Games: {len(results['no_games'])} DAT files (no valid titles)")
        if skipped_count > 0:
            print(f"     ❎ Skipped: {skipped_count} DAT files (already processed)")
        print(f"     ❌ Failed: {len(results['failed'])} DAT files")
    
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)