# 上传本地资产到 Stitch：本地应用验证

所有标识和内容均为离线测试 fixture。以下先验证请求构造和响应处理，不调用 HTTP，不把请求草案当作远程回执。

## 快速开始：HTML 请求与结果

输入：“把下面的演示预约页上传到已指定项目 123，页面标题 /orders，生产者 stitch-extract-static-html；本次只核对请求，不执行上传。”

```html
<main><h1>预约列表</h1><p>暂无预约</p></main>
```

预期的单项请求（HTML 对应 htmlCode、text/html 和 DOCUMENT）：

```json
{
  "screen": {
    "htmlCode": {
      "fileContentBase64": "PG1haW4+PGgxPumihOe6puWIl+ihqDwvaDE+PHA+5pqC5peg6aKE57qmPC9wPjwvbWFpbj4=",
      "mimeType": "text/html"
    },
    "screenType": "DOCUMENT",
    "isCreatedByClient": true,
    "generatedBy": "stitch-extract-static-html",
    "title": "/orders"
  }
}
```

上面的 base64 是公开演示输入的精确编码，只为说明内存请求结构；真实运行不应将文件正文或其编码写入日志。实际脚本将该请求放入 requests，parent 为 projects/123，CLI 的 createScreenInstances 为 true。

可从仓库根执行的本地构造校验：

```python
import base64
import importlib.util
from pathlib import Path

path = Path("skills/stitch-upload-to-stitch/scripts/upload_to_stitch.py")
spec = importlib.util.spec_from_file_location("stitch_upload", path)
upload = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upload)
html = "<main><h1>预约列表</h1><p>暂无预约</p></main>"
request = upload.build_screen_request(
    "text/html", base64.b64encode(html.encode()).decode(),
    title="/orders", generated_by="stitch-extract-static-html",
)
assert request["screen"]["htmlCode"]["mimeType"] == "text/html"
assert base64.b64decode(request["screen"]["htmlCode"]["fileContentBase64"]).decode() == html
assert request["screen"]["screenType"] == "DOCUMENT"
print("HTML 请求构造通过；远程未执行")
```

本次交付：“/orders 的 HTML 请求已本地验证；未发送请求，screenId 和 screenInstance 尚未取得。”只有收到并校验真实响应后，CLI 才能打印标识摘要。例如下列是**模拟回执的预期摘要**：

```json
{
  "screens": [{"name": "projects/123/screens/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}]
}
```

验证：标识必须是格式合法的字符串、属于目标项目，实例 sourceScreen 必须关联本响应的 screen；额外私密字段不输出。

## 典型场景：Markdown

输入：“上传内容为 x 的演示 DESIGN.md，仅检查类型映射，不调用网络。”

预期：build_screen_request("text/markdown", "eA==") 的 htmlCode.mimeType 为 text/markdown，screenType 为 DOCUMENT，generatedBy 默认 UserUploadedDesignMd。输出“Markdown 请求已构造；尚未上传，尚未创建项目系统”。创建系统是后续管理流程，不能由请求构造或文档上传推断已完成。

## 高级场景：图片与生产者

输入：“上传演示 PNG，title 为预约原型，generated-by 传入 demo-import；只做离线检查。”

预期：PNG 放入 screenshot 且 mimeType 为 image/png、screenType 为 IMAGE、title 为预约原型。CLI 提示 generated-by 对图片忽略，不把它写到图片请求。返回标识仍经过相同结构检查。

## 异常处理：缺项目或坏响应

输入：“上传预约页，但没有 projectId。”

本地草案：“文件类型 text/html，拟用标题 /orders；请求尚未发送。需要补充真实 projectId，以确定上传归属；环境中的 STITCH_API_KEY 仅由运行环境读取。”

收到 {}、[]、空 `results`、缺失 `results[].screen` 或对象型 name 时，输出“上传结果未知：响应标识缺失或结构异常，请先对账，勿重复提交”。不打印异常字段值，不返回空成功摘要，不重发。先读 get_project、list_screens、get_screen；无候选时记录最后一项无法执行的原因。

## 避免误触发与验证

输入：“把现有设计系统应用到两张屏幕。”

输出：“使用 stitch-manage-design-system，交接真实系统与屏幕实例；本上传入口不重复上传文件。”

本地测试入口：python3 -m unittest discover -s skills/stitch-upload-to-stitch/tests -v。该测试覆盖请求构造、响应结构和隐私，不证明真实服务已经接受上传。
