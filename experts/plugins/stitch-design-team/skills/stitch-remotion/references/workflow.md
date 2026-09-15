此文保留上游扩展流程及代码示例，属于按需参考。先读 [中文入口](../SKILL.md) 的范围、权限、来源和验证约束。历史工具名与参数必须以实际连接的 schema 和目标依赖版本核对；英文示例为结构演示，不是业务事实或已经执行的结果。

# Stitch to Remotion Walkthrough Videos

**Constraint**: Only use this skill when the user explicitly mentions "Stitch" and walkthrough video or Remotion.

You are a **video production specialist** creating walkthrough videos from Stitch app designs. Combine Stitch MCP (or **stitch-mcp-list-projects**, **stitch-mcp-list-screens**, **stitch-mcp-get-screen**) to get screens with Remotion for programmatic video: transitions, zoom, text overlays.

## Prerequisites

- Stitch MCP Server (https://stitch.withgoogle.com/docs/mcp/guide/)
- Remotion MCP or Remotion CLI; Node.js and npm
- A Stitch project with designed screens

## Retrieval and Networking

1. **Discover prefixes**: Run `list_tools` for Stitch and Remotion MCP prefixes.
2. **Project/screen lookup**: Use `[stitch_prefix]:list_projects` (filter view=owned), then `[stitch_prefix]:list_screens` with projectId; identify screens for the walkthrough.
3. **Screen metadata**: For each screen call `[stitch_prefix]:get_screen`; get `screenshot.downloadUrl`, `htmlCode.downloadUrl`, width, height, title, description.
4. **Asset download**: Do not assume local HTML or screenshots exist. Download the returned screenshot URLs with [scripts/download-stitch-asset.sh](../scripts/download-stitch-asset.sh); save to `video/public/assets/screens/{screen-name}.png` in walkthrough order. Run the script with Bash, HTTPS URL and output path; it requires curl/mktemp, stages atomically, bounds the transfer, and preserves existing output on failure. Keep signed URLs private; refresh expired URLs through `get_screen`.
5. **Manifest**: Create `screens.json` with projectName, screens array (id, title, description, imagePath, width, height, duration).

## Video Composition Strategy

- **ScreenSlide.tsx**: Single screen (imageSrc, title, description, width, height); zoom/fade; configurable duration (e.g. 3–5 s).
- **WalkthroughComposition.tsx**: Sequence of ScreenSlides; transitions (fade/slide from `@remotion/transitions`); text overlays.
- **Config**: Frame rate (e.g. 30 fps), dimensions (match Stitch or scale), total duration.

Use Remotion `spring()` for zoom; use `@remotion/transitions` (fade, slide) between screens.

### Common Patterns (align with official)

- **Simple slide show**: 3–5 s per screen, cross-fade, bottom text overlay (screen title), progress bar at top.
- **Feature highlight**: Zoom into regions; animated circles/arrows; slow-motion on key interactions; before/after comparisons.
- **User flow**: Sequential screens with directional slides; numbered steps overlay; highlight actions (clicks, taps); connect screens with animated paths.

### Optional: Voiceover and dynamic text

- **Voiceover**: Generate script from screen descriptions; use TTS or recorded audio; sync screen timing with narration.
- **Dynamic text**: Download `htmlCode.downloadUrl` per screen; parse HTML for headings/buttons/labels; generate timed callouts in the composition.

## Execution Steps

1. **Gather assets**: List Stitch project → list screens → get_screen for each → download screenshots → build screens.json.
2. **Remotion setup**: Use existing Remotion project or `npm create video@latest -- --blank` in e.g. `video/`; install `@remotion/transitions` etc.
3. **Build components**: Copy [screen-slide-template.tsx](../resources/screen-slide-template.tsx) to `video/src/ScreenSlide.tsx` and [WalkthroughComposition.tsx](../examples/WalkthroughComposition.tsx) to `video/src/WalkthroughComposition.tsx`; put the manifest at `video/screens.json`. Register `RemotionRoot` through the project's `registerRoot` entry. Keep Remotion package versions aligned. TransitionSeries transitions are siblings between sequences with `linearTiming`, and total duration subtracts overlapping transition frames. The 20-frame example requires every scene to exceed 20 frames; zoom happens inside ScreenSlide, while transitionType zoom falls back to fade.
4. **Preview**: `npm run dev` in video/; adjust timing and transitions.
5. **Render**: `npx remotion render WalkthroughComposition output.mp4` (or use Remotion MCP if available).
6. **Verify**: Follow [composition-checklist.md](../resources/composition-checklist.md). Check each actual asset, aspect ratio, text contrast/captions, narration pacing and first/transition/final frames. At 30 fps, two 4-second screens with one 20-frame transition yield 220 frames. CLI exit success alone is not visual acceptance; report render path, frames and checks actually performed.

## Integration with This Repo

- **Stitch screens**: Use **stitch-mcp-list-projects**, **stitch-mcp-list-screens**, **stitch-mcp-get-screen** to resolve projectId/screenId and get download URLs.
- **Design consistency**: If DESIGN.md exists (from **stitch-design-md**), use screen titles/descriptions for overlay text.

## File Structure

```
project/
├── video/
│   ├── src/
│   │   ├── WalkthroughComposition.tsx
│   │   ├── ScreenSlide.tsx
│   │   └── Root.tsx
│   ├── public/assets/screens/   # Stitch screenshots
│   ├── remotion.config.ts
│   └── package.json
├── screens.json                 # Screen manifest
└── output.mp4
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Blurry screenshots | Use full-resolution screenshot URLs |
| Misaligned text | Match composition size to screen dimensions |
| Choppy animations | Increase fps; tune spring damping |
| Build fails | Check Node/Remotion version; install deps |

## Keywords

**English:** Stitch, Remotion, walkthrough, video, screenshots, transitions.
**中文关键词：** Stitch、Remotion、走查视频、转场。

## References

- [Remotion docs](https://www.remotion.dev/docs/)
- [Remotion transitions](https://www.remotion.dev/docs/transitions)
- [Remotion Skills](https://github.com/remotion-dev/remotion/tree/main/packages/skills) — animation, composition patterns, performance; install with `npx skills add remotion-dev/skills`.
- [Remotion MCP](https://www.remotion.dev/docs/ai/mcp) — programmatic render and preview.
- [Stitch MCP](https://stitch.withgoogle.com/docs/mcp/guide/)
- [Examples](../examples/usage.md)
- [Screens Manifest Example](../examples/screens.json)
- Bundled templates and checklist above are adapted from [google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills/tree/0337446dadde6f8c94210444e2aa9d546126480f/plugins/stitch-build/skills/remotion).
- [TransitionSeries contract](https://www.remotion.dev/docs/transitions/transitionseries) — sibling transitions and overlap duration; check installed version before rendering.
