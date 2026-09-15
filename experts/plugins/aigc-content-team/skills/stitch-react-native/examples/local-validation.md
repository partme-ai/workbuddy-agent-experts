# Stitch 转 React Native：本地应用验证

以下是完整的中文请求与预期响应契约，使用演示资料；不是远程执行记录。不调用 Stitch 写操作即可检索、模拟应用并审阅结果。

## 快速开始

输入：“将门店预约稿转 iOS/Android 表单。只用演示素材，先返回本地结果与验证范围。”

输出：输入 <button>确认预约</button> → <Pressable accessibilityRole="button" accessibilityLabel="确认预约"><Text>确认预约</Text></Pressable>；事件由目标 onPress 契约提供。

验证：无 DOM 元素/浏览器事件且所有文本位于 Text；若示例无远程环境，明确远程状态未执行。

## 典型场景

输入：“把运营列表改为原生 FlatList；范围限当前需求。”

输出：按顺序列出提取当前项目 token 到 src/theme.ts；保留来源与同步时间。 将 div→View、文本→Text、button→Pressable、长列表→FlatList；用 StyleSheet 与当前 RN 版本能力映射。 按工程惯例拆组件/数据/hooks，连接既有原生导航，保留 readonly Props、safe-area 与无障碍标签。 最后返回已处理对象与来源，未运行的项目单列。

验证：theme token 来自当前源，Image 有尺寸。

## 高级场景

输入：“同步当前 Stitch 主题到既有 RN 工程；定制参数为目标 iOS/Android、工程路径、既有导航、主题和刷新范围。”

输出：保留所选参数、Web→Native 映射；长列表选择；平台差异与可访问性检查，提供检查 iOS/Android 的 safe-area、导航和键盘状态的判据；假设不冒充实际配置。

## 异常处理

输入：“将门店预约稿转 iOS/Android 表单，但暂时缺少目标 RN 工程与实际依赖版本。”

输出：“先给本地假设草案。需要补充：目标 RN 工程与实际依赖版本，用于确定真实来源；未执行依赖该来源的写操作。”不返回空答复，也不伪造成功。

## 避免误触发与验证

输入：“React/Vite 浏览器 UI，不扩大任务。”

输出：“使用stitch-react-components；交接当前素材和请求，当前入口不执行额外动作。”

检查：以上五种请求分别检索快速、典型、高级、失败、边界路径；检查输出中的 ID、token、运行结论是否均有输入/回执依据。此人工应用检查不等价于独立模型触发率统计。
