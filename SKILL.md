---
name: ref-downloader
description: >
  批量下载一篇论文的所有参考文献 PDF。接受 Zotero PDF 路径或 DOI 字符串作为输入，
  自动从 Zotero 数据库或 PDF 文本中查找 DOI，并通过单入口脚本串起
  extract_refs → validate_refs → download_refs 流水线。
  对 PDF 输入，输出到原论文同级目录下的 {文件名}_refs/ 子文件夹；
  对 DOI 输入，默认输出到当前工作目录下的 {PROJECT_NAME}_refs/。
  wrapper 结束后会在输出目录根部执行一次窄范围旧文件清理。
  触发场景：用户说"帮我下载这篇文献的参考文献"、"批量下载引用文献"、"把这篇论文的
  所有引用都下载下来"、或提供 PDF 路径/DOI 要求下载全部参考文献。
---

# Ref Downloader — 参考文献批量下载

推荐通过单入口 wrapper 使用；底层仍保留三脚本流水线，便于调试和增量重跑。

---

## 固定常量

每次执行时，以下路径固定不变：

```
PYTHON    = C:\Users\Link\AppData\Local\Programs\Python\Python311\python.exe
SKILL_DIR = C:\Users\Link\.agents\skills\ref-downloader
ZOTERO_DB = D:\Link\Documents\Zotero\zotero.sqlite
```

---

## 推荐入口

优先使用：

```bash
"{PYTHON}" "{SKILL_DIR}\run_ref_downloader.py" <DOI 或 PDF 路径>
```

可选参数：

```bash
"{PYTHON}" "{SKILL_DIR}\run_ref_downloader.py" <DOI 或 PDF 路径> --output-dir "E:\...\custom_refs"
```

wrapper 会负责：

- 解析 DOI（PDF 输入时先查 Zotero，再回退到 PDF 文本）
- 计算 `OUTPUT_DIR`
- 在 `OUTPUT_DIR` 里顺序运行三脚本
- 结束后只在 `OUTPUT_DIR` 根目录做一次窄范围清理

只有在你需要单独调试某一步时，才按下面的“三脚本手动流程”逐步执行。

---

## 完整执行流程（底层手动模式）

```
用户提供 PDF 路径 OR DOI 字符串
        │
        ▼
Step 1  解析输入 → 获取 DOI
        │
        ▼
Step 2  确认 DOI 正确 + Edge 已关闭
        │
        ▼
Step 3  确定 OUTPUT_DIR 和 PROJECT_NAME
        │
        ├─ refs_raw.json 不存在 ──▶ Step 4  extract_refs.py <DOI>
        │
        ▼
Step 5  validate_refs.py <PROJECT_NAME>
        │
        ├─ 有 unknown publisher ──▶ 更新 PUBLISHER_MAP ──▶ 重跑
        │
        ▼
Step 6  download_refs.py <PROJECT_NAME>
        │
        ▼
Step 7  展示 download_report.csv 摘要
        │
        ▼
Step 8  清理 OUTPUT_DIR 旧脚本
```

---

## Step 1：解析输入，获取 DOI

### 情况 A：用户直接给出 DOI
识别规则：输入以 `10.` 开头（如 `10.1021/jacs.5c05017`）。直接使用，跳到 Step 2。

### 情况 B：用户给出 PDF 文件路径
优先查 Zotero 数据库（速度快、元数据最准）：

```python
# 使用 PYTHON 执行以下代码（将 Zotero DB 复制到临时文件避免锁定）
import sqlite3, shutil, os, sys, tempfile, re

db_path = r"D:\Link\Documents\Zotero\zotero.sqlite"
pdf_path = sys.argv[1]  # 用户提供的 PDF 路径

tmp_db = tempfile.mktemp(suffix=".sqlite")
shutil.copy2(db_path, tmp_db)
try:
    conn = sqlite3.connect(tmp_db)
    basename = os.path.basename(pdf_path)
    row = conn.execute("""
        SELECT dv.value
        FROM itemData id
        JOIN fields f ON id.fieldID = f.fieldID
        JOIN itemDataValues dv ON id.valueID = dv.valueID
        WHERE f.fieldName = 'DOI'
          AND id.itemID IN (
              SELECT parentItemID FROM itemAttachments
              WHERE path LIKE ?
          )
        LIMIT 1
    """, (f"%{basename}%",)).fetchone()
    conn.close()
    print(row[0] if row else "")
finally:
    os.remove(tmp_db)
```

