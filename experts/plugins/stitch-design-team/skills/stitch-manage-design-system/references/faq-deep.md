# 管理 Stitch 项目设计系统：深度 FAQ

## Q1：遇到“把 screenId 直接当实例 id”怎样处理？

从 get_project.screenInstances 取 id/sourceScreen。处理后验证：selectedScreenInstances 不含 x/y/width/height。

## Q2：遇到“提交整个画布对象”怎样处理？

只传 id 与 sourceScreen。处理后验证：系统 assetId 来自 list_design_systems。

## Q3：遇到“把设计系统卡片当页面”怎样处理？

过滤 DESIGN_SYSTEM_INSTANCE。处理后验证：上传、创建、应用分别有状态，失败不串行继续。

## Q4：遇到“上传成功就称系统应用完成”怎样处理？

分别验证 create 和 apply。处理后验证：selectedScreenInstances 不含 x/y/width/height。

## Q5：遇到“本地 DESIGN.md 存在就省略全部 tokens”怎样处理？

只有已验证应用的远程系统才走独立系统通道。处理后验证：系统 assetId 来自 list_design_systems。

## Q6：多人或多平台交接怎样保持一致？

共享系统名称、主题、指定实例列表、仅查询/创建/应用模式；按角色分配素材、实现与验收。交接必须带selectedScreenInstances 不含 x/y/width/height的证据，以及已完成/待确认状态。不同平台的输出路径与版本分别记录，不能把一个平台成功外推到其他平台。

## Q7：素材含真实客户信息，或者工具缺失怎么办？

先输出本地草案与缺失清单，不运行依赖项。客户字段替换成明确的“演示门店/演示订单”；删除会话、cookie、签名 URL，截图中的个人信息也要脱敏。只检查与任务有关的文件；安装工具前说明具体依赖、范围和影响，已有批准有效。

## Q8：商用和品牌素材怎样处理？

本技能代码/文档遵循仓库 Apache-2.0 及 NOTICE；复制上游实现时保留所需版权声明。品牌字体、图像、截图内容及第三方依赖各自授权，不能由技能许可证推断其可商用；交付时列素材来源和未核验许可。此流程不会替用户作出法律授权结论。
