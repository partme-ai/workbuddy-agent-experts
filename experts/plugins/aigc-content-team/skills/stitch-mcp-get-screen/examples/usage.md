# Usage Example

## 1. Get Screen Details (Export Code)

**User Input:**
> "Give me the code for the login screen we just made."

**Agent Action:**
```json
{
  "name": "get_screen",
  "arguments": {"name": "projects/3780309359108792857/screens/88805318abe84d16add098fae3add91e"}
}
```

**Output:**
```json
{
  "name": "projects/.../screens/...",
  "htmlCode": {
    "downloadUrl": "https://stitch.google.com/download/html/..."
  },
  "screenshot": {
    "downloadUrl": "https://stitch.google.com/download/image/..."
  },
  "figmaExport": {
    "downloadUrl": "https://stitch.google.com/download/figma/..."
  }
}
```

## 2. Note on IDs
*   **name**: Must be the full string `projects/{project}/screens/{screen}`.
