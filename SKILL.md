# YouTube 播客归档到 second-brain

把一个 YouTube 访谈播客做成长期归档线：先建档首批，再挂每日 cron 增量续更。每期成品是四件套（shownotes 节目说明、英文转写、中文译稿、中文总结），只进私有仓 second-brain，音频和过程文件只留本地。仓库结构、索引水位线和推送核验的通用规矩同时看 `local_second_brain_archive` skill，本 skill 只管视频播客这条管线。

## 先出方案，等用户拍板

- 收到链接先只做识别，不动手。用 `~/workspace/venvs/yt/bin/yt-dlp --skip-download` 拉单集和频道元数据，查清频道名、频道 ID、主持人、订阅量、更新节奏和这一集的嘉宾、标题、时长、发布日期。

- 找出这个节目的权威清单，一般是官方播客播放列表。频道里与当前节目线无关的老视频（比如早年的其他主题内容）在方案里明确划出去，不回补。

- 把方案一句话给用户拍板，包含四件事：仓库位置（分类层由用户定，比如 Podcast 层还是新建 Youtube 层，不要自己类推）、首批期数、日更 cron 时间、收录范围下限日期。

- 用户拍板后才建目录、写 README、动手下载。仓库写入属于不可逆动作，不抢跑。

## 建档与索引

- 仓库位置：`70 Distillation/<分类层>/<节目名>/`，节目目录下按发布年月分 `YYYY-MM/` 子目录，每期一个 `<YYYY-MM-DD>-<嘉宾小写连字符 slug>/` 目录。

- 每层都放一个 `README.md`，避免 GitHub 网页把单链目录折叠显示。

- 节目 `README.md` 必须含三样东西：索引表（新行加在最上面，含发布日期、标题、嘉宾、时长和四件套相对链接）、归档水位线一行、已归档视频 ID 全集一行。判新集只认这三处，不靠记忆。

- 本地工作区：`~/workspace/podcasts/<节目 slug>/<YYYY-MM-DD>-<嘉宾 slug>/`，放音频和全部成品、过程文件。仓库只收成品 MD。

## 判新集

- 用 `yt-dlp --skip-download --flat-playlist` 拉播客播放列表和频道 /videos 页，合并候选，再逐条用单视频元数据核实 upload_date、标题和时长，不信 flat 列表的日期。

- 候选条件三条同时满足：视频 ID 不在已归档全集内、属于节目播放列表（或标题与嘉宾形态明确是长访谈）、upload_date 不早于建档时定的收录下限。预约首播（未正式发布）的不处理，留给后续日更。

- 拉取撞 429 时改走 android 客户端路线、串行慢拉，不硬闯，撞限流就停手等下一次。

## 下载与英文转写

- 下载音频用 `yt-dlp -f "bestaudio[ext=m4a]/bestaudio"`，存为该期目录下的 `audio.m4a`。

- 转写管线：分片转写脚本用本 skill 自带的 `scripts/transcribe_chunk.py`（`~/workspace/venvs/yt/bin/python` 加 faster-whisper small 本地缓存模型，cpu int8，language=en，vad_filter=True）。逐期驱动脚本和成品组装脚本按 `~/workspace/podcasts/silicon-valley-girl/tools/` 下的 `run_transcribe.sh`、`build_transcripts.py` 照抄改路径和节目名。

- 跑转写前把 `no_proxy` 和 `NO_PROXY` 清成 `localhost,127.0.0.1`，并设 `HF_HUB_OFFLINE=1`。本机的 IPv6 括号写法会让请求库解析崩溃，这一步不能省。

- 音频解码走 ffmpeg 转 f32le 16k 单声道 raw，再用 numpy 喂模型，不要用 faster-whisper 自带的 decode_audio。

- 必须按 300 秒切片、逐片单独进程转写、分段即时落盘到 `segments.jsonl`，支持断点续跑，禁止整文件单跑。本机只有 2 核约 7GB 内存，整跑会被运行时重启打断。长任务挂 systemd 服务跑，完成后 disable 并删 unit。

