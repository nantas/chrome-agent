#!/usr/bin/env bash
set -euo pipefail

PROG="clean-mediawiki.sh"
SITE=""
DRY_RUN=false

usage() {
  cat <<EOF
Usage: $PROG [--site <profile>] [--dry-run] [<input.md>]

MediaWiki Markdown cleanup script with site-specific profiles.

Profiles:
  vampire-survivors   Rules validated on vampire.survivors.wiki
  balatro             Rules validated on balatrowiki.org
  generic-mediawiki   All rules enabled (may be overly aggressive)

Rule clusters:
  navigation  strip_footer, strip_edit_links, strip_skip_links
  template    strip_dpl_wikitext, strip_json_data, strip_empty_parens
  link        convert_nested_images, normalize_internal, strip_category_links
  table       normalize_infobox, fix_separators

Options:
  --site <name>   Select cleanup profile (default: generic-mediawiki)
  --dry-run        Print which rules would be applied without running
  --help           Show this help message

Examples:
  $PROG --site vampire-survivors < article.md
  $PROG --site balatro --dry-run < article.md
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --site)
      SITE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      break
      ;;
  esac
done

if [[ -z "$SITE" ]]; then
  SITE="generic-mediawiki"
  echo "[$PROG] No --site specified; defaulting to 'generic-mediawiki'." >&2
  echo "[$PROG] Consider using --site for better results." >&2
fi

# Profile rule enablement
enable_navigation=false
enable_template=false
enable_link=false
enable_table=false

enable_strip_footer=false
enable_strip_edit_links=false
enable_strip_skip_links=false
enable_strip_dpl_wikitext=false
enable_strip_json_data=false
enable_strip_empty_parens=false
enable_convert_nested_images=false
enable_normalize_internal=false
enable_strip_category_links=false
enable_normalize_infobox=false
enable_fix_separators=false

case "$SITE" in
  vampire-survivors)
    enable_navigation=true
    enable_template=true
    enable_link=true
    enable_table=true
    enable_strip_footer=true
    enable_strip_skip_links=true
    enable_strip_json_data=true
    enable_strip_empty_parens=true
    enable_convert_nested_images=true
    enable_normalize_internal=true
    enable_strip_category_links=true
    enable_normalize_infobox=true
    enable_fix_separators=true
    ;;
  balatro)
    enable_navigation=true
    enable_template=true
    enable_link=true
    enable_table=true
    enable_strip_footer=true
    enable_strip_edit_links=true
    enable_strip_skip_links=true
    enable_strip_dpl_wikitext=true
    enable_strip_empty_parens=true
    enable_convert_nested_images=true
    enable_normalize_internal=true
    enable_strip_category_links=true
    enable_normalize_infobox=true
    enable_fix_separators=true
    ;;
  generic-mediawiki)
    enable_navigation=true
    enable_template=true
    enable_link=true
    enable_table=true
    enable_strip_footer=true
    enable_strip_edit_links=true
    enable_strip_skip_links=true
    enable_strip_dpl_wikitext=true
    enable_strip_json_data=true
    enable_strip_empty_parens=true
    enable_convert_nested_images=true
    enable_normalize_internal=true
    enable_strip_category_links=true
    enable_normalize_infobox=true
    enable_fix_separators=true
    ;;
  *)
    echo "Unknown site profile: $SITE" >&2
    echo "Valid profiles: vampire-survivors, balatro, generic-mediawiki" >&2
    exit 1
    ;;
esac

if [[ "$DRY_RUN" == true ]]; then
  echo "[$PROG] DRY RUN for profile: $SITE"
  echo "[$PROG] Enabled clusters:"
  $enable_navigation && echo "  - navigation"
  $enable_template && echo "  - template"
  $enable_link && echo "  - link"
  $enable_table && echo "  - table"
  echo "[$PROG] Enabled rules:"
  $enable_strip_footer && echo "  - strip_footer"
  $enable_strip_edit_links && echo "  - strip_edit_links"
  $enable_strip_skip_links && echo "  - strip_skip_links"
  $enable_strip_dpl_wikitext && echo "  - strip_dpl_wikitext"
  $enable_strip_json_data && echo "  - strip_json_data"
  $enable_strip_empty_parens && echo "  - strip_empty_parens"
  $enable_convert_nested_images && echo "  - convert_nested_images"
  $enable_normalize_internal && echo "  - normalize_internal"
  $enable_strip_category_links && echo "  - strip_category_links"
  $enable_normalize_infobox && echo "  - normalize_infobox"
  $enable_fix_separators && echo "  - fix_separators"
  if [[ "$SITE" == "generic-mediawiki" ]]; then
    echo "[$PROG] WARNING: generic-mediawiki enables all rules. Some may be overly aggressive for unknown sites."
  fi
  exit 0
fi

if [[ "$SITE" == "generic-mediawiki" ]]; then
  echo "[$PROG] WARNING: generic-mediawiki profile enables all rules." >&2
  echo "[$PROG] The following rules may be overly aggressive for your site:" >&2
  echo "  strip_dpl_wikitext, strip_json_data, strip_edit_links, normalize_infobox" >&2
  echo "[$PROG] Consider using --dry-run first or specifying --site for better results." >&2
fi

# Read all input into a variable for multi-pass processing
INPUT=$(cat)

