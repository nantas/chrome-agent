# Specification Delta: semantic-directory-mapping

## Capability 对齐（已确认）

- Capability: `semantic-directory-mapping`
- 来源: `proposal.md` New Capabilities
- 变更类型: `new`
- 用户确认摘要: 用户确认 ns=0 页面放根目录，ns=3000 页面放 `Slay_the_Spire_2/` 子目录，ns=14 分类页放 `Category_Name/index.md`

## 规范真源声明

- 本文件是 `semantic-directory-mapping` 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: namespace-based-directory-mapping
The system SHALL map each wiki page title to a filesystem path based on its MediaWiki namespace, using semantic directory containers.

#### Scenario: map-sts1-content-page
- **WHEN** a page has namespace `ns=0` (main/StS1) and title `Bash`
- **THEN** its output path SHALL be `Bash.md` in the root output directory
- **AND** the filename SHALL be derived by slugifying the title with `_` separator

#### Scenario: map-sts2-content-page
- **WHEN** a page has namespace `ns=3000` (Slay the Spire 2) and title `Slay the Spire 2:Bash`
- **THEN** its output path SHALL be `Slay_the_Spire_2/Bash.md`
- **AND** the `Slay the Spire 2:` namespace prefix SHALL be stripped before slugification
- **AND** the `Slay_the_Spire_2` directory SHALL serve as the namespace container

#### Scenario: map-sts2-list-page
- **WHEN** a page has namespace `ns=3000` and title `Slay the Spire 2:Cards_List`
- **THEN** its output path SHALL be `Slay_the_Spire_2/Cards_List.md`
- **AND** it SHALL NOT be treated as a category page

#### Scenario: map-category-page
- **WHEN** a page has namespace `ns=14` and title `Category:Cards`
- **THEN** its output path SHALL be `Cards/index.md`
- **AND** the `Category:` prefix SHALL be stripped
- **AND** the filename SHALL always be `index.md`

#### Scenario: map-category-page-with-spaces
- **WHEN** a page has namespace `ns=14` and title `Category:Slay the Spire 2 Cards`
- **THEN** its output path SHALL be `Slay_the_Spire_2_Cards/index.md`
- **AND** spaces SHALL be replaced with `_` in the directory name

### Requirement: slugification-rules
The system SHALL apply consistent slugification to all path components.

#### Scenario: slugify-title
- **WHEN** converting a page title to a filename or directory name
- **THEN** spaces SHALL be replaced with `_`
- **AND** special characters (`:`, `/`) SHALL be replaced with `_`
- **AND** the result SHALL be filesystem-safe

### Requirement: unique-path-guarantee
The system SHALL ensure no two distinct wiki pages map to the same output path.

#### Scenario: collision-sts1-sts2-same-name
- **WHEN** both `Bash` (ns=0) and `Slay the Spire 2:Bash` (ns=3000) exist
- **THEN** they SHALL map to `Bash.md` and `Slay_the_Spire_2/Bash.md` respectively
- **AND** neither SHALL overwrite the other