如果 Zotero 返回空，尝试从 PDF 文本提取：

```python
import fitz, re, sys
doc = fitz.open(sys.argv[1])
text = "".join(doc[i].get_text() for i in range(min(3, len(doc))))
m = re.search(r'10\.\d{4,9}/[^\s"<>]+', text)
print(m.group(0).rstrip(".,;)") if m else "")
```

如果两种方法都失败，停下来询问用户：
> "无法自动识别该 PDF 的 DOI，请手动提供（格式：10.xxxx/xxxxx）"

---

## Step 2：确认前置条件

在运行任何脚本前，向用户确认：

```
即将开始下载参考文献：
  DOI：<DOI>
  输出目录：<OUTPUT_DIR>（见 Step 3）

请确认：
1. 以上 DOI 是否正确？
2. Microsoft Edge 是否已完全关闭？（脚本需要独占 Edge 配置文件）
```

---

## Step 3：确定输出目录和项目名

```
情况 A：输入是 PDF 路径
  PDF 路径示例：
    E:\北大\...\Topic2 铜的沉积\Gordon 等 - 2015 - Trends in copper precursor...pdf

  OUTPUT_DIR = PDF 所在目录 + "/" + PDF 文件名（去掉 .pdf）+ "_refs"
    即：E:\北大\...\Topic2 铜的沉积\Gordon 等 - 2015 - Trends in copper precursor..._refs\

情况 B：输入是 DOI（没有原始 PDF 路径）
  OUTPUT_DIR 默认 = 当前工作目录 + "/" + PROJECT_NAME + "_refs"
    即：<cwd>\2.0261501jss_refs\
  也可以在 wrapper 里显式传 `--output-dir`

PROJECT_NAME = DOI 最后一个 "/" 之后的部分，特殊字符替换为 "_"
  即：2.0261501jss

项目数据最终存放在：OUTPUT_DIR\PROJECT_NAME\
  即：E:\...\Gordon 等 - 2015..._refs\2.0261501jss\
```

如果 `OUTPUT_DIR\PROJECT_NAME\refs_raw.json` 已存在，**跳过 Step 4**，直接从 Step 5 继续（增量模式）。

如果 OUTPUT_DIR 不存在，先创建：
```bash
mkdir "{OUTPUT_DIR}"
```

注意：
- `download_refs.py` 现在会把 run artifacts 固定写到 `OUTPUT_DIR\runs\`
- 但手动三步模式仍推荐先 `cd "{OUTPUT_DIR}"`，这样三脚本输出更一致、更不容易混淆

---

## Step 4：运行 extract_refs.py（提取 DOI 列表）

```bash
cd "{OUTPUT_DIR}"
"{PYTHON}" "{SKILL_DIR}\extract_refs.py" {DOI}
```

**预期输出**：`{PROJECT_NAME}/refs_raw.json` 创建成功，控制台显示参考文献总数。

**错误处理**：

| 错误 | 处理 |
|------|------|
| `DOI not found in Crossref` | DOI 可能有误，向用户确认 |
| `No references found` | Crossref 未收录该期刊参考列表，告知用户无法自动提取 |
| 网络超时 | 重试一次 |
| `Overwrite? [y/N]` 提示 | Step 3 已检测到已存在时跳过此步，此提示不应出现 |

---

## Step 5：运行 validate_refs.py（验证 DOI，分类出版商）

```bash
cd "{OUTPUT_DIR}"
"{PYTHON}" "{SKILL_DIR}\validate_refs.py" {PROJECT_NAME}
```

**预期输出**：`refs_validated.json` 创建成功，显示 `Verified: X / Failed: Y / No DOI: Z`。

### 自动更新 PUBLISHER_MAP

验证完成后，读取 `refs_validated.json`，检查 `publisher == "unknown"` 且有 DOI 的条目：

```python
import json, urllib.request, re

