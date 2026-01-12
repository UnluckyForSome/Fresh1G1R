# Retool exclude flags for Hearto configuration
# These flags are passed to Retool's --exclude option
#
# Exclusion flag descriptions (from Retool CLI documentation):
# a - Applications: Titles with DAT file category "Applications", or with "(Program)", "(Test Program)", "Check Program", "Sample Program" in the name
# A - Audio: Titles with DAT file category "Audio"
# b - Bad dumps: Titles marked as bad dumps with a "[b]" in the name
# B - BIOS and other chips: Titles with DAT file category "Console", or with "[BIOS]", "(Enhancement Chip)" in the name
# c - Coverdiscs: Titles with DAT file category "Coverdiscs"
# d - Demos, kiosks, and samples: Titles with DAT file category "Demos", or various demo/kiosk/sample text in the name
# D - Add-ons: Titles with DAT file category "Add-Ons"
# e - Educational: Titles with DAT file category "Educational"
# f - Fixed: Titles with "[f]" in the name (fixed/corrected dumps)
# k - MIA: Titles with ROMs declared as missing in action in the clone lists or DAT files
# m - Manuals: Titles with "(Manual)" in the name
# M - Multimedia: Titles with DAT file category "Multimedia"
# o - Bonus discs: Titles with DAT file category "Bonus Discs"
# p - Pirate: Titles with "(Pirate)" in the name
# P - Preproduction: Titles with DAT file category "Preproduction", or with "(Alpha)", "(Beta)", "(Proto)", etc. in the name
# r - Promotional: Titles with DAT file category "Promotional", or with "(Promo)", "EPK", "Press Kit" in the name
# u - Unlicensed: Titles unauthorized by console manufacturers, marked by "(Unl)", "(Aftermarket)", "(Pirate)" in the name
# v - Video: Titles with DAT file category "Video"
#
# Hearto configuration:
# Excludes: Applications (a), Audio (A), BIOS (B), bad dumps (b), Coverdiscs (c), Educational (e), Fixed (f), MIA (k), Manuals (m), Multimedia (M), Bonus discs (o), Pirate (p), Promotional (r), Video (v)
# Includes: Demos (d), Add-ons (D), Unlicensed (u), Preproduction (P)
exclude = "AaBbcefkmMoprv"

# Retool command-line options (from Retool CLI documentation):
#
# Options:
# -c: Prefer titles with RetroAchievements (data source uses hashes from CHD/RVZ files for disc-based images)
# -d: Disable 1G1R filtering - ignore clone lists and treat each title as unique (not compatible with --legacy)
# -l: Filter by languages using a list (if a title doesn't support any of the languages on the list, it's removed)
# -n: Use local names for titles if available (e.g., Japanese characters instead of romanized names)
# -o: Prefer oldest production versions instead of newest (useful for speedrunners and those concerned about censorship)
# -r: Prefer regions over languages (forces strict adherence to region priority regardless of language support)
# -y: Prefer licensed versions over unlicensed, aftermarket, or homebrew titles
# -z: Prefer titles ripped from modern rereleases over original system releases (reverses default behavior)
# --compilations: How compilations should be handled (i=always prefer individual, k=keep both, o=optimize for least duplication)
# --nooverrides: Disable global and system overrides
#
# Outputs:
# --labelmia: Mark files as MIA with an mia="yes" attribute (don't use if you're a DATVault subscriber)
# --labelretro: Mark titles with a retroachievements="yes" attribute
# --listnames: Also output a TXT file of just the kept title names
# --machine: Export each title node using the MAME standard of <machine> instead of <game>
# --originalheader: Use the original input DAT file headers in output DAT files
# --output <folder>: Set an output folder where the new 1G1R DAT file/s will be created
# --regionsplit: Split the result into multiple DAT files based on region (not compatible with --legacy)
# --removesdat: Also output DAT files containing titles that were removed from 1G1R DAT files
# --replace: Replace input DAT files with Retool versions (not compatible with --output)
# --report: Also output a report of the titles that have been kept, removed, and set as clones
# --reprocess: Let DAT files be processed even if Retool has already processed them
#
# Debug:
# --config <file>: Set a custom user config file to use instead of the default
# --clonelist <file>: Set a custom clone list to use instead of the default
# --legacy: Output DAT files in legacy parent/clone format (not compatible with -d)
# --metadata <file>: Set a custom metadata file to use instead of the default
# --mia <file>: Set a custom MIA file to use instead of the default
# --ra <file>: Set a custom RetroAchievements file to use instead of the default
# --singlecpu: Disable multiprocessor usage (forces single CPU core)
# --trace <regex>: Trace a title through the Retool process for debugging
# --warnings: Report clone list warnings during processing
# --warningpause: Pause when a clone list warning is found
#
# Retool command-line flags
flags = [
    "-y",      # Prefer licensed versions over unlicensed, aftermarket, or homebrew titles
    "--report" # Also output a report of the titles that have been kept, removed, and set as clones
               # Note: Not filtering by languages
]