# 现代组件：先复用，再编排

主题决定“这一段为什么出现、出现多久”，组件提供已实现的运动与布局，`theme.css`
统一字体、强调色、圆角、描边和节奏。组合这三层，避免每条视频重写所有效果。
Hyperframes Catalog 是可编辑源码，不是只能调用的黑盒插件，也不是任意 React UI 库。

## 找到合适的效果

```bash
node <skill-root>/scripts/hf.mjs catalog --query "two income curves comparison" --json
node <skill-root>/scripts/hf.mjs catalog --query "highlight a key phrase" --json
```

用英文描述动作，屏幕内容仍写中文。先搜索当前段落需要的效果，不遍历整库或安装整组。
结果中的 name 是实际安装名；查看条目说明和源码，确认是想要的效果再用。
搜索结果较长时只向模型返回最相关几项。无需下载语义搜索模型即可先用词匹配。

## 对 DraftCut 有用的起点

| 表达需求 | 优先搜索/查看的组件 | 使用判断 |
|---|---|---|
| 两条路径或职业收入曲线 | `mk-line-graph`、`data-chart` | 改为自己的示意关系与图例，不保留演示数据 |
| 关键词高亮与现代字幕 | `caption-highlight`、`caption-clip-wipe`、`caption-editorial-emphasis` | 保留最终 SRT，统一中文字体；短语高亮即可，不伪造逐词时间 |
| 反问、反差、综艺强调 | `caption-kinetic-slam`、`caption-emoji-pop` | 只在语义落点介入，不把整片变成持续弹跳 |
| 数字或结论解释 | `animated-bar-chart`、`chart-story` | 图形随讲述展开；只用实际内容支持的数据 |
| 方法、步骤与因果 | `flowchart`、`flowchart-vertical` | 选择适合画布的方向，控制字量，避开人物 |
| 身份条与段落标记 | `yt-lower-third`、`lt-mask-reveal` | 以创作者信息替换示例，不把每句都做成标题卡 |
| B-roll 进出与视觉衔接 | 搜索 `subtle wipe transition` / `soft reveal` | 先找克制转场；强 shader 效果只在内容需要时使用 |

条目可能随 Registry 更新；这些是查找起点，安装前以当前查询结果为准，不自动升级运行时。

## 安装与接入

```bash
node <skill-root>/scripts/hf.mjs add mk-line-graph --dir "$output_dir/hyperframes" --no-clipboard --json
node <skill-root>/scripts/hf.mjs add caption-highlight --dir "$output_dir/hyperframes" --no-clipboard --json
```

- **Block**：独立场景，通常位于 `compositions/<name>.html`。在主页面用
  `data-composition-src` 引入，填写 id、开始时间、时长、画布尺寸。宿主 id 与子场景 id 对齐。
  若把完整文档改为 template，style/script 必须放在 template 内，避免被装配器丢弃。
- **Component**：小效果片段，通常位于 `compositions/components/<name>.html`。读取后把所需
  HTML/CSS/JS 合入当前场景。不要把其整套示例页面、演示字幕和另一个主时间线一并复制。
- 主页面注册 `window.__timelines.master`；子场景注册自己的 id，由框架自动装配。
  给组件内部元素加唯一 id 前缀，避免多次使用时相互影响。
- 安装后的文件留在项目中复用，不在每次导出时重新安装；已有自定义内容不要用 `--force` 覆盖。
  将条目名、来源 URL、修改点简记到 `components-used.json`，方便下一条视频继承。

## 统一到你的视觉体系

以现有 `theme.css` 或用户的视觉规范为准。新项目可从少量变量开始：字体、主文字色、
强调色、背景、圆角和描边；由实际设计决定值，不硬编码“诗人程序员 Jun”到所有项目。
先统一这些变量，再调整尺寸、安全区和动效进出。现有主题中的布局关系继续有效。

中文适配尤其注意：移除英文大写/过大字距，加载真实中文字体，长句按语义分页或调整字号。
原 SRT 只有句级时间时使用句/短语级高亮，不为插件重跑转写。不改变口播原文来迁就样例。

组件带远程字体、GSAP CDN 或演示图片时，按需本地化到 assets，使用初始化时已复制的
`assets/gsap.min.js`；不要给同一页面加载多个 GSAP 版本。样例图表数据必须替换或明确标为示意。
Lottie 适合现成动画资产；GSAP 适合花字、曲线和时间编排；Three.js/WebGL 仅在确需三维效果时使用。

## 快速对 Agent 说

> 用“竖屏个人 IP”作为视觉起点。先查 Catalog 里的曲线图和关键词高亮组件，统一成我的视觉风格，
> 动态口播保持主体，B-roll 按语义穿插，MG 在人物旁边分步解释。复用好的实现，不保留演示文案。

组件检索、安装、设计、render 都沿用 DraftCut 的批准状态。不要运行上游整套 talking-head-recut
或迁移 skill 来重新转写、要求额外批准、逐场景截图。安装组件不代表上传素材；没有明确要求时
不运行 publish、feedback、file-issue、云渲染或其他外部发布命令。

参考：[Catalog](https://hyperframes.heygen.com/catalog)、
[Registry 接线说明](https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes-registry/SKILL.md)。
