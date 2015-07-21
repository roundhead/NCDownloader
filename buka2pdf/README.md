## 安装依赖

本程序需要使用refine-buka来解析buka的压缩包，请使用

```bash
git clone https://github.com/gumblex/refine-buka
```

下载该程序

## 使用方法

### 添加漫画
```bash
python2 buka.py search <keyword>
```

按照提示添加相应漫画记录

### 获取已添加漫画最新内容
```bash
python2 buka.py refresh
```

推荐配合crontab使用

