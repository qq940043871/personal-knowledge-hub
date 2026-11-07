# FFmpeg安装与核心概念

> 模块：安装与基础
> 更新时间：2026-03-29

---

## 一、FFmpeg概述

### 组件

```
ffmpeg      # 命令行工具，转码推流
ffplay     # 播放器
ffprobe    # 媒体信息查看
```

---

## 二、安装

### Windows

```bash
# 方法1: scoop
scoop install ffmpeg

# 方法2: choco
choco install ffmpeg

# 方法3: 下载编译好的包
# https://www.gyan.dev/ffmpeg/builds/
# 解压后添加到PATH
```

### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL
sudo yum install epel-release
sudo yum install ffmpeg

# 或编译安装（最新版本）
wget https://ffmpeg.org/releases/ffmpeg-6.0.tar.gz
tar xzf ffmpeg-6.0.tar.gz
cd ffmpeg-6.0
./configure --prefix=/usr/local/ffmpeg
make && make install
```

### macOS

```bash
brew install ffmpeg
```

---

## 三、核心概念

### 封装格式(Container)
```
MP4 │ MKV │ AVI │ FLV │ MOV │ TS
```

### 视频编码(Codec)
```
H.264/AVC │ H.265/HEVC │ VP8 │ VP9 │ AV1
```

### 音频编码
```
AAC │ MP3 │ OPUS │ FLAC │ PCM
```

### 常用参数

```bash
# 输入输出
-i              # 输入文件
-f              # 强制格式

# 视频参数
-c:v            # 视频编码器 (copy表示不转码)
-s              # 分辨率 (如1920x1080)
-r              # 帧率 (如30)
-b:v            # 视频码率
-pixel_format   # 像素格式 (yuv420p)

# 音频参数
-c:a            # 音频编码器
-b:a            # 音频码率
-ar             # 采样率 (如44100)
-ac             # 声道数

# 其他
-y              # 自动覆盖输出文件
-v quiet        # 减少日志输出
-progress url   # 输出进度到文件
```

<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 460" font-family="'Microsoft YaHei','PingFang SC',sans-serif">
  <defs>
    <marker id="ar1" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 z" fill="#64748b"/>
    </marker>
  </defs>
  <text x="360" y="32" text-anchor="middle" font-size="16" font-weight="bold" fill="#1e293b">FFmpeg转码处理流程</text>
  <rect x="260" y="56" width="200" height="44" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
  <text x="360" y="83" text-anchor="middle" font-size="13" fill="#1e293b">输入文件 input</text>
  <path d="M320,100 V126 H220 V146" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M400,100 V146" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="100" y="150" width="240" height="54" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="220" y="172" text-anchor="middle" font-size="13" fill="#1e293b">视频流</text>
  <text x="220" y="192" text-anchor="middle" font-size="12" fill="#475569">编码 H.264·H.265·AV1</text>
  <rect x="380" y="150" width="240" height="54" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="500" y="172" text-anchor="middle" font-size="13" fill="#1e293b">音频流</text>
  <text x="500" y="192" text-anchor="middle" font-size="12" fill="#475569">编码 AAC·MP3·OPUS</text>
  <path d="M220,204 V230 H330 V250" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <path d="M500,204 V230 H390 V250" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="260" y="254" width="200" height="54" rx="8" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5"/>
  <text x="360" y="276" text-anchor="middle" font-size="13" fill="#1e293b">封装格式 Container</text>
  <text x="360" y="296" text-anchor="middle" font-size="12" fill="#475569">MP4·MKV·FLV·TS</text>
  <line x1="360" y1="308" x2="360" y2="350" stroke="#64748b" stroke-width="1.5" marker-end="url(#ar1)"/>
  <rect x="260" y="354" width="200" height="44" rx="8" fill="#ecfdf5" stroke="#16a34a" stroke-width="1.5"/>
  <text x="360" y="381" text-anchor="middle" font-size="13" fill="#1e293b">输出文件 output</text>
  <text x="360" y="434" text-anchor="middle" font-size="13" fill="#475569">ffmpeg -i input.avi output.mp4 转换封装与编码</text>
</svg>

*图：FFmpeg转码处理流程示意（依正文整理）*

---

## 四、常用命令

### 查看媒体信息

```bash
# 查看完整信息
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4

# 简化输出
ffprobe input.mp4

# 查看视频流信息
ffprobe -v error -show_entries stream=codec_name,width,height,bit_rate input.mp4
```

### 格式转换

```bash
# AVI转MP4
ffmpeg -i input.avi output.mp4

# 指定编码器
ffmpeg -i input.mp4 -c:v libx265 -c:a aac output.mp4

# 保持原编码（快速转换）
ffmpeg -i input.mov -c copy output.mp4

# 转换为FLV（推流常用）
ffmpeg -i input.mp4 -c copy -f flv output.flv
```

### 视频处理

```bash
# 调整分辨率
ffmpeg -i input.mp4 -vf "scale=1280:720" output.mp4

# 裁剪视频
ffmpeg -i input.mp4 -vf "crop=1920:1080:0:0" output.mp4

# 视频截图
ffmpeg -i input.mp4 -ss 00:00:10 -frames:v 1 output.jpg

# 提取GIF
ffmpeg -i input.mp4 -ss 00:00:05 -t 3 -vf "fps=10,scale=480:-1" output.gif

# 视频拼接
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4
```

### 音频处理

```bash
# 提取音频
ffmpeg -i input.mp4 -vn -c:a copy output.aac

# 转换音频格式
ffmpeg -i input.mp3 -c:a libopus -b:a 128k output.opus

# 调整音量
ffmpeg -i input.mp4 -af "volume=2.0" output.mp4

# 音频混合
ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac output.mp4
```

---

*下一步：流媒体处理*
