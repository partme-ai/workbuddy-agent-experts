# Third-Party Notices

This repository does not bundle third-party application binaries, proprietary SDKs, credentials, or generated media. The plugin's own scripts use the Python standard library only.

The data/style-library.json template metadata is redistributed from
https://github.com/freestylefly/awesome-gpt-image-2 at commit
0dc09c46c8a30b1fdd89c18cc78a894dac2104e3 under MIT.
Copyright (c) 2026 freestylefly. The complete license is retained in
licenses/freestylefly-MIT.txt. JSON whitespace was normalized; template fields
were retained. Preview images are not bundled.

data/gallery-index.txt is the unmodified gallery routing index from
https://github.com/wuyoscar/GPT-Image2-Skill at
05cb1130bba29e0fc028220376280a2e934a8041; see licenses/wuyoscar-MIT.txt.
data/prompt-categories.json is the unmodified category manifest from
https://github.com/YouMind-OpenLab/ai-image-prompts-skill at
6e8339bbfda7ed3f21978df84f266f1c393f5918; see licenses/youmind-MIT.txt.

Original, inactive upstream snapshots are preserved under `vendor/upstream/`:

- freestylefly/awesome-gpt-image-2: its complete
  `gpt-image-2-style-library` Skill at the pinned commit above, MIT.
- wuyoscar/GPT-Image2-Skill: its complete `gpt-image` and
  `get-prompt-from-image` Skill directories at the pinned commit above, MIT.
- YouMind-OpenLab/ai-image-prompts-skill: its complete Skill entrypoint,
  scripts and prompt references at the pinned commit above, MIT.
- YouMind-OpenLab/awesome-gpt-image-2: README and license only at commit
  7516ce0d3132231e0de80f8a7978bc6ed728abe5, CC BY 4.0.

These snapshots are source material, not active plugin Skills. The plugin never
executes their installers, API clients, automatic updates or embedded tool
instructions. Preview images from the large galleries are not bundled, except
for the single example asset already contained in freestylefly's original Skill.

songguoxs/gpt4o-image-prompts and dongyubin/Awesome-AI-Images-Prompts did not
declare a license at the inspected revisions. Their repository and commit
pointers remain in `vendor/upstream/sources.json`; their content is not bundled.
Their recorded license status applies to the inspected repository revision;
it does not certify rights to third-party images or community contributions.

Referenced product names identify interoperability targets rather than bundled components. Codex is developed by OpenAI and is distributed under the Apache License 2.0; the plugin invokes a Codex installation that the user already has and does not redistribute it. OpenAI, ChatGPT, Codex, and GPT Image are trademarks of their respective owners.

The image generation model used for a batch is selected by Codex itself, not by this plugin. This repository records nothing about that model beyond what Codex reports, and it makes no claim about which model or tier an account will resolve to.
