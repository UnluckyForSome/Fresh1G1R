# Processed DAT Files

This directory contains **processed and filtered** 1G1R (One Game One ROM) DAT files.

## What's Here?

These are the **final output** DAT files that have been:
- ✅ Downloaded from Redump and No-Intro
- ✅ Processed through [Retool](https://github.com/unexpectedpanda/retool) with 1G1R filtering
- ✅ Filtered according to the configuration rules (Hearto, McLean, or PropeR)
- ✅ Ready to use with ROM management tools

## Directory Structure

```
daily-1g1r-dat/
├── Hearto/
│   ├── redump/     # Processed disc-based DATs (PlayStation, Xbox, etc.)
│   └── no-intro/   # Processed cartridge-based DATs (Nintendo, Sega, etc.)
├── McLean/
│   ├── redump/
│   └── no-intro/
└── PropeR/
    ├── redump/
    └── no-intro/
```

## How to Use

1. Navigate to the collection you want (e.g., `Hearto/redump/`)
2. Download the `.dat` file for your desired system
3. Use it with your ROM management tool (clrmamepro, RomVault, etc.)

## Original Source Files

The original, unprocessed DAT files from Redump and No-Intro are stored in [`../daily-virgin-dat/`](../daily-virgin-dat/README.md).

---

📖 For more information about the different configurations and how this project works, see the [main README](../README.md).
