# Explore Report

- Target: https://slaythespire.wiki.gg/wiki/Slay_the_Spire_2:Main
- Repo ref: env:CHROME_AGENT_REPO
- Resolution: Resolved via CHROME_AGENT_REPO default (env:CHROME_AGENT_REPO).
- Workflow: platform_analysis
- Strategy matched: yes
- Scrapling preflight: available (env)
- Strategy file: ../agentic/chrome-agent/sites/strategies/slaythespire.wiki.gg/strategy.md
- Protection level: low
- Entry points: sts2_main_page
- Matched page type: sts2_main_page
- Recommended fetcher: get
- Anti-crawl refs: default

## Structure Clues
- Domain: slaythespire.wiki.gg
- Declared pages: sts2_main_page, sts2_list_page, sts2_entity_page, sts2_mechanic_page, sts2_character_page, sts2_act_page, sts2_ancient_page
- Matched URL pattern: /wiki/Slay_the_Spire_2:Main

## Next Action
- Use `chrome-agent fetch <url>` for content retrieval, or `chrome-agent crawl <url>` when bounded traversal is needed.
