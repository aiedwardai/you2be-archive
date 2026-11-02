# you2be-archive

把一个 YouTube 访谈播客持续归档进私有仓 second-brain 的 skill：判新集、下载音频、300 秒分片 faster-whisper 转写、逐行中译并核验对齐、中文总结、四件套入仓并用 GitHub API 核验，最后挂每日 :38 错峰 cron 增量续更，无新集静默。

由 Silicon Valley Girl（主持 Marina Mogilko）归档线实操整理，2026-10-30 至 11-01 已跑通首批 3 期加日更 1 期。

## 内容

- `SKILL.md`：完整流程（先出方案等拍板、建档索引与水位线、判新集、转写硬规矩、翻译与总结口径、入仓核验、日更汇报规矩）
- `skill.yaml`：skill 描述
- `scripts/transcribe_chunk.py`：单片 300 秒转写脚本（ffmpeg 解码 f32le 16k 单声道 raw 加 numpy 喂模型，cpu int8，vad_filter=True，支持断点续跑落盘）

## 使用

把本目录放进你的 agent 的 custom-skills 目录即可。触发语：「归档这个主播」「归档这个播客」。
