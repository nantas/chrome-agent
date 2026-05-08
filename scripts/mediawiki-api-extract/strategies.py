"""Backward-compatibility shim — all symbols re-exported from the new sub-package.

This file exists so that any code doing `from scripts.mediawiki_api_extract.strategies import X`
continues to work during the migration period.  The canonical implementations now live in:
  - strategies/discovery.py
  - strategies/acquisition.py
  - strategies/link_resolver.py
  - strategies/template.py
  - strategies/list_assembler.py
  - converters/html_to_markdown.py
  - converters/wikitext_to_md.py
  - converters/card_stats.py
"""

# Import everything from the new strategies sub-package, which in turn
# re-exports converters as well.
from .strategies import *  # noqa: F401,F403
from .strategies import (  # explicit re-exports for type checkers
    DiscoveryStrategy,
    ContentAcquisitionStrategy,
    LinkResolver,
    TemplateProcessor,
    ListPageAssembler,
    AllPagesDiscoveryStrategy,
    CategoryMembersDiscoveryStrategy,
    WikitextOnlyAcquisitionStrategy,
    HybridAcquisitionStrategy,
    HtmlRenderedAcquisitionStrategy,
    ExactTitleLinkResolver,
    ShortNameLinkResolver,
    SimpleSubstitutionTemplateProcessor,
    StructuredTemplateProcessor,
    FrontmatterDrivenListPageAssembler,
    HybridListPageAssembler,
    HtmlToMarkdownConverter,
    convert_wikitext_to_markdown,
    convert_wikitable_to_markdown,
    extract_card_stats,
    split_card_list_pages,
    title_to_filepath,
    validate_links,
    validate_content_integrity,
    validate_images,
    run_validation,
    _split_templates,
    _replace_dpl_template,
    _split_template_args,
)
