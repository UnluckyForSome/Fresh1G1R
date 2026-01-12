# Fresh1G1R

Fresh1G1R generates fresh daily, up-to-date 1G1R (One Game One ROM) DAT files for Redump and No-Intro collections, processed with several different [Retool](https://github.com/unexpectedpanda/retool) filter configurations, currently: **Hearto**, **PropeR**, and **McLean**.

## What Is This?

This repository provides the latest, box-fresh 1G1R DAT files for every system in both Redump and No-Intro collections, processed through the latest [Retool](https://github.com/unexpectedpanda/retool) release with curated 1G1R filter configurations. The DAT files are automatically updated daily via GitHub Actions, ensuring the 1G1R DATs available are always the most current filtered collections.

**Three configurations are available:**
- **McLean** - The Custom Fresh1G1R configuration, which I use and is the most lean:
  - **Includes**: 🎮 Games only
  - **Options**: 🌐 Language filter (English), ✅ Prefer licensed versions
  - **Good For**: 👍 If you want just English language retail releases.

- **PropeR** - Based on the [PropeR 1G1R Collection](https://github.com/proper1g1r/proper1g1r-collection) rules:
  - **Includes**: 🎮 Games, ➕ Add-ons, 📚 Educational, 🔧 Fixed, 🎁 Bonus discs, 📢 Promotional
  - **Options**: ✅ Prefer licensed versions
  - **Good For**: 👍 If you want retail releases in any language, along with additional content.

- **Hearto** - Based on the [Hearto 1G1R Collection](https://www.reddit.com/r/Roms/comments/1k45s56/heartos_1g1r_nointroredump_collection_ds_ps1/) rules:
  - **Includes**: 🎮 Games, 🎯 Demos, ➕ Add-ons, ⚠️ Unlicensed, 🧪 Preproduction (protos, betas, alphas)
  - **Options**: ✅ Prefer licensed versions
  - **Good For**: 👍 Retail, unlicensed and promo releases in any language, along with additional content.

Each configuration processes both **Redump** (disc-based) and **No-Intro** (cartridge-based) DAT files with their respective filter settings.

## How Can I Use This?

The latest, up-to-date DAT files for every system are available in the `daily-processed-dat/` directory on GitHub:

### McLean Collection
- **Redump DATs**: https://github.com/UnluckyForSome/Fresh1G1R/tree/main/daily-processed-dat/McLean/redump
- **No-Intro DATs**: https://github.com/UnluckyForSome/Fresh1G1R/tree/main/daily-processed-dat/McLean/no-intro

### PropeR Collection
- **Redump DATs**: https://github.com/UnluckyForSome/Fresh1G1R/tree/main/daily-processed-dat/PropeR/redump
- **No-Intro DATs**: https://github.com/UnluckyForSome/Fresh1G1R/tree/main/daily-processed-dat/PropeR/no-intro

### Hearto Collection
- **Redump DATs**: https://github.com/UnluckyForSome/Fresh1G1R/tree/main/daily-processed-dat/Hearto/redump
- **No-Intro DATs**: https://github.com/UnluckyForSome/Fresh1G1R/tree/main/daily-processed-dat/Hearto/no-intro

**To use these DAT files:**
1. Navigate to the collection and system you want (e.g., `daily-processed-dat/McLean/redump/`)
2. Download the `.dat` file for your desired system
3. Use the DAT file with your ROM management tool (e.g., clrmamepro, RomVault, etc.)

All DAT files are updated daily, so you can always get the latest filtered collections without manual processing.

## Thanks

- **[hugo19941994](https://github.com/hugo19941994)** for [auto-datfile-generator](https://github.com/hugo19941994/auto-datfile-generator) - Inspiration for automated DAT processing
- **[iamyethere](https://www.reddit.com/user/iamyethere/)** for the [PropeR 1G1R Collection](https://github.com/proper1g1r/proper1g1r-collection) - PropeR configuration rules
- **[heartolazor](https://www.reddit.com/user/heartolazor/)** for the [Hearto 1G1R Collection](https://www.reddit.com/r/Roms/comments/1k45s56/heartos_1g1r_nointroredump_collection_ds_ps1/) - Hearto configuration rules
- **[Retool](https://github.com/unexpectedpanda/retool)** by [unexpectedpanda](https://github.com/unexpectedpanda) - The powerful 1G1R tool that makes this all possible
- **[Redump](http://redump.org)** - For providing disc-based DAT files
- **[No-Intro](https://www.no-intro.org)** - For providing cartridge-based DAT files