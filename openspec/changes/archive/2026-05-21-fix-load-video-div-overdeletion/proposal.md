# Proposal

## 问题定义

`HtmlToMarkdownConverter.clean_html()` 中的 YouTube oEmbed 清理循环存在过度删除 bug。

当 wiki 页面包含 YouTube 视频嵌入（`<figure class="embedvideo">`）时，`parser.css("div")` 遍历所有 div 节点并检查 `text(deep=True)` 是否包含 "Load video"。由于 `mw-parser-output`（页面内容根容器）作为祖先节点，其 deep text 自然包含嵌套的视频组件文本，导致**整个页面内容被 `decompose()` 销毁**。

**实测影响**：BOI 100 页基线测试中，99 个缓存页面有 **20 个被清空**（所有含 YouTube 视频嵌入的页面），输出 markdown 仅保留 video link 提取的几行链接。

## 范围边界

**In scope**：
- 修复 `clean_html()` 中 "Load video" div 清理逻辑，阻止对祖先节点的误删
- 更新 boi-crawl-100-validation-baseline.json 以反映修复后的改善
- 验证修复后所有 99 页输出完整性

**Out of scope**：
- 不改变 video link 提取逻辑（`extract_video_links` 工作正常）
- 不引入新的 CSS 选择器引擎或依赖
- 不重构 converter 整体架构

## Capabilities

### New Capabilities

无新增能力。

### Modified Capabilities

无既有 spec 需修改（converter 为内部实现，无冻结规范）。

## Capabilities 待确认项

- [x] 能力清单已与用户确认（纯 bug fix，无能力变更）

## Impact

- **直接影响**：20/99 页面内容从"几乎为空"恢复为完整 markdown
- **验证指标**：empty_content 应从 1 降为 0（或保持不变，因仅影响内容量而非文件存在性）
- **回归风险**：低——修复仅缩小删除范围，不扩大
- **基线更新**：unavailable_images 和 broken_links 数值可能变化（更多内容 = 更多链接和图片引用）

## 关联绑定

- 关联 binding: `binding.md`
- 已确认标准页 / 项目页 / 回写目标：无需回写（内部 bug fix）