data = json.loads(open(r"{OUTPUT_DIR}\{PROJECT_NAME}\refs_validated.json").read())
unknowns = [r for r in data["references"] if r.get("publisher") == "unknown" and r.get("doi")]

# 提取唯一 DOI 前缀
prefixes = {}
for r in unknowns:
    prefix = r["doi"].split("/")[0]
    if prefix not in prefixes:
        prefixes[prefix] = r["doi"]

print(f"Unknown prefixes: {list(prefixes.keys())}")
```

如果有未知前缀，对每个前缀查询 Crossref 获取 publisher 名称：

```python
# 对 doi = prefixes[prefix] 查 Crossref
url = f"https://api.crossref.org/works/{urllib.request.quote(doi, safe='')}"
req = urllib.request.Request(url, headers={"User-Agent": "RefDownloader/1.0"})
with urllib.request.urlopen(req, timeout=15) as r:
    msg = json.loads(r.read())["message"]
    publisher_name = msg.get("publisher", "").lower()
    print(f"  {prefix} → {publisher_name}")
```

根据 publisher 名称判断映射值（参考下表），然后用 Read/Edit 工具更新 `SKILL_DIR/validate_refs.py` 中的 `PUBLISHER_MAP`：

| Publisher 名称包含 | 映射值 |
|-------------------|--------|
| aip, american institute of physics | aip |
| ieee | ieee |
| osa, optica | osa |
| royal society of chemistry, rsc | rsc |
| american physical society | aps |
| taylor & francis | tandfonline |
| elsevier | elsevier |
| wiley | wiley |
| springer, nature portfolio | springer/nature |

更新 `PUBLISHER_MAP` 后，**重跑 validate_refs.py**（增量模式，只重新分类 unknown 条目）：

```bash
cd "{OUTPUT_DIR}"
"{PYTHON}" "{SKILL_DIR}\validate_refs.py" {PROJECT_NAME}
```

同时，如果 download_refs.py 中对应出版商没有 `direct_pdf_url` 和 `PDF_SELECTORS` 条目，用 Edit 工具补充合理的默认值（用 `doi.org/{doi}` 做 article URL，用 `a:has-text("PDF")` 做选择器兜底）。

---

## Step 6：运行 download_refs.py（下载 PDF）

```bash
cd "{OUTPUT_DIR}"
"{PYTHON}" "{SKILL_DIR}\download_refs.py" {PROJECT_NAME}
```

默认推荐**交互模式**，不要先加 `--auto`。

`--auto` 标志仍可用：
- 跳过手动 Enter 确认
- challenge 等待使用 15 秒超时
- 更适合“先快速扫一遍看整体成功率”
- **不适合**作为需要你接管验证码/学校登录/热会话的主流程

当前 `download_refs.py` 的等待策略是：
- 交互模式：`CAPTCHA_WAIT = 10s`
- `--auto`：`AUTO_CAPTCHA_WAIT = 15s`

注意：
- 脚本会打开**真实的 Microsoft Edge 持久 profile**：`%LOCALAPPDATA%\Microsoft\Edge\User Data\Default`
- 当前默认**保留你平时 Edge profile 里的扩展**，不再默认禁用扩展；只有设置环境变量 `REF_DOWNLOADER_DISABLE_EXTENSIONS=1` 时才会回到旧的“禁扩展”模式
- 交互模式下，`manual_pending` 页面会保留并进入后续 retry loop。
- 当前实现还会在主循环中做“小队列即时 flush”：
  - `elsevier`：只要出现 `manual_pending`，就会尽快提示你立刻处理并重试，利用热会话
  - 第一篇 `Elsevier` challenge 解决后，后续一段时间内的 `Elsevier` 过渡态（如 `crasolve shell` / `viewer_capture_failed`）会尝试自动热重试一次，不再每篇都先弹提示
  - 其他出版商：积累到一个很小的队列上限后就会提示处理，避免几十个页面堆到最后
- 如果 Edge 会话在运行中意外关闭，脚本现在会自动重启一次持久会话，并只重试当前这篇，避免后续全部级联成 `BrowserContext.new_page ... has been closed`
- 如果某篇已经进入 PDF viewer，但自动保存还没接住，manual retry 现在会优先从**当前保留的 live page**继续抓，不再默认回到 article 页整篇重跑
- `--auto` 会跳过 retry loop，run 结束后浏览器上下文会关闭，所以更适合“纯自动跑一遍看结果”，不适合作为人工接管主流程。

**预期输出**：
- PDF 文件保存到 `OUTPUT_DIR\PROJECT_NAME\`
- 运行事件保存到 `OUTPUT_DIR\runs\<timestamp>-round-03\events.jsonl`
- graceful completion 时生成 / 刷新 `OUTPUT_DIR\PROJECT_NAME\download_report.csv`

**状态说明**：
- `downloaded (X KB)` — 新下载成功
- `already_exists` — 之前已下载，跳过
- `manual_pending` — 需要机构访问权限或验证码
- `failed (...)` — 自动下载失败
- `ignored` — 已知无法访问

报告中还会额外保留：
- `session_restarts` — 当前 ref 在运行中经历过几次自动会话恢复
- `session_last_error` — 最近一次触发会话恢复的原始浏览器错误

**重要现实约束**：
- `download_report.csv` 目前是在**运行正常结束时**统一写回根项目目录
- 如果你中途 `Ctrl+C`、强关终端、或运行异常中断，根目录里的旧 CSV 可能不会反映本轮最新状态
- 这种情况下，请以两个地方为准：
  - 最新 run 目录下的 `events.jsonl`
  - `OUTPUT_DIR\PROJECT_NAME\` 里已经真实落盘的文件

---

## Step 7：展示下载报告

优先顺序如下：

1. 如果本轮**正常结束**：
   读取 `OUTPUT_DIR\PROJECT_NAME\download_report.csv`，展示摘要
2. 如果本轮**中途中断**：
   不要盲信旧 `download_report.csv`
   应读取：
   - 最新 `OUTPUT_DIR\runs\<timestamp>-round-03\events.jsonl`
   - `OUTPUT_DIR\PROJECT_NAME\` 中已经存在的 PDF / SI 文件

正常结束时的摘要示例：

```
========== 下载报告 ==========
总参考文献：X 条
主文 PDF 成功：X 篇
主文 PDF 失败：X 篇（见下方列表）
需手动下载：X 篇
SI 文件成功：X 个
PDF 位置：{OUTPUT_DIR}\{PROJECT_NAME}\
==============================

