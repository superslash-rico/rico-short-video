# Rico 口播与拍屏视频制作 Skill

为短视频制作提供可复用的协作流程：**露脸口播、手机拍屏/录屏讲解、混合模式**。ChatCut负责主剪辑、字幕、声音和最终导出，原生可编辑源码按讲述创作MG动画；成片、封面、发布准备、复盘与归档在同一流程中接续。

本仓库是轻量公开分发版，当前 `main` 为 **v0.4.0 / 来源技能修订48**。它提供工作流和辅助脚本，实际视频处理需要使用者自己的工具、素材及授权。露脸与手机单源拍屏已有制作案例；混合、双源同步、稳像/去频闪和自动跟踪仍按具体素材验证。

当前版将六项剪辑经验接入下一条制作入口：自然肤色与高光、真实素材和动画表达、声画事件、转场中途检查、同源单声单字幕、模块修改及依赖归档。支持按当前实际工具优先接续ChatCut Desktop，并保留网页表面的适用方法。详见[制作入口](skills/rico-short-video/references/next-video.md)和[人像高光检查](skills/rico-short-video/references/presenter-layout.md)。

## 安装

在Codex中发送：

> 请从 https://github.com/superslash-rico/rico-short-video 安装 skills/rico-short-video 到我的用户级技能目录，并按 resources.md 初始化本机状态。先检查已有同名技能，不覆盖维护版或本机修改。

也可使用已安装的skill-installer，让它从仓库的`skills/rico-short-video`路径安装。安装后在下一轮任务调用`$rico-short-video`；若当前客户端未刷新技能列表，重新启动后核对。

首次初始化与结构检查：

```text
python3 <技能目录>/scripts/setup_local.py
python3 <技能目录>/scripts/verify_resources.py
```

需要Python 3.10或更新版本。ChatCut、当前原生MG运行环境及浏览器能力需各自准备；新制作不需要MotionGit模板库。旧工程恢复才核对旧模板许可；安装Skill不继承维护者的登录、Key或付费权限。

## 使用

- **露脸口播：**“用 $rico-short-video 制作这个主题，先写两分钟内逐字稿。”
- **已拍原片：**“用 $rico-short-video 剪这条原片，重点保留……，两分钟以内。”
- **拍屏讲解：**“这是后置手机拍电脑屏幕、边拍边讲的素材，按实际操作和结果剪辑。”
- **混合素材：**“这里有露脸和屏幕演示两类原片，根据内容安排。”

助手先查看实际原片并选择模式。已有原片直接进入分析和剪辑，不倒补写稿审批。纯拍屏不强加人物窗；混合按真实覆盖区间处理，不能循环或冻结短露脸素材假装全程出镜。

露脸开场默认2—3秒全幅真人；适用区间人物持续可见。缩窗/资料组合需背景时用同源视频加轻色罩。手机观看要看清真实目标；拍屏保护输入、反馈、等待、结果和解释的关系，无口播等待压缩或加速需据实标注。

拍屏先按原声和操作事件剪辑，保护按钮、反馈、结果和字幕；默认用原生短透明图形辅助表达。旧MotionGit去底/VP9 alpha案例只用于历史工程恢复，不证明新方法的透明烘焙能力。设备播报与配乐、动作音效分开处理。详见[拍屏制作流程](skills/rico-short-video/references/screen-explainer.md)及[公开方法摘要](skills/rico-short-video/references/data/first-screen-case.json)。

封面默认16:9、3:4、4:3分别构图，先读取已认可的系列风格。视频不露脸，也可以在实际肖像许可内设计本人封面；安装本技能不会继承维护者的肖像授权。

所有平台最终发布按钮由用户自己点击，或取得对具体最终点击动作的明确授权。用户明确说任务完成后，再核验依赖、清理过程文件并归档。

## 更新给同事

让同事在Codex中发送：

> 请从同一个仓库检查Rico视频Skill的新版本；先备份本机修改，保留我的profile、个人模板和项目原片，再更新适用的公开版文件。正在制作的视频记录原版本，升级前先核对影响。

