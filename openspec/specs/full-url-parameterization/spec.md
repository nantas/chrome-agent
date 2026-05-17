# full-url-parameterization Specification

## Purpose
Provides link and image URL full-path conversion for the Markdown output pipeline. Converts relative `/wiki/` and `/images/` paths to absolute `https://domain/...` URLs using a `wiki_domain` parameter sourced from strategy files. Ensures all output Markdown contains self-contained, resolvable URLs.

## Requirements

### Requirement: convert-internal-links-to-full-urls

The system SHALL provide `convert_links_to_md(html: str, wiki_domain: str) -> str` that converts all internal `<a href="/wiki/...">text</a>` links to `[text](https://wiki_domain/wiki/...)` Markdown format.

The method SHALL:
1. Accept `wiki_domain` as a REQUIRED parameter (no hardcoded default)
2. Convert `/wiki/*` hrefs to `https://{wiki_domain}/wiki/*`
3. Convert `/images/*` hrefs to `https://{wiki_domain}/images/*`
4. Convert any other path starting with `/` to `https://{wiki_domain}/*`
5. Preserve absolute external URLs (starting with `http://` or `https://`) unchanged
6. Preserve anchor-only links (`#section`) unchanged
7. Strip `javascript:` links to their text content only
8. Return empty string for links with no visible text content

#### Scenario: internal-wiki-link-full-url
- **WHEN** `convert_links_to_md('<a href="/wiki/Items">Items</a>', "bindingofisaacrebirth.wiki.gg")` is called
- **THEN** the output SHALL be `[Items](https://bindingofisaacrebirth.wiki.gg/wiki/Items)`

#### Scenario: internal-image-link-full-url
- **WHEN** `convert_links_to_md('<a href="/wiki/File:icon.png">icon</a>', "wiki.gg")` is called
- **THEN** the output SHALL be `[icon](https://wiki.gg/wiki/File:icon.png)`

#### Scenario: external-link-unchanged
- **WHEN** `convert_links_to_md('<a href="https://youtube.com/watch?v=abc">Video</a>', ...)` is called
- **THEN** the output SHALL be `[Video](https://youtube.com/watch?v=abc)`

#### Scenario: anchor-link-unchanged
- **WHEN** `convert_links_to_md('<a href="#Effects">Effects</a>', ...)` is called
- **THEN** the output SHALL be `Effects` (text only, no wrapping link)

#### Scenario: no-domain-default
- **WHEN** `convert_links_to_md()` is called without an explicit `wiki_domain` argument
- **THEN** the method SHALL raise a `TypeError`
- **AND** no default domain SHALL be applied

### Requirement: convert-internal-images-to-full-urls

The system SHALL provide `convert_images_to_md(html: str, wiki_domain: str, skip_patterns: list[str] = []) -> str` that converts `<img src="/images/...">` to `![alt](https://wiki_domain/images/...)` Markdown format.

The method SHALL:
1. Accept `wiki_domain` as a REQUIRED parameter
2. Convert `/images/*` src attributes to `https://{wiki_domain}/images/*`
3. Accept `skip_patterns` — a list of regex patterns; images whose `src` matches any pattern SHALL be excluded
4. Extract `alt` text from the `<img>` tag and use it as the Markdown image alt text
5. Return `![alt_text](full_url)` for each retained image

#### Scenario: internal-image-full-url
- **WHEN** `convert_images_to_md('<img src="/images/icon.png" alt="Item icon">', "bindingofisaacrebirth.wiki.gg")` is called
- **THEN** the output SHALL be `![Item icon](https://bindingofisaacrebirth.wiki.gg/images/icon.png)`

#### Scenario: skip-font-images
- **WHEN** `convert_images_to_md(html, domain, skip_patterns=["Font_TeamMeat"])` is called on HTML containing `<img src="/images/Font_TeamMeat_T.png" alt="T">`
- **THEN** the image SHALL be excluded from output (empty string)

#### Scenario: skip-dlc-indicators
- **WHEN** `convert_images_to_md(html, domain, skip_patterns=["Dlc_.*indicator"])` is called on HTML containing `<img src="/images/Dlc_r_indicator.png" alt="(in Repentance)">`
- **THEN** the image SHALL be excluded from output

#### Scenario: external-image-unchanged
- **WHEN** `convert_images_to_md()` processes `<img src="https://external.com/img.png" alt="ext">`
- **THEN** the output SHALL be `![ext](https://external.com/img.png)`

### Requirement: base-url-from-strategy

The pipeline SHALL extract `wiki_domain` from the strategy file's `domain` field or `api.base_url` field and pass it to `convert_links_to_md()` and `convert_images_to_md()`.

#### Scenario: domain-from-strategy-file
- **WHEN** `HtmlToMarkdownConverter` is instantiated with a strategy whose `domain` is `"bindingofisaacrebirth.wiki.gg"`
- **THEN** `wiki_domain` SHALL be set to `"bindingofisaacrebirth.wiki.gg"`
- **AND** all internal links and images SHALL use `https://bindingofisaacrebirth.wiki.gg/...` as the base URL

#### Scenario: domain-from-api-base-url
- **WHEN** `domain` field is absent but `api.base_url` is `"https://bindingofisaacrebirth.wiki.gg/api.php"`
- **THEN** `wiki_domain` SHALL be extracted as `"bindingofisaacrebirth.wiki.gg"`
