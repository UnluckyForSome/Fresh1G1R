# Retool Configuration Files

This directory contains the filter configuration files used by [Retool](https://github.com/unexpectedpanda/retool) to generate 1G1R (One Game One ROM) DAT files.

## What's Here?

Each subdirectory contains the configuration for a specific 1G1R filter set:
- **Hearto** - Based on the [Hearto 1G1R Collection](https://www.reddit.com/r/Roms/comments/1k45s56/heartos_1g1r_nointroredump_collection_ds_ps1/) rules
- **Hearto-NoDemos** - Hearto with demos, kiosks, and samples removed
- **McLean** - Custom Fresh1G1R configuration (most lean)
- **PropeR** - Based on the [PropeR 1G1R Collection](https://github.com/proper1g1r/proper1g1r-collection) rules

## Directory Structure

```
config/
├── Hearto/
│   ├── filters.py        # Python filter rules
│   └── user-config.yaml  # Retool configuration settings
├── Hearto-NoDemos/
│   ├── filters.py
│   └── user-config.yaml
├── McLean/
│   ├── filters.py
│   └── user-config.yaml
└── PropeR/
    ├── filters.py
    └── user-config.yaml
```

## Configuration Files

### `filters.py`
- Contains Python code that defines which ROMs/games to keep or remove
- Implements the 1G1R logic specific to each configuration
- Handles region preferences, language filtering, duplicate detection, etc.

### `user-config.yaml`
- YAML configuration file for Retool
- Defines Retool flags and options
- Specifies output settings and processing parameters

## Configuration Differences

### Hearto
- **Includes**: Games, Demos, Add-ons, Unlicensed, Preproduction (protos, betas, alphas)
- **Language**: Any language
- **Best For**: Comprehensive collections including unlicensed and promotional releases

### Hearto-NoDemos
- **Includes**: Games, Add-ons, Unlicensed, Preproduction (protos, betas, alphas)
- **Language**: Any language
- **Best For**: The Hearto set without demo discs

### McLean
- **Includes**: Games only
- **Language**: English only
- **Best For**: Lean collections with just English retail releases

### PropeR
- **Includes**: Games, Add-ons, Educational, Fixed, Bonus discs, Promotional
- **Language**: Any language
- **Best For**: Retail releases in any language with additional content

## How These Are Used

1. The automation script (`automate.py`) loads the appropriate configuration
2. Retool processes each DAT file using the selected configuration's rules
3. The filtered results are saved to `daily-1g1r-dat/{config}/{collection}/`
4. Processing reports are saved to `report/{config}/{collection}/`

## Modifying Configurations

⚠️ **Note**: Modifying these files will change how DAT files are processed. Changes will take effect on the next automated run.

To customize:
1. Edit the `filters.py` or `user-config.yaml` files
2. Run the automation script locally to test changes
3. Commit changes to apply them to the automated daily processing

---

📖 For more information about the project and how to use the processed DATs, see the [main README](../README.md).