# Helper: run a sed expression only if a flag is true
apply_if() {
  local flag="$1"
  local expr="$2"
  if [[ "$flag" == "true" ]]; then
    echo "$INPUT" | sed -E "$expr"
  else
    echo "$INPUT"
  fi
}

# ===== Navigation Cluster =====
if $enable_navigation; then
  if $enable_strip_footer; then
    INPUT=$(echo "$INPUT" | sed -E '/^\[?(Tools|Privacy|About|Disclaimers|Terms|Navigation menu)\]?[[:space:]]*$/d')
    # Also remove lines that are common footer links
    INPUT=$(echo "$INPUT" | sed -E '/^\[?(Privacy policy|Terms of Use|Cookie statement|Mobile view)\]?[[:space:]]*$/d')
  fi
  if $enable_strip_edit_links; then
    INPUT=$(echo "$INPUT" | sed -E 's/\[edit\](\[source\])?[[:space:]]*//g')
    INPUT=$(echo "$INPUT" | sed -E '/^\[edit[^\]]*\][[:space:]]*$/d')
  fi
  if $enable_strip_skip_links; then
    INPUT=$(echo "$INPUT" | sed -E '/Jump to (navigation|search)/d')
  fi
fi

# ===== Template Cluster =====
if $enable_template; then
  if $enable_strip_dpl_wikitext; then
    # Remove lines that are DPL template calls
    INPUT=$(echo "$INPUT" | sed -E '/\{\{(hl|Chips|Mult|Seal|Edition|Planet|Spectral|Tarot|Vampire)[^\}]*\}\}/d')
  fi
  if $enable_strip_json_data; then
    # Remove lines that look like JSON arrays/objects (Scribunto data)
    INPUT=$(echo "$INPUT" | sed -E '/^[[:space:]]*\[.*\][[:space:]]*$/d')
    INPUT=$(echo "$INPUT" | sed -E '/^[[:space:]]*\{.*\}[[:space:]]*$/d')
    # Remove lines with quoted key-value pairs typical of JSON
    INPUT=$(echo "$INPUT" | sed -E '/^[[:space:]]*"[^"]+":\s*("[^"]*"|[0-9]+|true|false|null)[[:space:]]*,?[[:space:]]*$/d')
  fi
  if $enable_strip_empty_parens; then
    INPUT=$(echo "$INPUT" | sed -E 's/\(\)[[:space:]]*//g')
    INPUT=$(echo "$INPUT" | sed -E '/^[[:space:]]*\(\)[[:space:]]*$/d')
  fi
fi

# ===== Link Cluster =====
if $enable_link; then
  if $enable_convert_nested_images; then
    # Transform [![](thumb)](page) into ![](thumb)
    # Handle both markdown image inside link and bare nested patterns
    INPUT=$(echo "$INPUT" | sed -E 's/\[\!\[([^\]]*)\]\(([^)]+)\)\]\([^)]+\)/!\[\1\](\2)/g')
    # Also handle cases where the inner image has no alt text: [![](url)](page)
    INPUT=$(echo "$INPUT" | sed -E 's/\[\!\[\]\(([^)]+)\)\]\([^)]+\)/!\[\](\1)/g')
  fi
  if $enable_normalize_internal; then
    # Clean "title") residue from internal links: [text](url "title") -> [text](url)
    INPUT=$(echo "$INPUT" | sed -E 's/(\]\([^)]+)[[:space:]]+"[^"]+"\)/\1)/g')
    # Remove namespace prefixes like "File:", "Category:" from link text if exposed
    INPUT=$(echo "$INPUT" | sed -E 's/\[(File|Category|Template|Special):([^\]]+)\]/[\2]/g')
  fi
  if $enable_strip_category_links; then
    # Remove [[Category:...]] lines and standalone Category references
    INPUT=$(echo "$INPUT" | sed -E '/\[\[Category:/d')
    INPUT=$(echo "$INPUT" | sed -E '/^Category:/d')
  fi
fi

# ===== Table Cluster =====
if $enable_table; then
  if $enable_fix_separators; then
    # Insert missing separator rows after table headers
    # A header row is a line starting with | that contains text but no ---
    # If the next line is also a content row (not ---), insert separator
    INPUT=$(echo "$INPUT" | awk '
      /^\|/ && !/---/ {
        if (prev_is_header && !/---/) {
          # Count columns in previous header
          n = split(prev_line, cols, "|")
          sep = "|"
          for (i = 2; i < n; i++) {
            sep = sep " --- |"
          }
          print sep
        }
        prev_is_header = 1
        prev_line = $0
        print
        next
      }
      /^\|.*---/ {
        prev_is_header = 0
        print
        next
      }
      {
        prev_is_header = 0
        print
      }
    ')
  fi

  if $enable_normalize_infobox; then
    # Detect infobox rows with many empty columns and compress to | key | value |
    # Heuristic: line starts with |, has > 5 cells, and ≤ 2 non-empty cells
    INPUT=$(echo "$INPUT" | awk -F'|' '
      /^\|/ {
        non_empty = 0
        key = ""
        val = ""
        for (i = 2; i <= NF; i++) {
          gsub(/^[[:space:]]+|[[:space:]]+$/, "", $i)
          if ($i != "") {
            non_empty++
            if (key == "") key = $i
            else if (val == "") val = $i
          }
        }
        if (NF > 6 && non_empty <= 2 && key != "") {
          if (val == "") val = " "
          print "| " key " | " val " |"
          next
        }
      }
      { print }
    ')
  fi
fi

echo "$INPUT"
