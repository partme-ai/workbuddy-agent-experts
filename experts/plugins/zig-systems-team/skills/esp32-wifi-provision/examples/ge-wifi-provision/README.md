# GE · wifi-provision（esp32-wifi-provision 黄金示例）

**徽章**：`B0 Build Verification Only`

## 与 SKILL.md 映射

- §Workflow: "Security 1 + SoftAP" → `WIFI_PROV_SECURITY_1` / `wifi_prov_scheme_softap`
- §Pitfalls: "NVS 持久化凭据" → `nvs_flash_init()` + 注释"运行时核验"
- §Pitfalls: "Production 禁 Security 0" → Security 1（PoP），不选 Security 0
- §References: security-scheme.md → Security 0/1/2 对比

## 验证

```bash
python3 -c "import json;json.load(open('ge-provision-state.json'))" && echo "JSON OK"
```
