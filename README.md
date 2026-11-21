# 🎮 Fresh1G1R

> ***Update 21/11/26 - Potentially Breaking Changes***
>
> Due to the daily DAT commits growing this repository to several GB, new DATs are found in **[releases](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest)** instead of the `daily-1g1r-dat/` folders. Those folders have been removed, so old links to them no longer work. Use the download links in [How Can I Use This?](#-how-can-i-use-this) instead.

Fresh1G1R generates fresh daily, up-to-date 1G1R (One Game One ROM) DAT files for [Redump](https://redump.info) and [No-Intro](https://www.no-intro.org) collections, processed with several different [Retool](https://github.com/unexpectedpanda/retool) filter configurations, currently: **[Hearto](#-hearto)**, **[Hearto (No Demos)](#-hearto-no-demos)**, **[PropeR](#-proper)**, and **[McLean](#-mclean)**.

## ❓ What Is This?

This repository provides the latest, box-fresh 1G1R DAT files for every system in both [Redump](https://redump.info) and [No-Intro](https://www.no-intro.org) collections, processed through the latest [Retool](https://github.com/unexpectedpanda/retool) release with curated 1G1R filter configurations. The DAT files are automatically updated daily via GitHub Actions, ensuring the 1G1R DATs available are always the most current filtered collections.

## 📚 Available Collections

**Four configurations are available:**

### 🧼 McLean
The Custom Fresh1G1R configuration, which I use and is the most lean:
- **Includes**: 🎮 Games only
- **Options**: 🌐 Language filter (English), ✅ Prefer licensed versions
- **Good For**: 👍 If you want just English language retail releases.

### 📦 PropeR
Based on the [PropeR 1G1R Collection](https://github.com/proper1g1r/proper1g1r-collection) rules:
- **Includes**: 🎮 Games, ➕ Add-ons, 📚 Educational, 🔧 Fixed, 🎁 Bonus discs, 📢 Promotional
- **Options**: ✅ Prefer licensed versions
- **Good For**: 👍 If you want retail releases in any language, along with additional content.

### ❤️ Hearto
Based on the [Hearto 1G1R Collection](https://www.reddit.com/r/Roms/comments/1k45s56/heartos_1g1r_nointroredump_collection_ds_ps1/) rules:
- **Includes**: 🎮 Games, 🎯 Demos, ➕ Add-ons, ⚠️ Unlicensed, 🧪 Preproduction (protos, betas, alphas)
- **Options**: ✅ Prefer licensed versions
- **Good For**: 👍 Retail, unlicensed and promo releases in any language, along with additional content.

### ❤️ Hearto (No Demos)
Hearto, with demos, kiosks, and samples removed:
- **Includes**: 🎮 Games, ➕ Add-ons, ⚠️ Unlicensed, 🧪 Preproduction (protos, betas, alphas)
- **Options**: ✅ Prefer licensed versions
- **Good For**: 👍 The Hearto set without demo discs, and without the duplicate artwork those demos add when you scan a collection.

---

Each configuration processes both **💿 [Redump](https://redump.info)** (disc-based) and **🎮 [No-Intro](https://www.no-intro.org)** (cartridge-based) DAT files with their respective filter settings.

---

## 🚀 How Can I Use This?

The latest DAT files for every system are published daily as a **[GitHub release](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest)**, as one zip per collection:

| Collection | 💿 Redump | 🎮 No-Intro |
|---|---|---|
| 🧼 McLean | [Redump](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-McLean-Redump.zip) | [No-Intro](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-McLean-No-Intro.zip) |
| 📦 PropeR | [Redump](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-PropeR-Redump.zip) | [No-Intro](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-PropeR-No-Intro.zip) |
| ❤️ Hearto | [Redump](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-Hearto-Redump.zip) | [No-Intro](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-Hearto-No-Intro.zip) |
| ❤️ Hearto (No Demos) | [Redump](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-Hearto-NoDemos-Redump.zip) | [No-Intro](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-Hearto-NoDemos-No-Intro.zip) |
| 📄 Original (unfiltered source DATs) | [Redump](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-Original-Redump.zip) | [No-Intro](https://github.com/UnluckyForSome/Fresh1G1R/releases/latest/download/Fresh1G1R-Original-No-Intro.zip) |

These links always point at the newest release, so they also work in scripts.

### 📥 To use these DAT files:

1. ⬇️ Download the zip for the collection you want from the table above
2. 📂 Extract it: it holds one `.dat` file per system
3. 🔧 Use the DAT files with your ROM management tool (e.g., [clrmamepro](https://mamedev.emulab.it/clrmamepro/), [RomVault](https://www.romvault.com/), etc.)

Each release's notes list the systems that changed since the previous one, and `Fresh1G1R-Reports.zip` holds Retool's reports for that run. The last 7 releases are kept.

---

## 🙏 Thanks

- **[hugo19941994](https://github.com/hugo19941994)** for **[auto-datfile-generator](https://github.com/hugo19941994/auto-datfile-generator)** — Inspiration for automated DAT processing  
- **[iamyethere](https://www.reddit.com/user/iamyethere/)** for the **[PropeR 1G1R Collection](https://github.com/proper1g1r/proper1g1r-collection)** — PropeR configuration rules  
- **[heartolazor](https://www.reddit.com/user/heartolazor/)** for the **[Hearto 1G1R Collection](https://www.reddit.com/r/Roms/comments/1k45s56/heartos_1g1r_nointroredump_collection_ds_ps1/)** — Hearto configuration rules  
- **[unexpectedpanda](https://github.com/unexpectedpanda)** for **[Retool](https://github.com/unexpectedpanda/retool)** — The powerful 1G1R tool that makes this all possible  
- **[Redump](https://redump.info)** — For providing disc-based DAT files  
- **[No-Intro](https://www.no-intro.org)** — For providing cartridge-based DAT files

---
