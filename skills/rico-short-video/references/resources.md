# 随包资源与本机状态

路径以本Skill实际目录为准，可执行`scripts/paths.py`查看；原片、媒体和可编辑工程写入使用者指定的任务目录。全局安装仍只有一个维护源，兼容链接不另建副本。

## 当前制作资源

- [mg-visual-standard.md](mg-visual-standard.md)和`assets/mg-shared/standard.json`：唯一MG视觉/工艺/质量入口及共享包版本。随包SceneRoot/PaperSurface/geometry提供全画幅与同源材质起点；原生样段验收前不声称已达标。
- [实际参考索引](data/mg-reference-index.json)和`scripts/mg_references.py`：固定源版本/SHA、认可范围、字体与许可。普通运行只定位核验；`--source-dir <含SKILL.md的长技能目录>`从本机来源复制，`--download`才取固定公共URL，缓存位于本机状态的`mg-reference-cache/`而非技能内。输出实际路径后观看图片/时序/动态、读相应代码和用途限制；不把参考人像/声音导入新片。长技能尚未自动接入共享包。

- [animation-production.md](animation-production.md)、[mg-whole-first-and-camera.md](mg-whole-first-and-camera.md)：短视频原生MG的内容、整体/模块与镜头创作。
- [native-mg-runtime.md](native-mg-runtime.md)及[交接清单](../templates/animation-handoff.json)：项目内源码、支持模块、属性/实例、时钟与实际输出。当前宿主的create-motion-graphics技能及运行时文档负责具体API；本技能不复制一套易过时的宿主实现。
- [mg-method-source.md](mg-method-source.md)：迁移来源、仅动画范围和未完成的新标准样片验证。
- [caption-design.md](caption-design.md)与[audio-style.md](audio-style.md)：原生字幕的设计层次、积极配乐与仅换音乐的修改范围。
- [纯MG研究场景](../assets/mg-shared/TaskCapabilityStudy.jsx)及[属性](../assets/mg-shared/study-properties.json)：已认可横竖基准的去人像/去音轨代码研究；项目本机profile可另记私人样段路径，公共安装不包含私人影片。
- `references/writing/`及`scripts/measure_script.py`：Rico表达方法和时长参考，不包含原课程字幕、私有文件清单或声纹。
- `references/data/platform-fields.json`：已去除账号和草稿信息的历史字段观察，发布前仍核对当前后台。
- `references/data/course-catalog.json`：无课程内容的结构示例；实际课程、会员权益由使用者提供并确认。
- 原有色彩、字幕、人物、发布与归档参考及脚本继续使用；无需因新动画方法安装第二套整片剪辑环境。

新制作需要当前可用的ChatCut及本条实际需要的浏览器/图片工具、原生MG运行环境；读取对应宿主的官方合同，分别核对所需登录/许可。源码写入本条工程，支持文件使用稳定相对依赖，实际引用的字体/素材随工程留存或说明外部依赖。安装技能不继承账号、媒体传云或费用授权。没有相应工具能力时保存具体设计与源码并报告缺口，不把说明文档称为渲染成功，也不自动回退MotionGit。

## 结构校验与私有状态

~~~text
python3 <技能目录>/scripts/verify_resources.py
~~~

默认检查随包结构与链接即可。验证脚本中的`counts.templates`是历史MotionGit目录数量，`--check-private`/`--check-media`检查的是旧库/预览，不是新原生MG的开工或交付门槛。

私有状态默认在`~/.local/share/rico-short-video/`，可用`RICO_SHORT_VIDEO_DATA_HOME`指定其它目录；历史快照在其中`history/`。需要本机profile时可沿用已有配置，首次才按需运行`scripts/setup_local.py`；它也会创建旧库空登记，不表示新制作需要领模板。原片和工程仍属任务目录，账号Key/登录态/私有原片不提交仓库。

## 旧MotionGit工程恢复资源

以下仅用于已使用MotionGit的历史工程，不在新制作时默认读目录、检查更新或下载：

- `references/data/motiongit-catalog.json`、`motiongit-experience.json`、`preview-sources.json`及`assets/motiongit/gallery.html`保留历史目录、经验与官方公共预览引用。
- [motiongit.md](motiongit.md)、[motiongit-selection.md](motiongit-selection.md)、[motiongit-library.md](motiongit-library.md)及相关脚本保留旧源参数、锁定版本、许可和恢复办法。
- 个人包仍在技能外的本机私有缓存；既有缓存和授权凭证不因新版技能删除或复制进工程包。旧工程需要具体文件时才读取实际登记，不能从公开目录推断已下载/已授权/可商用。

旧预览或个人模板并非原生MG方法的运行依赖；保留历史恢复能力不改变当前动画创作入口。