本仓库的Git标签与[Releases](https://github.com/superslash-rico/rico-short-video/releases)标记正式版本。可指定标签安装；`main`代表当前维护分支。安装工具若提示目标已存在，不把重装当成升级，也不先删除用户目录。

同事反馈先放本条复盘或改进建议；维护者审核、去除私人资料并验证后再发布。公共仓库更新与本机Skill自我迭代是不同动作，不自动将原片、用户对话或内部课程上传到公共仓库。

## 可选：作为Codex插件分发

仓库包含可移植`plugin.json`、兼容`.codex-plugin/plugin.json`及市场目录。在支持自定义市场的客户端可添加：

```text
codex plugin marketplace add superslash-rico/rico-short-video
```

随后按当前客户端界面安装。市场刷新入口：

```text
codex plugin marketplace upgrade rico-skills
```

具体支持与刷新行为以客户端为准，首次安装/升级应在新会话核对。直接Skill安装与插件安装选择一种，避免同名重复。

参考：[OpenAI技能文档](https://learn.chatgpt.com/docs/build-skills)、[插件与仓库市场](https://developers.openai.com/plugins/build/plugins)。

## 当前动画与声音标准

专业MG采用完整工程画幅：深紫黑`#0C0A14`、清楚而克制的点阵、中部横向淡紫微光；点阵在主体下层，弱跟随实际镜头，纸面始终不透明。用纸面材质、厚度、阴影、透视与前后关系建立空间，不添加复杂舞台或顶底遮挡带。

先理解讲述、设计完整场景，再精修对象的前态/变化/结果，分别编排摄影机和对象。横竖屏共享工艺与质量，分别构图、取景、避让真人；保留短视频原人物窗口和其它剪辑流程。已有认可的同内容横竖基准和完整竖屏案例；随包纯MG研究代码不含人物、音轨或真实截图。

字幕继续原生可编辑，保留准确原文和时码，以字级和重点提高设计感；MG不放常驻Rico角标。提到具体软件时主动取得官方真实图标并按口播锚点融入动画。配乐默认明亮、积极、有活力的无歌词器乐，实际听口播混音，保留人声ducking。

详见[共享视觉与质量](skills/rico-short-video/references/mg-visual-standard.md)、[原生MG创作](skills/rico-short-video/references/animation-production.md)、[字幕设计](skills/rico-short-video/references/caption-design.md)、[配乐](skills/rico-short-video/references/audio-style.md)及[案例范围](skills/rico-short-video/references/data/first-native-mg-case.json)。第三方代码来源见[许可说明](docs/THIRD_PARTY_NOTICES.md)。长视频技能尚未被本仓库自动修改。

## 旧工程的模板与预览

公开版包含45项历史官方目录参考、123项已观察到的预览/封面URL及通用制作经验；不包含第三方预览视频、模板原包、账户helper或授权回执。

可以查看[模板链接页](skills/rico-short-video/assets/motiongit/gallery.html)或先启动本机图库服务。可选缓存只在使用者本机，准确SHA匹配时复用：

```text
python3 <技能目录>/scripts/cache_previews.py --list
python3 <技能目录>/scripts/cache_previews.py --kind cover --download
python3 <技能目录>/scripts/cache_previews.py --kind full --download
python3 <技能目录>/scripts/motiongit/serve_gallery.py
```

下载需显式执行，不调用生成服务或读取账户Key；完整预览可能较大。官方URL变化或摘要不符时保留旧缓存并报告。图库启动时校验并优先使用已缓存的预览，下载新缓存后重新启动图库即可。缓存预览不等于获得模板许可。

## 本机资料与配置

默认本机状态目录：`~/.local/share/rico-short-video/`，也可设置`RICO_SHORT_VIDEO_DATA_HOME`。每人维护自己的profile、个人包和校验状态；项目原片、工程和成片留在各任务目录。

仓库没有内部课程目录、私人素材、手机号/邮箱、登录态、模板Key及维护者的“已下载/已授权”状态。课程和会员权益在实际任务中由使用者提供并确认。为Rico制作沿用Rico规范；其他讲述者使用其本人明确要求，不移植Rico的经历或权益。

## 验证与贡献

```text
python3 tools/check_public.py
python3 -m unittest discover -s tests -v
python3 skills/rico-short-video/scripts/test_closeout.py
```

维护者使用当前skill-creator官方校验工具检查SKILL.md。提交建议时描述问题、适用条件和可公开证据；不要提交个人包、Key、原片或内部资料。发布范围见[PUBLICATION.md](docs/PUBLICATION.md)。

## 许可

当前仓库未指定开源许可证。第三方软件、模板、字体与素材各遵循其自身许可，本仓库不对它们重新授权。
