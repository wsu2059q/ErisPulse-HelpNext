# ErisPulse-HelpNext

<div align="center">
  <img src=".github/assets/ErisPulseLogo.png" width="140" alt="ErisPulse" />
</div>

Renders the ErisPulse `/help` command as a card image via [ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/), with day/night theme and multilingual support. Requires ErisPulse 2.7.0+.

[English](#english) | [简体中文](#简体中文)

---

<a id="english"></a>

## English

> 2.7.0+ recommends this module. The classic [`ErisPulse-HelpModule`](https://pypi.org/project/ErisPulse-HelpModule/) is still maintained for backward compatibility. Both register `/help`, so enable only one.

### Features

- Day/night theme by local time (19–7 dark), or pin light / dark
- Multilingual: zh-CN / zh-TW / en / ja / ru (declarative `I18nClass`)
- Falls back to Html → Markdown → Text when images aren't supported
- Declarative config (`ConfigClass`), descriptions also translated

### Install

```bash
epsdk install HelpNext
```

### Commands

```
/help                        List all available commands (card image)
/help <index>                Show detail of the command at <index>
/help --format <fmt>         Force output format: image | html | markdown | text
```

Aliases: `/h`, `/帮助`

### Config

First load writes defaults; edit the `HelpNext` section:

```toml
[HelpNext]
show_hidden_commands = false   # show commands marked hidden
group_commands = true          # group commands by category
theme = "auto"                 # auto | light | dark
utc_offset = 8                 # UTC offset for day/night switching
show_logo = true               # show ErisPulse icon in header
header_title = ""              # custom header title (empty = default)
header_subtitle = ""           # custom header subtitle (empty = default)
```

- `show_hidden_commands`: when `true`, shows commands marked as hidden
- `group_commands`: when `false`, lists all commands in a single group
- `theme`: `auto` (by time), or fixed `light` / `dark`
- `utc_offset`: UTC offset used for day/night detection
- `show_logo`: show the ErisPulse icon in the header
- `header_title` / `header_subtitle`: customize the header text (empty = defaults)

### Dependencies

- ErisPulse SDK 2.7.0+
- [ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/) (declared as a dependency, auto-installed)

---

<a id="简体中文"></a>

## 简体中文

> 2.7.0+ 推荐使用本模块；经典版 [ErisPulse-HelpModule](https://pypi.org/project/ErisPulse-HelpModule/) 继续维护，用于向后兼容。两者都注册 `/help`，请按需启用其一。

### 功能特性

- 按本地时间自动切换昼夜主题（19–7 点深色），也可固定为浅色 / 深色
- 多语言：zh-CN / zh-TW / en / ja / ru（声明式 `I18nClass`）
- 平台不支持图片时按 Html → Markdown → 文本 回退
- 声明式配置（`ConfigClass`），配置描述同样支持多语言

### 安装

```bash
epsdk install HelpNext
```

### 命令

```
/help                        列出所有可用命令（卡片图片）
/help <序号>                  查看指定序号命令的详情
/help --format <格式>         指定输出格式：image | html | markdown | text
```

别名：`/h`、`/帮助`

### 配置选项

首次加载会写入默认配置，可在 ErisPulse 配置的 `HelpNext` 节修改：

```toml
[HelpNext]
show_hidden_commands = false   # 是否显示隐藏命令
group_commands = true          # 是否按分组显示
theme = "auto"                 # auto | light | dark
utc_offset = 8                 # 昼夜切换用的时区偏移
show_logo = true               # 头部是否显示 ErisPulse 图标
header_title = ""              # 自定义头部标题（留空使用默认）
header_subtitle = ""           # 自定义头部副标题（留空使用默认）
```

- `show_hidden_commands`：设为 `true` 时显示标记为隐藏的命令
- `group_commands`：设为 `false` 时不分组，所有命令在同一列表
- `theme`：图片主题，`auto` 跟随时间，或固定 `light` / `dark`
- `utc_offset`：昼夜判定使用的 UTC 时区偏移
- `show_logo`：头部是否显示 ErisPulse 图标
- `header_title` / `header_subtitle`：自定义头部标题 / 副标题（留空使用默认）

### 依赖

- ErisPulse SDK 2.7.0+
- [ErisPulse-Takumi](https://pypi.org/project/ErisPulse-Takumi/)（已声明为依赖，自动安装）
