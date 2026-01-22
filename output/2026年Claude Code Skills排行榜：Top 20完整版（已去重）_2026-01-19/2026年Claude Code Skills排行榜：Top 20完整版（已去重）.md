# 2026年Claude Code Skills排行榜：Top 20完整版（已去重）

> 原文链接: https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247484754&idx=1&sn=bf00799b9a1d88e37af7efd5e70caea6&chksm=91eb8ad984fba2474ce7dcf923a67cf03731af47ddfba887906bddd0d39bf6bbc41fd6ded38b&mpshare=1&scene=24&srcid=0120r8Lac4JkxW8S1nOUddlP&sharer_shareinfo=2e0b9f34792f8347901cef44f7f812ee&sharer_shareinfo_first=2e0b9f34792f8347901cef44f7f812ee#rd
> 图片状态: 已本地化 (assets/)

---

![图片](assets/ff1ff6f5f6ffa72d498074173b2371c1.png)

> 数据更新时间：2026年1月19日
> 
> 这是一份持续更新的Claude Code Skills GitHub排行榜，收录了官方仓库和社区热门项目。

* * *

## 为什么要关注Skills？

2025年10月，Anthropic正式推出了Agent Skills系统。

简单说就是：**给Claude装上专业技能包，让它自己判断什么时候该用** 。

Skills是一个`SKILL.md`文件，里面写着某个领域的专业知识和操作流程。装好之后，Claude会根据对话上下文**自动识别并触发** ——你不需要输入任何命令。比如你说"帮我审查这段代码"，如果装了code-review Skill，Claude会自动按Skill里定义的检查清单执行。

> ⚠️ Skills ≠ Slash Commands：Slash Commands（如`/commit`）需要你手动输入触发；Skills是Claude自己判断要不要用。

三个月过去，GitHub上的Skills生态已经爆发式增长。哪些值得装？哪些是噱头？

看排行榜最直接。

* * *

## 官方仓库排行榜（2026年1月）

这两个是Anthropic官方维护的，质量有保障。

排名| 仓库名称| Stars| 功能定位  
---|---|---|---  
1| anthropics/claude-code| 58.1k ⭐| Claude Code主程序  
2| anthropics/skills| 45.1k ⭐| 官方Skills仓库  
  
**官方Skills包含什么？**

  * docx - Word文档处理（创建、编辑、追踪修改）
  * pdf - PDF提取（文本、表格、元数据、合并）
  * pptx - PPT生成与调整
  * xlsx - Excel操作（公式、图表、数据转换）
  * web-artifacts-builder - 构建复杂的Web组件



这五个是官方Skills里用得最多的。处理文档类任务，先装这套。

* * *

## 社区热门Skills排行榜 Top 20

数据来源：SkillsMP · 2026年1月19日

> 说明：热度值基于GitHub Stars和使用量综合计算，已剔除功能重复的Skills。

### 🏆 开发工作流类

排名| Skill名称| 热度| 功能介绍  
---|---|---|---  
1| create-pr| 169.7k| 自动创建GitHub PR，格式化标题，通过CI校验  
2| skill-lookup| 142.6k| 技能查找与安装器，问什么Skills都能找到  
3| frontend-code-review| 126.3k| 前端代码审查，支持tsx/ts/js文件检查清单  
4| component-refactoring| 126.3k| 组件重构专家，安全拆分和优化React组件  
5| github-code-review| 48.2k| GitHub代码审查+AI协调，多Agent协同评审  
  
### 🧠 AI/LLM开发类

排名| Skill名称| 热度| 功能介绍  
---|---|---|---  
6| cache-components-expert| 137.2k| 缓存组件专家，优化LLM应用的缓存策略  
7| opus-4.5-migration| 47.2k| Opus 4.5迁移指南，升级现有Claude应用  
8| confidence-check| 19.8k| 置信度检查，让Claude评估自己的回答可靠性  
9| context-engineering| 5.5k| 上下文工程基础，优化Prompt设计  
10| multi-agent-patterns| 5.5k| 多Agent架构模式，设计协作式AI系统  
  
### 🛠️ 专项技术类

排名| Skill名称| 热度| 功能介绍  
---|---|---|---  
11| dify-frontend-testing| 124.9k| Dify前端测试，专为Dify平台优化  
12| electron-chromium-upgrade| 119.6k| Electron升级指南，Chromium版本迁移  
13| zig-syscalls-bun| 86k| Zig系统调用，Bun运行时底层开发  
14| cloudflare-skill| 2.8k| Cloudflare全平台开发，60+产品一站式指南  
  