- 断点续跑后检查末片重叠段并去重。全部转完检查全文有无大于 12 秒的内部空白（VAD 漏检），有就对该时间段用无 VAD 模式补转并入。

- 产物两个：`transcript.txt`（每行 `[MM:SS] 英文`）和 `transcript.md`（带标题和机器转写未人工校对的说明，正文 `**[MM:SS]** 英文`）。频道自带字幕轨即使存在也不替代本地转写，口径统一。

## 中文翻译与总结

- 把 `transcript.txt` 全文逐行翻译成中文，产出 `transcript_zh.txt` 和 `transcript_zh.md`，格式与英文稿镜像。行数与时间戳必须与英文稿逐行一致，译完用脚本核验行数相等、时间戳不符为 0 处，再抽查头、中、尾三处通顺。

- 翻译要求：不摘要、不跳段，广告段照常翻译。人名、公司、产品名保留英文。明显的 Whisper 转写错误按上下文修正语义，不要直译错词。实在无法还原的转写噪声保留直译并在交付时如实提醒用户以原视频为准，不猜。

- 中文总结 `summary_zh.md` 只基于中文译稿提炼，不编造观点和数字。头部注明嘉宾、主持、时长和「基于中文译稿提炼、数字均为节目中口径」。正文含一句话核心、按主题或章节的要点、值得留存的判断与数据锚点，关键数字注明是节目中谁的口径。

- `shownotes.md` 写标题、嘉宾（姓名加身份）、发布时间、时长、视频 ID、原视频链接、章节（取自视频简介的 Timestamps）和本期文件清单，并注明音频仅存本地。

## 入仓与核验

- 进仓库的只有四个文件：`shownotes.md`、`transcript.md`、`transcript_zh.md`、`summary_zh.md`。音频、txt、segments 和脚本一律不进仓库。

- 提交前先 `source ~/.github/token.env` 再 `git pull --ff-only`。工作区有其他任务的未提交改动时不要动、不要顺手提交。

- 更新节目 `README.md` 的索引表、水位线和已归档 ID 全集，三处与新一期对齐。

- 提交信息用「<分类层>/<节目名>：归档 <YYYY-MM-DD> <标题简写>（YYYY-MM）」。推送后用 `gh api repos/aiedwardai/second-brain/contents/...` 核验该期四个文件都在且大小与本地逐一一致，核验不过要在汇报里明说。

- 合并生成成品并核验无误后，立即删该期的过程文件（`segments.jsonl`、临时脚本），本地只留成品文件和音频。

## 挂日更 cron 并守汇报规矩

- 建 cron `<节目 slug>-daily-archive`，每天一个 :38 分的错峰空位（先查现有 cron 占用再选），owner 设为 `goal:second-brain`，任务体写全本 skill 的判新集、单期处理、入仓核验全流程和汇报规矩。

- 日更只在两种情况给用户发消息：新集归档推送成功时一句话白话汇报（哪一期、嘉宾或标题、已归档），失败时一句话说清卡在哪、要不要用户做什么，不贴日志。推送失败只报一次。

- 无新集静默结束，不提交、不发消息。

## Available connectors

- [GitHub（本机 token）](~/workspace/custom-connectors/custom.legacy-github/CONNECTOR.md) for 私有仓 second-brain 的推送与 API 核验，凭据走 `~/.github/token.env`，不进 skill 和聊天记录。

- Use `muse.connector_search` to find other connectors and `muse.skill_search` to find related skills.

- If nothing here fits, look on the web for a maintained API or MCP server and set it up with [Custom Connectors and MCPs](/opt/muse/skills/custom-connector-setup/SKILL.md), or build a custom connector.

## Websites

- [YouTube](https://www.youtube.com/) for 节目识别与元数据核实，一律走本机 `yt-dlp` 拉取，不用浏览器打开视频页判断。

## Alternatives for better results

- 节目更新很慢（月更或不定期）时，把日更 cron 换成用户点名时手动跑一期，省得每天空转。

- 用户只要单期不要整条线时，跳过建档和 cron，只做这一期的四件套发给用户看，不入仓。
