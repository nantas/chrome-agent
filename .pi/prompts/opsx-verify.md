# opsx-verify — chrome-agent 项目级覆盖

> 本文件是 `~/.pi/agent/prompts/opsx-verify.md` 的项目级覆盖。
> 仅包含差异部分，未覆盖的步骤沿用全局 prompt。

## 追加步骤 3.5：运行测试套件

在全局 prompt 步骤 3（加载 artifacts）之后、步骤 4（初始化验证报告）之前，执行以下步骤：

### 3.5.1 检查 test_runner 是否存在

```bash
test -f scripts/test_runner.py && echo "EXISTS" || echo "NOT_FOUND"
```

- 若输出 `NOT_FOUND`，跳过本步骤，在验证报告中备注"项目测试运行器不存在，跳过测试套件检查"。
- 若输出 `EXISTS`，继续 3.5.2。

### 3.5.2 运行测试套件

```bash
python3 scripts/test_runner.py all 2>&1
```

记录退出码和输出。

### 3.5.3 将结果纳入验证报告

根据退出码和输出，在验证报告中增加 "Test Suite" 部分：

**退出码 0（全部通过）**：
- 添加信息："Test Suite: 全部通过"

**退出码非 0（存在失败）**：
- 解析输出中的失败测试
- 按 J3 分级将每个失败纳入报告：
  - 新增模块无测试 → **CRITICAL**
  - 修改模块未更新测试 → **WARNING**
  - 其他测试失败 → **WARNING**

### 3.5.4 文档变更豁免

若本次 change 仅修改 `.md` 文件，跳过 3.5.2 和 3.5.3，在报告中备注"纯文档变更，跳过测试套件检查"。