### ✍️ 技能创作与管理类

排名| Skill名称| 热度| 功能介绍  
---|---|---|---  
15| skill-writer| 96k| 技能编写器，帮你创建高质量SKILL.md  
16| skill-creator| 38.5k| 技能创建向导，从零开始设计Skills  
17| llm-project-methodology| 5.5k| LLM项目方法论，AI项目最佳实践  
  
### 📦 综合框架类

排名| Skill名称| 热度| 功能介绍  
---|---|---|---  
18| obra/superpowers| 29.1k| 超能力框架，TDD+YAGNI+DRY方法论全家桶  
19| awesome-claude-skills| 21.6k| 社区精选合集，50+经过验证的Skills  
20| skillport| 229| 跨Agent技能管理器，一处管理多处使用  
  
* * *

## 重点项目拆解

### 🔥 Superpowers（29.1k Stars）

这个项目在2026年1月14日单日涨了1,871星，冲上GitHub Trending榜首。

**为什么这么火？**

创建者Jesse Vincent把自己的开发方法论打包成了Skills：

  * 强制TDD（测试驱动开发）
  * YAGNI原则（不写用不到的代码）
  * DRY原则（不重复自己）



用了之后，Claude不会上来就写代码，而是先问：**"你到底想实现什么？" 包含的核心技能：**

技能| 作用  
---|---  
test-driven-development| 红-绿-重构的TDD流程  
systematic-debugging| 系统化定位问题  
code-review| 代码审查清单  
refactoring| 安全重构步骤  
  
开发者反馈：用Superpowers之后，Claude可以自主编程2小时以上不跑偏。

**安装方式：**

claude

> 
>     /install-plugin obra/superpowers  
>     > 
> 
> `

* * *

### 📚 awesome-claude-skills（ComposioHQ版，21.6k Stars）

这是一个**Skills目录** ，不是单个Skill。

收录了50+个经过验证的Skills，按用途分类：

ddle;word-break:normal;word-wrap:normal;}

分类| 典型Skills  
---|---  
测试与质量| TDD、代码覆盖率检查  
调试与排障| 系统化调试、日志分析  
协作与工作流| Git提交、PR创建  
文档处理| Word/PDF/PPT/Excel  
  
**这个列表的价值** ：不用你一个个找，直接从这里挑。

* * *

### ☁️ cloudflare-skill（2.8k Stars）

把整个Cloudflare平台（60+产品）教给了Claude。

**解决的问题** ：

  * Workers还是Pages？
  * Durable Objects还是Workflows？
  * 怎么配置Bindings？



一个`SKILL.md`文件，引用了60个参考文档。

**适合谁** ：重度Cloudflare用户。

* * *

## 按用途速查表

不想看排行榜？直接告诉你装哪个。

你要干什么| 装这个| 热度  
---|---|---  
自动创建PR、规范化Git工作流| create-pr| 169.7k  
查找和安装其他Skills| skill-lookup| 142.6k  
前端代码审查| frontend-code-review| 126.3k  
优化LLM应用缓存| cache-components-expert| 137.2k  
想让Claude像高级工程师一样工作| obra/superpowers| 29.1k  
处理Word/PDF/Excel文档| anthropics/skills| 45.1k  
开发Electron应用、升级Chromium| electron-chromium-upgrade| 119.6k  
开发Cloudflare应用| cloudflare-skill| 2.8k  
创建自己的Skill| skill-writer| 96k  
找各种Skills参考| awesome-claude-skills| 21.6k  
  
* * *

## 怎么安装Skills？

> 💡 Skills有两种形态：**Plugin** （技能集合包）和**单独的SKILL.md文件** ，安装方式不同。

**方法1：安装Plugin（技能集合包）**

Superpowers、awesome-claude-skills这类是以Plugin形式发布的，包含多个Skills：

claude

> 
>     /install-plugin obra/superpowers  
>     > 
> 
> `

**方法2：手动复制SKILL.md（单个技能）**

从SkillsMP或GitHub下载单个SKILL.md文件：

# 项目级Skills（仅当前项目可用）
    
    
    mkdir -p your-project/.claude/skills/  
    cp skill-name/SKILL.md your-project/.claude/skills/skill-name/  
    

`

# 个人级Skills（所有项目可用）
    
    
    mkdir -p ~/.claude/skills/  
    cp skill-name/SKILL.md ~/.claude/skills/skill-name/  
    

`

**方法3：使用SkillPort（第三方工具）**
    
    
     pip install skillport  
    skillport search code-review  
    skillport install skill-name  
    

