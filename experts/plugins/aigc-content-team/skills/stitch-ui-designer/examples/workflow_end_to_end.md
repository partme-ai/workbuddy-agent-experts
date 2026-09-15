# End-to-End Workflow Example

## Scenario: Creating a Pet Adoption App

**User**: "Use Stitch to design a pet adoption app called 'PawPals'. Start with a warm, friendly home screen."

Illustrative tool transcript, not a recorded live run. Reuse an existing project when supplied; the IDs below illustrate returned values. This example assumes legacy tools without project-level design-system support, so it uses inline tokens. When `list_design_systems` is available, apply the requested system first and omit duplicate tokens from the generation prompt.

### Step 1: Initialize Project
*Orchestrator invokes MCP tool `create_project`*

**Agent Action**:
```json
{
  "name": "create_project",
  "arguments": {
    "title": "PawPals"
  }
}
```
**Result**: Project created. Resource name: `projects/123`.

**Agent Note**: Extract numeric project ID `123` for `generate_screen_from_text`.

### Step 2: Design Analysis
*Orchestrator invokes `stitch-ui-design-spec-generator`*

**Agent Action**:
```json
{
  "name": "stitch-ui-design-spec-generator",
  "arguments": {
    "request": "Pet adoption app, warm friendly style"
  }
}
```
**Result**:
```json
{
  "theme": "LIGHT",
  "primaryColor": "#FF9F43",
  "roundness": "HIGH",
  "font": "Nunito",
  "styleKeywords": ["Friendly", "Playful", "Clean"],
  "deviceType": "MOBILE"
}
```

### Step 3: Prompt Construction
*Orchestrator invokes `stitch-ui-prompt-architect`*

**Agent Action**:
```json
{
  "name": "stitch-ui-prompt-architect",
  "arguments": {
    "userRequest": "Home screen",
    "designSpec": {
      "theme": "LIGHT",
      "primaryColor": "#FF9F43",
      "roundness": "HIGH",
      "font": "Nunito",
      "styleKeywords": ["Friendly", "Playful", "Clean"],
      "deviceType": "MOBILE"
    }
  }
}
```
**Result**:

```text
[Context]
Mobile home screen for PawPals. Inline-token fallback: light theme, Nunito,
Warm Orange (#FF9F43) for primary actions, Soft Cream (#FFF8F0) background.
[Layout]
1. Header: PawPals brand and search.
2. Categories: Dogs, Cats and Birds in a horizontal strip.
3. Featured: Vertical pet-card list.
4. Bottom navigation: Home, Favorites, Messages, Profile.
[Components]
Search input labelled "Find your friend"; pet cards with photo, name and
"Adopt" action; labelled navigation items with Home active.
```

### Step 4: Generation
*Orchestrator invokes MCP tool `generate_screen_from_text`*

**Agent Action**:
```json
{
  "name": "generate_screen_from_text",
  "arguments": {
    "projectId": "123",
    "prompt": "[Context] Mobile PawPals home. Light theme, Nunito, Warm Orange (#FF9F43) primary actions, Soft Cream (#FFF8F0) background. [Layout] 1. Header and search. 2. Categories Dogs/Cats/Birds. 3. Featured pet-card list. 4. Bottom navigation. [Components] Search labelled Find your friend; photo/name/Adopt pet cards; Home, Favorites, Messages, Profile navigation.",
    "deviceType": "MOBILE"
  }
}
```

### Step 5: Retrieve the Generated Screen
*Orchestrator invokes MCP tool `list_screens`*

**Agent Action**:
```json
{
  "name": "list_screens",
  "arguments": {
    "projectId": "123"
  }
}
```

Then select a screen and invoke `get_screen` to retrieve the screenshot/HTML.
### Step 6: Presentation

Surface actual outputComponents descriptions/suggestions; save and inspect the returned screenshot and HTML, update metadata and report verified screen IDs. If generation or download fails, report that failure instead of using the illustrative values above.
