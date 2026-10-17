# 公开版资源与本机状态

路径以本Skill实际目录为基准，执行`scripts/paths.py`查看。公开版保留完整制作流程、三种输入模式、工作流脚本、公开模板目录与可追溯的官方预览链接。

## 随包资源

- `references/data/motiongit-catalog.json`：带日期的官网公开目录。
- `references/data/preview-sources.json`：实际观察到的官方封面、短预览与完整预览URL、大小和SHA；仓库不再分发这些第三方媒体字节。
- `references/data/motiongit-experience.json`：特定版本的通用制作经验，网站声明、技术通过与审美认可分别对待。
- `references/data/platform-fields.json`：已去除账号和草稿信息的历史字段观察，发布前仍核对当前后台。
- `references/data/course-catalog.json`：无课程内容的结构示例；实际课程、会员权益由使用者提供并确认。
- `references/writing/`及`scripts/measure_script.py`：Rico表达方法和时长参考，不包含原课程字幕、私有文件清单或声纹。
- `assets/motiongit/gallery.html`：仅引用官方公共媒体地址的目录页；可用本机预览服务打开。

## 首次初始化

~~~text
python3 <技能目录>/scripts/setup_local.py
python3 <技能目录>/scripts/verify_resources.py
~~~

本机状态默认在`~/.local/share/rico-short-video/`，可通过`RICO_SHORT_VIDEO_DATA_HOME`指定其它目录。初始化只创建本机目录、空的个人包登记表和可自行填写的profile.json；不会登录、下载模板、传云、生成媒体或发布视频，不覆盖已有配置。

个人模板包和授权状态只在本机`.motiongit-library/`；公开预览缓存只在`public-media/`，视频原片和工程仍属各任务。公开目录中的模板不表示本机已下载、已授权或可商用；使用者必须以自己的账号获取并按当前许可核验。模板Key、登录态、私有原片和本机校验状态不得提交仓库。

模板预览可先查看官方链接。需要缓存时先列出，再显式下载所需类型：

~~~text
python3 <技能目录>/scripts/cache_previews.py --list
python3 <技能目录>/scripts/cache_previews.py --kind cover --download
python3 <技能目录>/scripts/cache_previews.py --kind full --download
python3 <技能目录>/scripts/motiongit/serve_gallery.py
~~~

下载只访问清单中实际观察到的官方HTTPS地址，校验文件摘要并复用准确缓存。完整视频可能较大；缓存不包含模板授权，不能替代本人正式领取。公开链接变化或校验失败时记录缺口，不默默把新字节当原版本。

ChatCut、MotionGit及浏览器/图片工具需要在使用者环境中可用，并分别完成所需登录授权。安装Skill或插件不会继承维护者的账户连接。没有实际工具能力时保留制作资料和具体缺口，不把流程说明称为实际渲染成功。
