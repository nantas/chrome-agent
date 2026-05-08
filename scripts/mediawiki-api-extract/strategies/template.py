"""Template processor strategy implementations."""

import logging
import re

log = logging.getLogger("mediawiki-api-extract")


class SimpleSubstitutionTemplateProcessor:
    """Default template processor using simple string substitution."""

    def extract_frontmatter(self, wikitext: str, fields: list[str]) -> dict:
        frontmatter = {}
        if not fields:
            return frontmatter

        from ..converters.wikitext_to_md import _split_templates
        templates = _split_templates(wikitext)
        for tmpl in templates:
            inner = tmpl[2:-2]
            pipe_idx = inner.find("|")
            if pipe_idx < 0:
                continue
            params_str = inner[pipe_idx + 1:]

            found_any = False
            for field in fields:
                pattern = rf'\|\s*{re.escape(field)}\s*=\s*'
                m = re.search(pattern, params_str)
                if m:
                    start = m.end()
                    depth = 0
                    i = start
                    while i < len(params_str):
                        if params_str[i:i+2] == '{{':
                            depth += 1
                            i += 2
                        elif params_str[i:i+2] == '}}':
                            if depth > 0:
                                depth -= 1
                                i += 2
                            else:
                                break
                        elif params_str[i] == '|' and depth == 0:
                            rest = params_str[i+1:]
                            if re.match(r'\s*[\w. -]+\s*=', rest):
                                break
                            i += 1
                        else:
                            i += 1
                    value = params_str[start:i].strip()
                    if value:
                        for _ in range(3):
                            value = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', value)
                            value = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', value)
                        value = re.sub(r'\[\[[^|\]]*?\|([^\]]*?)\]\]', r'\1', value)
                        value = re.sub(r'\[\[([^\]]*?)\]\]', r'\1', value)
                        value = re.sub(r'<[^>]+>', '', value)
                        value = re.sub(r'\b\w+\|', '', value) if '|' in value and not any(c in value for c in '[]{}') else value
                        value = value.replace('<br>', ' ').replace('<br/>', ' ').strip()
                        value = value.strip()
                        if value:
                            frontmatter[field] = value
                            found_any = True
            if found_any:
                break
        return frontmatter

    def expand_templates(self, text: str, template_map: dict[str, str]) -> tuple[str, list[str]]:
        unrecognized = []
        if not template_map:
            return text, unrecognized

        def replace_template(match):
            full_match = match.group(0)
            inner = match.group(1)
            parts = inner.split("|")
            template_name = parts[0].strip()
            args = [p.strip() for p in parts[1:]] if len(parts) > 1 else []

            if template_name in template_map:
                fmt = template_map[template_name]
                if args:
                    try:
                        return fmt % args[0]
                    except (TypeError, ValueError):
                        return fmt
                return fmt
            else:
                unrecognized.append(template_name)
                return full_match

        expanded = re.sub(r'\{\{([^}]+)\}\}', replace_template, text)
        return expanded, unrecognized

    def remove_infobox(self, wikitext: str, fields: list[str]) -> str:
        if not fields:
            return wikitext
        from ..converters.wikitext_to_md import _split_templates
        templates = _split_templates(wikitext)
        for tmpl in templates:
            inner = tmpl[2:-2]
            pipe_idx = inner.find("|")
            if pipe_idx < 0:
                continue
            params_str = inner[pipe_idx + 1:]
            for field in fields:
                if re.search(rf'\|\s*{re.escape(field)}\s*=', params_str):
                    wikitext = wikitext.replace(tmpl, "")
                    break
        return wikitext

    def clean_remaining_templates(self, text: str) -> str:
        text = re.sub(r'\{\{for\|[^}]*\}\}', '', text)
        text = re.sub(r'\{\{Main\|([^}]*)\}\}', r'See also: \1', text)
        text = re.sub(r'\{\{See also\|([^}]*)\}\}', r'See also: \1', text)
        text = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', text)
        text = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', text)
        return text


