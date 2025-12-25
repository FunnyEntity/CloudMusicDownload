# CloudMusicDownloader

网易云音乐下载器 - 一个简单易用的音乐下载工具。

## 功能特点

- 扫码登录网易云音乐账号
- 支持 Listen1 备份文件 (listen1_backup.json)
- 自动下载歌曲，支持 FLAC/MP3 音质
- 自动添加封面和标签信息
- 自动下载歌词
- VIP用户不受下载次数限制

## 使用方法

### 1. 获取歌单 JSON 文件

1. 访问 [Listen1](https://listen1.github.io/listen1/)
2. 搜索并添加你喜欢的歌曲到歌单
3. 点击"歌单管理" -> "导出歌单" -> 下载 JSON 文件

### 2. 运行程序

**方式一：直接运行 Python 脚本**

```bash
python musicdownload.py
```

**方式二：运行 EXE 文件**

双击 `MusicDownload.exe`

### 3. 使用步骤

1. **扫码登录** - 点击"扫码登录"按钮，用网易云音乐 App 扫描二维码
2. **选择 JSON 文件** - 点击"浏览"按钮，选择之前导出的 listen1_backup.json
3. **选择音质** - 选择 Auto（自动）、MP3 或 FLAC
4. **选择下载目录** - 点击"选择目录"设置下载位置
5. **开始下载** - 点击"开始下载"按钮

### 4. 下载结果

歌曲保存格式：`歌手 - 专辑 - 歌名.mp3/flac`

歌词文件：`歌手 - 专辑 - 歌名.lrc`

## 依赖安装

如果使用 Python 脚本运行，需要先安装依赖：

```bash
pip install -r requirements.txt
```

## 打包 EXE

```bash
build_exe.bat
```

打包后会自动清理临时文件，只保留 `MusicDownload.exe`

## 参数说明（代码中）

```python
PLAYLIST_IDS = []     # 待下载歌单列表
SONG_IDS = []         # 待下载歌曲列表（从 JSON 自动加载）
QUALITY = "auto"      # 音质：auto（自动）、mp3、flac
```

## 相关项目

- [pycloudmusic](https://github.com/FengLiuFeseliud/pycloudmusic) - 网易云音乐 API
- [Listen1](https://listen1.github.io/listen1/) - 开源音乐播放器

## 免责声明

本项目仅供个人学习和研究使用，请勿用于商业用途。

使用本工具下载的音乐内容版权归属于网易云音乐及其版权所有者。请用户在使用本工具时遵守相关法律法规及网易云音乐的服务条款。

作者不对使用本工具所产生的任何后果负责。下载的内容请在 24 小时内删除，支持正版音乐。