`

* * *

## 近期涨幅最快的项目

数据来源：2026年1月第三周SkillsMP趋势

项目| 周涨幅| 原因  
---|---|---  
create-pr| +12.3k| PR自动化需求爆发  
skill-lookup| +8.7k| Skills生态入口  
cache-components-expert| +6.2k| LLM应用性能优化热  
skill-writer| +5.8k| 越来越多人创建自己的Skill  
obra/superpowers| +4.2k| 登顶GitHub Trending  
frontend-code-review| +3.9k| 前端团队刚需  
  
* * *

## 我的建议

**新手** ：先装官方的`anthropics/skills`，把文档处理技能用起来。

**开发者** ：直接上`obra/superpowers`，让Claude按规范流程写代码。

**想探索更多** ：逛逛`awesome-claude-skills`列表，按需选装。

* * *

## 相关资源

类型| 链接  
---|---  
官方文档| code.claude.com/docs/en/skills  
Skills规范| github.com/anthropics/skills/tree/main/spec  
视觉目录| awesomeclaude.ai/awesome-claude-skills  
Skills市场| skillsmp.com  
  
* * *

 _本文数据截至2026年1月19日，Stars数会持续变动，以GitHub实时数据为准。_

 _  
_

  


**- END-**

**  
**

**  
**

**更多关于**AI工具、Cursor、MCP相关** 的教程和资讯请持续关注后续分享！**

**本文完整版详见公众号：**未来的回响****

**文章精校版参见知识星球：**AI工具实战派****

****

  


  


  


**【限时开放】** 欢迎加入**AI工具实战派** 交流群一起学习进步～

  


![](assets/97f309071e53a6e259abeff3967ed547.jpg)

  


**AI编程、AI运营、工具资料分享** 请加入知识星球

![](assets/7fb720ec1a4d6bdf0eac6e3a15cf6bcf.jpg)

**  
**

**  
**

**- 推荐阅读-**

**  
**

**【AI编程】**

  * [Cursor+Gitlens再也不用担心频繁重建项目了](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483693&idx=1&sn=cffa5e0542c912297387ee2637b98cee&scene=21#wechat_redirect>)

  * [使用Cursor时如何规避AI改坏代码——终极指南](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483699&idx=1&sn=7fbd243a6357d8f15e526b2a3126af5a&scene=21#wechat_redirect>)

  * [Cursor编程bug反复改不好⁉️让AI用思维链整理思路](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483705&idx=1&sn=7a3658d619cf882f4f2ccd1919d69f71&scene=21#wechat_redirect>)
  * [怎么从Cursor转到Claude Code？配合GLM-4.5的性价比AI编程指南](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247484341&idx=1&sn=d3d70b3522d175c9448a66f2fc0daef6&scene=21#wechat_redirect>)  




**【AI设计】**

  * [AI设计对话指南（第一期）：一文掌握20个主流UI组件库，让AI秒懂你的设计意图！](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483978&idx=1&sn=28e4853177c30b4bbadf1acb8ac276dc&scene=21#wechat_redirect>)

  * [AI设计对话指南（第二期）：19种UI设计风格速查手册](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247484010&idx=1&sn=5f4773a2ffb1df2b62adb01b167f84d8&scene=21#wechat_redirect>)

  * [AI设计对话指南（第三期）：UI设计提示词指南，减少与AI掰扯](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247484219&idx=1&sn=e4841d0987003f0d722fd3ff3a495a2b&scene=21#wechat_redirect>)

  * [如何使用Magic MCP生成好看的UI](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483898&idx=1&sn=325483d6c635e779b6cc0f105daaf69e&scene=21#wechat_redirect>)

  * [如何使用Magic MCP生成好看的UI（第二期）](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483920&idx=1&sn=29ae0739dff846d72c9792291aedc23d&scene=21#wechat_redirect>)

  * [如何在Cursor中使用Figma MCP自动进行产品原型设计](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247484042&idx=1&sn=769e7881f49ae4529025bdb434d55c1e&scene=21#wechat_redirect>)




  


**【AI工具 】**

  * [【2025最全】12个顶级MCP服务器资源汇总，Cursor/Claude/AI开发者必备](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483865&idx=1&sn=9998131d2ac940084fefbfb8224206fa&scene=21#wechat_redirect>)

  * [简单介绍一些常用的MCP服务器，快用来提高Cursor干活效率吧](<https://mp.weixin.qq.com/s?__biz=MzA4Nzc3NzkzNQ==&mid=2247483825&idx=1&sn=a6138244d10a05c96520a1dffaff9528&scene=21#wechat_redirect>)


  

