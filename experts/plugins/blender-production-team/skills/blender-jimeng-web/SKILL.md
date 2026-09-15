---
name: blender-jimeng-web
description: "Use an already enabled official Jimeng Blender uploader to render or select a local video and create a Jimeng Web handoff link."
---

# Official Jimeng Web Handoff

Use this Skill only when the user explicitly asks to upload/open a Blender
preview in Jimeng Web or use the official uploader. It delegates to the user's
installed add-on; this plugin does not bundle, install, enable, or reproduce
the uploader.

## 能力边界说明

### ✅ 能做

- 检查前台 Blender Connector 中是否已启用官方上传插件。
- 调用官方 `render_upload` 完成相机渲染并生成 Web 交接链接。
- 调用官方 `upload_existing` 将已有本地视频交接到即梦网页。
- 查询链接状态，并在用户明确要求时打开当前链接。

### ⚠ 需要用户准备

- Blender 必须处于前台 Connector 模式并由用户主动授权连接。
- 官方 `jimeng_blender_uploader` 必须由用户自行安装并启用。
- 相机、帧范围、输出目录或已有视频路径必须明确。

### ❌ 超出范围

- 不安装、复制、启用或修改官方插件。
- 不持久化本地 Bridge token、`thirdparty_id`、Cookie 或账号凭据。
- 不把网页链接就绪描述为 Seedance 生成完成。
- 不在失败或超时后自动再次渲染或上传。

## Workflow

1. Call `official_uploader.inspect`. If unavailable, stop with official
   installation guidance; do not mutate Blender.
   This command exists only in a foreground Connector session; managed and
   background sessions must report the route as unavailable.
2. For camera intent, collect the approved camera, resolution, frame range,
   output directory under the Connector's approved output root and prompt,
   then call
   `official_uploader.render_and_link` exactly once.
3. For an existing video, require a regular non-symlink file under an approved
   asset root, then call `official_uploader.link_existing` exactly once.
4. Call `official_uploader.status`. Report only the redacted origin and state.
5. Completion is `JimengLinkReady`. This does not mean Seedance Completed.
6. Call `official_uploader.open_link` only when the user explicitly asks to
   open the link; browser opening is a separate gated action.

## Privacy and safety

Treat scene paths, prompts, video paths and account context as private user
data. Keep them out of durable audit text where a hash or status is enough.
Never expose the loopback resource URL or its token. The official add-on owns
the Bridge lifetime and web protocol.

Durable audit output may contain only command, request ID, result status,
official task state, link origin, input SHA-256, and error category. It must
never contain raw prompt, input/output path, redirect URL, loopback token, or
`thirdparty_id`.
