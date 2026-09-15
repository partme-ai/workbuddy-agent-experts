# White-model → final video handoff prompt

Draft the downstream prompt from this template once the previs package is approved.
Fill every `<…>` from the previs map and shot table; do not invent roles or retimings.
The downstream consumer is `dreamina-3d-from-blender` or
`dreamina-video-production` (Seedance / Dreamina). Chinese is the primary prompt
language for Seedance; keep the English version alongside for review.

## Template (zh)

```text
【白模 → 真实资产映射】
<逐条列出，例如：>
浅青色长方体 = 女主
深灰色长方体 = 三名特工
红色圆柱体 = 火箭
白色长方体 = 赛车
青绿色长方体 = 列车

【严格参考白模视频】
严格参考白模视频中的摄影机运动、景别、切镜时间、人物整体位置和空间关系。

【几何体语义限定】
几何体只代表人物的位置和移动方向，不代表真实肢体动作；
人物按语义自然表演，角色外观以附加的角色资产图为准。

【资产与风格】
角色/道具资产图：<逐角色列出 assetImageRef>
场景/风格参考：<场景与风格描述或参考图>

【逐镜说明】
<逐镜：镜号（沿用 shotId，不改编号）、时长（帧数/秒）、景别、
该镜中每个角色的位置与运动意图、该镜的动作要点。>
```

## Template (en, for review parity)

```text
[White-model → real asset mapping]
List every placeholder explicitly, e.g.:
light-cyan cube = heroine; dark-gray cubes = three agents;
red cylinder = rocket; white box = car; teal long box = train.

[Strictly follow the previs video]
Follow the reference video's camera movement, shot sizes, cut timings,
overall subject positions, and spatial relationships exactly.

[Geometry semantics]
The placeholder geometry encodes position and direction of movement only —
never real limb motion. Characters perform naturally per the scene semantics;
final appearance follows the attached character asset sheets.

[Assets and style]
Character/prop sheets: <assetImageRef per role>.
Scene/style reference: <description or reference images>.

[Per-shot notes]
One block per shot, reusing the original shotId and timing: shot size,
per-subject position and motion intent, and the action beat.
```

## Rules for filling it

- The mapping list must match `previs-map.schema.json` `cast` one-to-one — every
  placeholder color and shape appears exactly once, in the same words the video shows.
- Cut timings in the per-shot notes must equal the shot table's frame ranges.
- Attach the previs video itself as the reference; the prompt constrains, the video
  anchors. Never describe camera moves in words where the video already shows them.
- `encoding.doesNotEncode` is mandatory context: the generator must be told the
  geometry is not a performance reference, or it will imitate stiff box-people.
