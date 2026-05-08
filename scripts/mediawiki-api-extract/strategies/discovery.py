"""Discovery strategy implementations."""

import logging
import time
from typing import Optional

from ..client import ApiClient

log = logging.getLogger("mediawiki-api-extract")


class AllPagesDiscoveryStrategy:
    """Default discovery using action=query&list=allpages."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"page_list", "category_lookup"}

    def discover_pages(self, client: ApiClient, strategy: dict) -> list[dict]:
        api = strategy.get("api", {})
        namespaces = api.get("namespaces", [api.get("namespace", 0)])
        if not isinstance(namespaces, list):
            namespaces = [namespaces]

        all_pages = []
        for ns in namespaces:
            pages = []
            continue_token = None
            while True:
                params = {
                    "list": "allpages",
                    "apnamespace": ns,
                    "apfilterredir": "nonredirects",
                    "aplimit": 500,
                }
                if continue_token:
                    params["apcontinue"] = continue_token
                data = client.query(**params)
                result = data.get("query", {}).get("allpages", [])
                for p in result:
                    p["ns"] = ns
                pages.extend(result)
                if "continue" in data:
                    continue_token = data["continue"].get("apcontinue")
                else:
                    break
            all_pages.extend(pages)

        seen = set()
        deduped = []
        for p in all_pages:
            pid = p.get("pageid")
            if pid and pid not in seen:
                seen.add(pid)
                deduped.append(p)
            elif not pid:
                deduped.append(p)
        return deduped

    def discover_categories(self, client: ApiClient, page_titles: list[str], batch_size: int = 50) -> dict[str, list[str]]:
        categories = {}
        for i in range(0, len(page_titles), batch_size):
            batch = page_titles[i:i + batch_size]
            titles_str = "|".join(batch)
            data = client.query(titles=titles_str, prop="categories", cllimit="max")
            pages_data = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages_data.items():
                title = page_info.get("title", "")
                cats = [c["title"].replace("Category:", "") for c in page_info.get("categories", [])]
                categories[title] = cats
            time.sleep(0.2)
        return categories

    def classify_page(self, page_title: str, categories: list[str],
                      list_pages: dict[str, str],
                      page_categories: Optional[dict[str, str]] = None,
                      category_filters: Optional[list[str]] = None,
                      namespace: int = 0) -> str:
        import re
        filters = set(category_filters or [])
        page_categories = page_categories or {}

        title_norm = page_title.replace(" ", "_")
        if title_norm in list_pages:
            return list_pages[title_norm]
        if page_title in list_pages:
            return list_pages[page_title]

        filtered_cats = [c for c in categories if c not in filters]
        for cat in filtered_cats:
            if cat in page_categories:
                return page_categories[cat]

        dir_lookup = {}
        for _page, directory in list_pages.items():
            dir_lookup[directory] = directory
            for segment in directory.split("/"):
                norm = segment.replace(" ", "_").lower()
                dir_lookup[norm] = directory

        for directory in page_categories.values():
            dir_lookup[directory] = directory
            for segment in directory.split("/"):
                norm = segment.replace(" ", "_").lower()
                dir_lookup[norm] = directory

        dir_scores: dict[str, int] = {}
        for cat in filtered_cats:
            cat_norm = cat.replace(" ", "_")
            cat_lower = cat_norm.lower()
            for key, directory in dir_lookup.items():
                if cat_norm == key or cat == key:
                    dir_scores[directory] = dir_scores.get(directory, 0) + 2
                elif key.lower() in cat_lower or cat_lower in key.lower():
                    dir_scores[directory] = dir_scores.get(directory, 0) + 1

        if dir_scores:
            return max(dir_scores, key=dir_scores.get)
        return "Misc"

    def fetch_list_pages(self, client: ApiClient, list_pages: dict[str, str]) -> dict[str, str]:
        content = {}
        for page_title in list_pages:
            try:
                data = client.parse(page=page_title, prop="wikitext")
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                content[page_title] = wikitext
            except RuntimeError as e:
                log.warning("Failed to fetch list page %s: %s", page_title, e)
        return content


class CategoryMembersDiscoveryStrategy:
    """Discovery using action=query&list=categorymembers with namespace support."""

    @property
    def required_capabilities(self) -> set[str]:
        return {"page_list", "category_lookup"}

    def discover_pages(self, client: ApiClient, strategy: dict) -> list[dict]:
        api = strategy.get("api", {})
        taxonomy = api.get("taxonomy", {})
        page_categories = taxonomy.get("page_categories", {})
        namespaces = api.get("namespaces", [api.get("namespace", 0)])
        if not isinstance(namespaces, list):
            namespaces = [namespaces]

        all_pages = []
        for ns in namespaces:
            ns_pages = self._discover_for_namespace(client, page_categories, ns)
            for p in ns_pages:
                p["namespace"] = ns
            all_pages.extend(ns_pages)

        seen = set()
        deduped = []
        for p in all_pages:
            pid = p.get("pageid")
            if pid and pid not in seen:
                seen.add(pid)
                deduped.append(p)
            elif not pid:
                deduped.append(p)
        return deduped

    def _discover_for_namespace(self, client: ApiClient, page_categories: dict, ns: int) -> list[dict]:
        pages = []
        for category in page_categories:
            cmtitle = f"Category:{category}"
            continue_token = None
            while True:
                params = {
                    "list": "categorymembers",
                    "cmtitle": cmtitle,
                    "cmnamespace": ns,
                    "cmlimit": 500,
                }
                if continue_token:
                    params["cmcontinue"] = continue_token
                data = client.query(**params)
                result = data.get("query", {}).get("categorymembers", [])
                pages.extend(result)
                if "continue" in data:
                    continue_token = data["continue"].get("cmcontinue")
                else:
                    break
        return pages

    def discover_categories(self, client: ApiClient, page_titles: list[str], batch_size: int = 50) -> dict[str, list[str]]:
        categories = {}
        for i in range(0, len(page_titles), batch_size):
            batch = page_titles[i:i + batch_size]
            titles_str = "|".join(batch)
            data = client.query(titles=titles_str, prop="categories", cllimit="max")
            pages_data = data.get("query", {}).get("pages", {})
            for page_id, page_info in pages_data.items():
                title = page_info.get("title", "")
                cats = [c["title"].replace("Category:", "") for c in page_info.get("categories", [])]
                categories[title] = cats
            time.sleep(0.2)
        return categories

    def classify_page(self, page_title: str, categories: list[str],
                      list_pages: dict[str, str],
                      page_categories: Optional[dict[str, str]] = None,
                      category_filters: Optional[list[str]] = None,
                      namespace: int = 0) -> str:
        filters = set(category_filters or [])
        page_categories = page_categories or {}

        title_norm = page_title.replace(" ", "_")
        if title_norm in list_pages:
            return list_pages[title_norm]
        if page_title in list_pages:
            return list_pages[page_title]

        filtered_cats = [c for c in categories if c not in filters]
        for cat in filtered_cats:
            if cat in page_categories:
                return page_categories[cat]
                break
        else:
            dir_lookup = {}
            for _page, directory in list_pages.items():
                dir_lookup[directory] = directory
                for segment in directory.split("/"):
                    norm = segment.replace(" ", "_").lower()
                    dir_lookup[norm] = directory

            for directory in page_categories.values():
                dir_lookup[directory] = directory
                for segment in directory.split("/"):
                    norm = segment.replace(" ", "_").lower()
                    dir_lookup[norm] = directory

            dir_scores: dict[str, int] = {}
            for cat in filtered_cats:
                cat_norm = cat.replace(" ", "_")
                cat_lower = cat_norm.lower()
                for key, directory in dir_lookup.items():
                    if cat_norm == key or cat == key:
                        dir_scores[directory] = dir_scores.get(directory, 0) + 2
                    elif key.lower() in cat_lower or cat_lower in key.lower():
                        dir_scores[directory] = dir_scores.get(directory, 0) + 1

            if dir_scores:
                return max(dir_scores, key=dir_scores.get)
            return "Misc"

    def fetch_list_pages(self, client: ApiClient, list_pages: dict[str, str]) -> dict[str, str]:
        content = {}
        for page_title in list_pages:
            try:
                data = client.parse(page=page_title, prop="wikitext")
                wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
                content[page_title] = wikitext
            except RuntimeError as e:
                log.warning("Failed to fetch list page %s: %s", page_title, e)
        return content
