# Change 2 (sts2-strategy-set) 产出质量评估报告

**日期**: 2026-05-07  
**作者**: Pi agent 实施后审  
**状态**: 待讨论  

## 背景

Change 2 (`sts2-strategy-set`) 在 Change 1 冻结的 5 个策略接口上新增了 5 个 StS2 专用策略实现和 L6 验证层。实施后对 `./outputs/slaythespire-wiki` 的产出进行了系统性质量审查，发现以下问题。

## 问题清单

### 问题 1：`QueryLink` 模板残留

**严重程度**: 高 — 影响几乎所有 StS2 实体页

**现象**: 产出页面中看到未处理的模板参数内容，例如 Bash.md:
```
Cards|rarity:Basic&color:Ironclad|Basic|2 Cards|type:Attack&color:Ironclad|Attack|2 Card
```

**根因追踪**:
- StS2 wikitext 使用 `{{QueryLink|Cards|rarity:Basic|...}}` 
- `QueryLink` **不在** `template_map` 中
- `expand_templates` 无法处理，返回原文
- `clean_remaining_templates` 的通用 regex 匹配到它，替换为参数内容（仅去掉 `{{` `}}`，保留全部 inner）

**判断**: 执行问题 — template_map 不完整  
**修复**: 将 `QueryLink` 加入 `sites/strategies/slaythespire.wiki.gg/strategy.md` 的 `template_map`，值为 `""`（与 `Cards` 相同，因为它只是卡片链接的包装器）

### 问题 2：列表页 index.md 含未处理 wikitext

**严重程度**: 高 — Cards/Relics/Potions/Events 的 index.md 内容不可用

**现象**: 产出中看到原始 wikitext 模板：
```
{{Sequel Disambiguation|2}}{{Ambox|...}}
{{#description2: ...}}{{#setmainimage: ...}}
{{#invoke:Cards/filtering|render|2}}
```

**根因追踪**:
- 列表页的 content 是手动构造的 `f"---\ntitle: ...\n---\n\n# {title}\n\n" + raw_wikitext`
- 这段内容没有经过 `convert_wikitext_to_markdown`，即没有执行 expand_templates、clean_remaining_templates、convert_links
- `HybridListPageAssembler.assemble_index` 只追加表格，不对 wikitext 做任何加工
- 根本原因在于 `extraction_results.json` 的设计只保存 status/error，不保存 content/rendered_html，导致 Phase C 恢复时需要重新构造内容

**判断**: 执行问题 — 绕过管线流程  
**修复方向**: 
- 修改 `pipeline.py` 的 `extraction_results.json` 持久化策略，为 list pages 保存转换后的 content 和 rendered_html
- 或者让 Phase C 在恢复时对 list pages 重新调用 `convert_wikitext_to_markdown`
- 需要将 list page 的原始 wikitext（来自 manifest 的 `list_page_content`）传递给 Phase C

### 问题 3：实体页没有任何图片

**严重程度**: 高 — 所有实体页缺失主图（DRUID infobox 图片）

**现象**: Bash.md 全文没有 `![...](...)` 图片链接

**根因追踪**:
- `HybridAcquisitionStrategy.has_dynamic` 检查：
  ```python
  has_dynamic = bool(re.search(r'\{\{\s*#\s*(invoke|dpl|lst|if|ifeq)\s*[:|]', wikitext, re.IGNORECASE))
  ```
- Bash wikitext 使用 `{{Card Infobox|Bash||2}}` —— 这个模板**内部**调用 Lua 生成图片，但 wikitext 层面不是 `{{#invoke:...}}`
- `has_dynamic` = False → `prop=images` 从未被请求 → `images` 始终为 None
- `process_single_page` 中的图片注入代码永远不会执行

