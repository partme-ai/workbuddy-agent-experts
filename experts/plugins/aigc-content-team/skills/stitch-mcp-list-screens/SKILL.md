---
name: stitch-mcp-list-screens
license: Apache-2.0
description: Lists all screens contained within a specific project.
---
# List Screens

**CRITICAL PREREQUISITE:**
**You must ONLY use this skill when the user EXPLICITLY mentions "Stitch".**

Lists all screens contained within a specific project.

## Use Case
Invoke this skill to browse the history of generated designs in a project or to find a specific screen to reference or iterate upon.

## Input Parameters

The skill expects you to extract the following information from the user request:
*   `projectId` (required): Bare project ID string, for example `123456`; never add the `projects/` prefix.

## Output Schema

Returns an object with `screens` array:
*   **`screens`**:
    *   `name`: Resource identifier (e.g., `projects/123/screens/abc`).
    *   `title`: Auto-generated title.
    *   `screenshot`: Thumbnail URL.
    *   `deviceType`: The device type of the screen.

## Usage Example

User Input: "Show me all screens in this project."

Agent Action:
1.  Extract project ID.
2.  Call `list_screens` with the bare ID: `{"projectId": "123456"}`.

## References

- [Examples](examples/usage.md)

