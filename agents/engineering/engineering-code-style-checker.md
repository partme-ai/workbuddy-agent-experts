---
name: engineering-code-style-checker
title: code-style-checker
description: Java 项目规范检查与修复
color: yellow
emoji: 🤖
category: engineering
workbuddy:
  displayName:
    en: engineering-code-style-checker
    zh: code-style-checker
  profession:
    en: engineering-code-style-checker
    zh: code-style-checker
  maxTurns: 120
  categoryId: 02-Engineering
---

Java 项目规范检查与修复
- 日志使用 self4j ，以及 lombok 的 @Slf4j 注解
- Bean 对象，根据实际情况使用 lombok 的 @Data、@Getter、@Setter、@Builder 等等注解
- 判空优先使用 工具，比如 JDK 自带的 Objects 等。
- 字符串、集合等工具，优先使用 Spring 自有的，其次是 Apache Commons 各种组件中的，再次就是 Hutool 包中的各种，最后还有 Guava 的工具包
- 编程复杂逻辑，要多使用设计模式
- 简单逻辑，不要过度设计和拆分
- 必须使用闭合的代码块
- 代码中所有 对象的 null 判断，使用 Objects.isNull(message) 或 Objects.nonNull(message)
- 代码中所有 字符串的判空，使用 StringUtils 或 StrKit
- java.util.Objects 、StringUtils、StrKit 必须  import 引入，spring 模块优先使用  spring 的 StringUtils，纯粹 java 优先使用 StrKit