未能自动下载（可尝试手动）：
  [7]  Wang2018_JPowerSources  https://doi.org/10.1016/j.jpowsour.2018.01.068
  ...
```

---

## Step 8：清理旧文件

如果你使用的是 `run_ref_downloader.py`，wrapper 会在结束后自动检查 OUTPUT_DIR（注意：是 `_refs` 根目录，不是 `PROJECT_NAME` 子目录）并执行一次**窄范围清理**：

```
要清理的文件模式（仅当存在时）：
  fetch_refs.py
  fetch_refs_playwright.py
  fetch_refs_v2.py
  *.log（最后修改时间超过 7 天的）
```

**注意**：
- 只清理 OUTPUT_DIR 目录本身，不递归进子目录
- 不删除 `.bak` 文件（可能是用户手动备份）
- 不删除 SKILL_DIR 中的任何文件
- 如果你是手动逐步运行三脚本，默认**不会**自动做这一步

---

## 出版商支持

`validate_refs.py` 中已内置以下 DOI 前缀：

| 前缀 | 出版商 | 典型期刊 |
|------|--------|---------|
| 10.1038 | nature | Nature, Nature Energy, Nature Catalysis... |
| 10.1021 | acs | JACS, ACS Catalysis, Nano Letters... |
| 10.1126 | science | Science, Science Advances |
| 10.1016 | elsevier | Journal of Power Sources, Thin Solid Films... |
| 10.1002 | wiley | Angewandte Chemie, Advanced Materials... |
| 10.1039 | rsc | Journal of Materials Chemistry... |
| 10.1007 | springer | Springer journals |
| 10.1073 | pnas | PNAS |
| 10.1149 | ecs | Journal of The Electrochemical Society |
| 10.1088 | iop | IOP journals |
| 10.1063 | aip | Applied Physics Letters, JAP |
| 10.1109 | ieee | IEEE conferences/journals |
| 10.1364 | osa | Optical Materials Express |
| 10.1103 | aps | Physical Review |
| 10.1080 | tandfonline | Taylor & Francis |
| 10.1143 | iop | Japanese Journal of Applied Physics (old) |
| 10.1147 | springer | IBM Journal of Research |
| 10.3938 | kps | Korean Physical Society |

新出版商前缀遇到时，按 Step 5 描述的流程自动更新。

### 下载策略分层

`download_refs.py` 中的运行时策略并不是所有出版商都一样，当前应按下面三层理解：

- `specialized`
  - `wiley`：先开 article page，再在页面上下文里抓 `pdfdirect`
  - `elsevier`：先走 article page，再把 `View PDF` 当成 popup/new-tab 路径处理；若已进入 viewer，会优先复用当前 live page 与 tokenized `main.pdf` 候选；利用热会话做即时/自动重试
  - `aip` / `avs`：先过“请稍候”加载页，再进入 click flow
- `generic fallback`
  - `acs`、`nature`、`science`、`rsc`、`springer`、`pnas`、`ieee`、`osa`、`kps`
  - 共用 `direct_pdf_url -> article_url -> PDF_SELECTORS -> viewer fetch` 的通用路径
- `weak support`
  - `aps`、`annualreviews`、`tandfonline`
  - 当前属于“已识别 publisher，但主要依赖 DOI/article 通用兜底”，不要把它们理解成和 `wiley` / `elsevier` 一样有专门下载链路
- `specialized but weakly validated`
  - `ecs` / `iop`
  - 已有专门的 barrier-aware 分流和 IOP-family 路由，但当前环境下仍容易先撞到 `Radware`，非 barrier selector 分支还不能算完全验收

补充说明：
- 当前最小验收环境是 headed Microsoft Edge；实测 `headless` 模式会让部分 `Wiley` / `ACS` SI 样本返回空结果。
- `Wiley` 主 PDF 的路径已经修正，但是否能自动成功仍受当次会话里的 challenge 状态影响。
- `Elsevier` 主 PDF 现在已具备较强的热会话自动化能力；但极少数条目仍可能停在 `manual_pending`，尤其是 `crasolve shell` 没完全转成 viewer 的时候。
- `Annual Reviews` 这类 `href="#"` 但实际通过 JS 打开 viewer/popup 的站点，当前已由通用 popup/viewer hotpath 覆盖，不再只依赖显式 `target="_blank"`。
- `Wiley` 的 `downloadSupplement` SI 路径已经纳入更长的 post-challenge 等待，但 SI 整体仍是当前系统最薄弱的一环。
- 使用真实 Edge 持久配置目录验证时，必须先把普通 `msedge.exe` 进程彻底关掉；否则 Playwright 可能因为 profile 被占用而直接启动失败。

因此，“支持某出版商”至少要区分两件事：
- `validate_refs.py` 能不能识别 publisher
- `download_refs.py` 有没有经过验证的专门下载策略

--- 

## 常见问题

| 现象 | 处理 |
|------|------|
| `No references found` | Crossref 未收录该出版商参考列表 |
| Edge 无法启动 | 确认 Edge 已完全关闭（含后台进程），重跑 Step 6 |
| 大量 `manual_pending` | VPN/校园网未连接，或该出版商需登录 |
| 根目录 `download_report.csv` 看起来没更新 | 如果本轮中断过，请改看最新 `runs/<timestamp>/events.jsonl` 和项目目录里真实落盘的文件 |
| `validated.json` 中 `failed` 多 | Crossref API 偶发故障，重跑 Step 5（自动跳过已验证） |
| PDF 用 Zotero 找不到 DOI | 尝试 fitz 提取，仍失败则询问用户 |
