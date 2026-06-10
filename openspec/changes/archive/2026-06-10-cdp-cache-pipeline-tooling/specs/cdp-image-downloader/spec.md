# Specification Delta

## Capability 对齐（已确认）

- Capability: `cdp-image-downloader`
- 来源: `proposal.md`
- 变更类型: new
- 用户确认摘要: 确认 — CDP fetch→base64 下载图片 + 本地化

## 规范真源声明

- 本文件是该 capability 在本次 change 中的行为规范真源
- design / tasks / verification 必须引用本文件
- 项目页面回写不得替代本文件

## ADDED Requirements

### Requirement: Image download via CDP fetch
The downloader SHALL retrieve images from authenticated origins by executing `fetch(url)` inside a Chrome CDP session and converting the response to a base64 data URL.

- The downloader SHALL use an existing CDP target (tab) that has an active authenticated session for the target domain.
- Images larger than 2MB SHALL be skipped with an error logged.
- Failed downloads SHALL be logged with the URL and error reason.

#### Scenario: Successful PNG download
- **WHEN** `fetch()` returns a 200 response for a PNG image
- **THEN** the blob SHALL be converted to base64 via `FileReader.readAsDataURL()`, decoded, and written as a binary file

#### Scenario: HTTP error
- **WHEN** `fetch()` returns a 404 or 403 status
- **THEN** the download SHALL be skipped and the error logged with URL and HTTP status

### Requirement: Local file storage
Images SHALL be stored under `<output_dir>/images/` with a path structure mirroring the original URL's path relative to the document's `contents/` directory.

#### Scenario: Path mirroring
- **WHEN** the image URL is `https://.../Packages/Network/Guides/NX-Account_Guide/contents/Attachments/Attach_xxx/yyy.png`
- **THEN** the local path SHALL be `images/Attachments/Attach_xxx/yyy.png`

### Requirement: Markdown reference update
After downloading, all Markdown files SHALL be updated to replace the full external image URL with a relative `../images/` path.

#### Scenario: URL to relative path
- **WHEN** a Markdown file contains `![alt](https://developer.nintendo.com/.../Attachments/Attach_xxx/yyy.png)` and the image has been downloaded
- **THEN** the reference SHALL become `![alt](../images/Attachments/Attach_xxx/yyy.png)`

### Requirement: Deduplication
The downloader SHALL collect unique image URLs across all Markdown files before downloading, so each image is downloaded only once even if referenced from multiple pages.

#### Scenario: Shared image
- **WHEN** two Markdown files reference the same image URL
- **THEN** the image SHALL be downloaded once and both files SHALL be updated with the same relative path

### Requirement: Skip existing
The downloader SHALL skip images that already exist at the target local path with a file size greater than 100 bytes.

#### Scenario: Already downloaded
- **WHEN** `images/Attachments/Attach_xxx/yyy.png` already exists and is >100 bytes
- **THEN** the download SHALL be skipped and the existing file reused