class StructuredTemplateProcessor:
    """Template processor supporting positional and named arguments, with Lua awareness."""

    def extract_frontmatter(self, wikitext: str, fields: list[str]) -> dict:
        frontmatter = {}
        if not fields:
            return frontmatter

        from ..converters.wikitext_to_md import _split_templates
        templates = _split_templates(wikitext)
        for tmpl in templates:
            inner = tmpl[2:-2]
            pipe_idx = inner.find("|")
            if pipe_idx < 0:
                continue
            params_str = inner[pipe_idx + 1:]

            found_any = False
            for field in fields:
                pattern = rf'\|\s*{re.escape(field)}\s*=\s*'
                m = re.search(pattern, params_str)
                if m:
                    start = m.end()
                    depth = 0
                    i = start
                    while i < len(params_str):
                        if params_str[i:i+2] == '{{':
                            depth += 1
                            i += 2
                        elif params_str[i:i+2] == '}}':
                            if depth > 0:
                                depth -= 1
                                i += 2
                            else:
                                break
                        elif params_str[i] == '|' and depth == 0:
                            rest = params_str[i+1:]
                            if re.match(r'\s*[\w. -]+\s*=', rest):
                                break
                            i += 1
                        else:
                            i += 1
                    value = params_str[start:i].strip()
                    if value:
                        for _ in range(3):
                            value = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', value)
                            value = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', value)
                        value = re.sub(r'\[\[[^|\]]*?\|([^\]]*?)\]\]', r'\1', value)
                        value = re.sub(r'\[\[([^\]]*?)\]\]', r'\1', value)
                        value = re.sub(r'<[^>]+>', '', value)
                        value = re.sub(r'\b\w+\|', '', value) if '|' in value and not any(c in value for c in '[]{}') else value
                        value = value.replace('<br>', ' ').replace('<br/>', ' ').strip()
                        value = value.strip()
                        if value:
                            frontmatter[field] = value
                            found_any = True
            if found_any:
                break
        return frontmatter

    def expand_templates(self, text: str, template_map: dict[str, str]) -> tuple[str, list[str]]:
        unrecognized = []
        if not template_map:
            return text, unrecognized

        from ..converters.wikitext_to_md import _split_template_args

        def replace_template(match):
            full_match = match.group(0)
            inner = match.group(1)
            parts = _split_template_args(inner)
            template_name = parts[0].strip()
            args = parts[1:] if len(parts) > 1 else []
            kwargs = {}
            positional = []
            for arg in args:
                if '=' in arg:
                    k, v = arg.split('=', 1)
                    kwargs[k.strip()] = v.strip()
                else:
                    positional.append(arg.strip())

            if template_name.startswith("#invoke:"):
                unrecognized.append(f"Lua module: {template_name}")
                return full_match

            if template_name in template_map:
                fmt = template_map[template_name]
                if positional:
                    try:
                        return fmt % positional[0]
                    except (TypeError, ValueError):
                        pass
                if kwargs:
                    try:
                        result = fmt
                        for k, v in kwargs.items():
                            result = result.replace(f"%({k})s", v)
                        return result
                    except (TypeError, ValueError):
                        pass
                return fmt
            else:
                unrecognized.append(template_name)
                return full_match

        expanded = re.sub(r'\{\{([^}]+)\}\}', replace_template, text)
        return expanded, unrecognized

    def remove_infobox(self, wikitext: str, fields: list[str]) -> str:
        if not fields:
            return wikitext
        from ..converters.wikitext_to_md import _split_templates
        templates = _split_templates(wikitext)
        for tmpl in templates:
            inner = tmpl[2:-2]
            pipe_idx = inner.find("|")
            if pipe_idx < 0:
                continue
            params_str = inner[pipe_idx + 1:]
            for field in fields:
                if re.search(rf'\|\s*{re.escape(field)}\s*=', params_str):
                    wikitext = wikitext.replace(tmpl, "")
                    break
        return wikitext

    def clean_remaining_templates(self, text: str) -> str:
        text = re.sub(r'\{\{for\|[^}]*\}\}', '', text)
        text = re.sub(r'\{\{Main\|([^}]*)\}\}', r'See also: \1', text)
        text = re.sub(r'\{\{See also\|([^}]*)\}\}', r'See also: \1', text)
        text = re.sub(r'\{\{#invoke:[^}]+\}\}', '', text)
        text = re.sub(r'\{\{([^|{}]*?)\|([^{}]*?)\}\}', r'\2', text)
        text = re.sub(r'\{\{([^{}]*?)\}\}', r'\1', text)
        return text
