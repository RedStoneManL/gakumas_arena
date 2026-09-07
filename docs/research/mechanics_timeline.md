# 学マス master data：数据时效性与机制/评分变更时间线

> 目的：审计 `data/raw/gakumasu-diff`（vertesan/gakumasu-diff 的 git clone）相对真实游戏的**新鲜度**，并从全部 git 历史中提取**机制与评分规则随时间的变化**，据此给出通用引擎必须具备的扩展点清单。
> 生成工具：`tools/masterdata/history_diff.py`（见 §B.0）。审计日期：2026-09-07。
> 相关文档：`docs/research/data_sources.md`（数据源）、`docs/research/existing_engines.md`（现有模拟器）、`docs/ARCHITECTURE.md` §8。

---

## Part A — 数据新鲜度

### A.1 dump 现状

| 项目 | 值 |
|---|---|
| 仓库 | `vertesan/gakumasu-diff`，本地 clone 已 `--unshallow`，**249 个 commit**，2024-05-18 → 2026-09-04 |
| 最新 commit | `5b8969e` 2026-09-04 11:03:33 UTC（=JST 20:03）；同日还有 `855a24f` 02:03 UTC（=JST 11:03） |
| 提交者 | 全部为 `vts-server`（自动化账号），commit message 是 master DB 文件的 sha256，无人工描述 |
| `ForceAppVersion.yaml` | iOS / Android / DMM 均为 **3.3.0**（`PlatformType_Other` 仍是 1.10.1，为占位） |
| 表数量 | 286 个 YAML（初始 dump 195 → 现在 286；历史上删除过 9 个） |

### A.2 与真实游戏的对照

能核实到的官方/半官方事实（本环境的出口代理封锁了 `gakuen.idolmaster-official.jp`、`idolmaster-official.jp`、App Store、Google Play、X、seesaawiki、wikiwiki 等域名，只能通过搜索引擎摘要间接核实；下列结论已用多条独立搜索结果交叉确认）：

- **ver.3.3.0** 于 **2026-08-17 11:00 JST** 上线（内容之一：サポートイベントのスキルカードが強化済みで獲得可能、可在设置中开关）。搜索引擎摘要将其描述为「約 3 週間前」，与今天 2026-09-07 吻合。
- 搜索 `ver.3.3.1` / `ver.3.3.2` / `ver.3.4.0` 均无结果，说明截至 2026-09-07 **3.3.0 仍是最新版本**。
- 2026-08-26 16:40 JST 有一次「あさり先生のプロデュースゼミ」的紧急维护（修复メモリーアビリティ重复的 bug）；dump 同日 02:03 UTC 有 commit `10fd0cf`。
- 2026-09-04 11:00 JST 新剧情活动「さいごの文化祭」开始；dump 同日 02:03 UTC（=11:03 JST）即有 commit `855a24f`，20:03 JST 再次 commit。
- 第三方商店镜像（QooApp）曾记录 v3.2.3 更新于 2026-08-05；dump 的 `ForceAppVersion` 在 2026-08-10 变为 3.2.3、2026-08-21 变为 3.3.0，与「发布日 + 数日后强制更新」的官方惯例一致（官方 X 历史公告：ver.1.3.0 于 7/18 发布、7/22 强制更新；ver.1.4.0 于 8/28 发布、9/1 强制更新）。

**结论：dump 没有落后于线上。** 最新 commit 就是 2026-09-04 当天两次更新的 master data；`ForceAppVersion` 3.3.0 与线上最新版本一致。dump 的「滞后」上限就是 vts-server 的轮询周期（见 A.3），实际观测为**同一小时内**。

### A.3 vertesan/campus 的更新机制与节奏

- `vertesan/campus`（Go）是 `gakumasu-diff` 与 `gkms-webdata` 的后台 cronjob：用 Firebase 匿名认证登录游戏服务器、下载加密的 master DB（MasterMemory/MessagePack）与混淆的 AssetBundle，解密后把每张表写成一个 YAML 文件，再由 `push_master.sh` 推送到 gakumasu-diff。仓库含 `cronjob.sh`、Docker 封装。
- 观测到的节奏（249 commits / 840 天 ≈ **每 3.4 天一次**，每月 4–13 次）。commit 的 UTC 小时分布高度集中在 02 时（=JST 11 时，学マス的常规更新时刻）与 06–11 时之间，说明 cron 以小时级轮询、只有 master 变化时才 commit。
- 最长间隔 **13 天**（2026-01-27 → 02-09），其余均 ≤12 天；从未出现「几周没更新」的情况，因此不存在系统性滞后。
- 每次 commit 改动 25–130 个文件；**改动文件 ≥ 100 的 commit 与大版本对应**：2024-11-16 `cda4882`（1.5.0）、2024-12-20 `4bad77b`（1.6.x）、2024-12-26 `cb5768d`（1.7.0 / N.I.A）、2025-05-16 `be4e3b4`（2.0.0）、2025-12-26 `6edc27e`（2.7.0 / レジェンド）、2026-05-16 `f0dac51`（3.0.2 / H.I.F）。
- 一个可直接用作「版本↔日期」映射的副产品：`ForceAppVersion.yaml` 自 2024-12-20 出现以来每次变化都对应一次强制更新（见 §B.3.0 的版本表）。

### A.4 对引擎的含义

- 每次同步 dump 后先跑 `history_diff.py HEAD@{1} HEAD`，把「新表 / 新枚举值 / 配置行变化」作为**升级信号**；不要假设 master data 只是「加卡」。
- 机制变化和版本号并不总是同步：2025-10-31 的最終試験スコア上限属于**代码侧**改动，`ResultGradePattern` / `ProduceGrade` 表当天没有任何变化（见 §B.3）。因此引擎的评分规则需要带 `effective_from` 日期、而非只跟 dump commit 走。

