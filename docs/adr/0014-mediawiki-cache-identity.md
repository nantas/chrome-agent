# ADR 0014: Exact MediaWiki cache identity

## Status
Accepted — fix-mediawiki-extraction-integrity.

## Context
Space/separator replacement maps different titles to the same file and cannot reconstruct original titles. Predictable temporary filenames also collide between writers. Existing caches must remain readable without a bulk rewrite.

## Decision
Use v2- plus SHA-256 of exact UTF-8 title for new cache filenames within platform/domain scope. Validate stored title on every read. Use unique same-directory temporary files and atomic replace. Read safe legacy candidates only when their stored title matches. Enumerate metadata, not reversed filenames. Cache admission separately checks resolved acquisition and payload; a name match is insufficient.

## Consequences
Bounded names support Unicode, slashes and long titles without changing Markdown output naming. Old files remain untouched and may coexist with v2 entries. Invalid or ambiguous old entries become misses. Hash identity is internal storage, independent of the obsidian-safe-filenames change. Theoretical digest collisions cannot return another title because metadata is checked.
