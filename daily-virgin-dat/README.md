# Virgin DAT Files

This directory contains **original, unprocessed** DAT files directly from Redump and No-Intro.

## What's Here?

These are the **raw input** DAT files that:
- 📥 Are downloaded directly from [Redump.org](http://redump.org) and [datomatic.no-intro.org](https://datomatic.no-intro.org)
- 🔄 Are updated daily when new versions are released
- ⚙️ Are used as input for the Retool processing pipeline
- 📦 Have **not** been filtered or processed yet

## Directory Structure

```
daily-virgin-dat/
├── redump/      # Original Redump DAT files (disc-based systems)
└── no-intro/    # Original No-Intro DAT files (cartridge-based systems)
```

## What Happens to These Files?

These virgin DAT files are automatically:
1. Downloaded/updated daily
2. Processed through Retool with 1G1R filtering
3. Saved to [`../daily-1g1r-dat/`](../daily-1g1r-dat/README.md) with the appropriate configuration filters applied

## Why Keep These?

- 🔍 **Reference**: Compare original vs. processed files
- 🔄 **Reprocessing**: Re-run processing with different configurations
- 📊 **Verification**: Verify what was filtered out
- 🛠️ **Development**: Test changes to the processing pipeline

---

📖 For more information about the processed files and configurations, see the [main README](../README.md).
