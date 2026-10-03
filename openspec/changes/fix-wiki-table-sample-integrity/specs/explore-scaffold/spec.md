# MODIFIED Requirements

### Requirement: self-check-precision
S5 SHALL 按完整词或有界完整短语检测重复，不匹配相邻单词的局部字符。S6 SHALL 逐表计直接结构行，避免嵌套双计数，不能因 mw-collapsible 而排除游戏数据。

#### Scenario: precision-and-loss
- WHEN 输入 with the / This is
- THEN S5 通过；hero hero 仍失败。
- WHEN 嵌套等级子表在转换中丢失
- THEN S6 失败。

### Requirement: rendered-structure-checks
S6 SHALL 比较可见内容结构，排除空白／纯嵌套布局行并计入多行表头折叠；真实数据行损失仍须失败。S8 SHALL 对照渲染后的标题文本，不能因链接语法或标点空白误报缺节。S5 版本格式扫描 SHALL 排除 URL 编号，但原文重复不能静默删改。

#### Scenario: linked-heading-and-url
- WHEN 标题含超链接、标点，正文链接带字母数字散列
- THEN 标题与格式检查通过；真实缺标题和未分隔版本仍失败。