**判断**: 设计问题  
**根因**:
- Design 的方案是"只在检测到动态内容时才补充请求"（减少 API 调用）
- 但检测模式只覆盖了 `{{#invoke:...}}`、`{{#dpl:...}}` 等裸露的 parser function 调用
- StS2 的 DRUID infobox 图片通过 `{{Card Infobox|...}}` 模板（内部调用 Lua）生成，在 wikitext 层面不可见
- 检测策略过于狭窄

**修复方向**:
- 扩展检测模式，覆盖 `{{Card Infobox|...}}`、`{{Power Infobox|...}}` 等 infobox 模板
- 或改为：只要 `frontmatter_fields` 包含 `image`，就无条件请求 `prop=images`
- 需要评估 API 调用量增加的影响

### 问题 4：卡片表格缺少链接

**严重程度**: 中 — 卡片名称不是可点击的链接

**现象**: 卡片表格中：
```
| Bash | Basic | Attack | Ironclad |
```
`Bash` 不是链接，应该是 `[Bash](Slay_the_Spire_2_Bash.md)`

**根因追踪**:
- `_extract_table_from_html` 中提取 card-box 数据：
  ```python
  name = box.get("data-name", "")
  if not name:
      img = box.find("img")
      if img:
          name = img.get("alt", "")
  ```
- 直接取文本，没有从 `<a href="/wiki/Slay_the_Spire_2:Bash">` 提取链接信息
- `get_text(strip=True)` 丢弃了所有 HTML 结构

**判断**: 执行问题 — 链接信息被丢弃  
**修复方向**:
- 从 card-box 中的 `<a>` 标签提取 `href` 和链接文本
- 使用 `ShortNameLinkResolver.resolve()` 将 wiki 链接转换为 Markdown 相对链接

### 问题 5：短名链接解析跨 namespace 选错目标

**严重程度**: 中 — 部分内部链接指向错误 namespace

**现象**: StS2/Cards/Bash.md 中：
```markdown
[Bash](../../StS1/Cards/Bash.md)
```
StS2 的 "Bash" 页面中，`[[Bash]]` 应解析到同 namespace 的 `StS2/Cards/Slay_the_Spire_2_Bash.md`，却解析到了 StS1 版本。

**根因追踪**:
```python
def resolve(self, target, display, source_dir, manifest_pages):
    # Step 1: exact match (不区分 namespace)
    page = pages_by_title.get(target)
    # target = "Bash" → pages_by_title["Bash"] = StS1 的 Bash 页面
```

- `_pages_by_title` 以 title 为 key，manifest 中同时有 `"Bash"` (StS1) 和 `"Slay the Spire 2:Bash"` (StS2)
- `get("Bash")` 返回 StS1 版本，**即使 source 在 StS2**
- 短名索引中的同 namespace 优先逻辑（Step 2）永远不会执行，因为 Step 1 已经返回了

**判断**: 设计问题  
**根因**:
- Design 规定 "先查 exact match，再查 short index，再查 namespace-prefixed match"
- 但没有规定 exact match 应该考虑 source_dir 的 namespace
- 当 `[[Bash]]` 出现在 StS2 页面中，exact match 找到 StS1 的 Bash 是错误行为

**修复方向**: exact match 时检查 namespace 匹配：
```python
page = pages_by_title.get(target)
if page and self._guess_namespace(page["target_directory"]) == self._guess_namespace(source_dir):
    return self._make_link(page, display, source_dir)
# 否则 fallthrough 到 short name resolution
```

## 根因分类汇总

| 类型 | 问题 | 数量 |
|------|------|------|
| **设计问题** | 图片检测策略过窄、短名解析 namespace 隔离缺失 | 2 |
| **执行问题** | template_map 不完整、列表页绕过管线、表格缺链接 | 3 |

## 后续步骤

1. **设计问题**（问题 3、5）需要回到 design 阶段讨论修正方案
2. **执行问题**（问题 1、2、4）可以在 Change 2 内修复

建议在当前 `openspec/changes/sts2-strategy-set` 中讨论设计修正，然后在本 session 或新 session 中实施修复。
