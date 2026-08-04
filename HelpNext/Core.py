from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ErisPulse import sdk
from ErisPulse.Core.Bases import BaseConfig, BaseI18n, BaseModule, I18nKey
from ErisPulse.Core.Event import command

from .Templates import HelpTemplates
from .Visualizer import Visualizer

class Main(BaseModule):
    """ErisPulse modern help module (Takumi-rendered, i18n-aware)."""

    @dataclass
    class ConfigClass(BaseConfig):
        show_hidden_commands: bool = field(
            default=False,
            metadata={
                "description": {"i18n": "HelpNext.cfg_show_hidden", "default": "显示隐藏命令"},
                "ui": {"widget": "switch", "group": "basic", "order": 1},
            },
        )
        group_commands: bool = field(
            default=True,
            metadata={
                "description": {"i18n": "HelpNext.cfg_group_commands", "default": "按分组显示命令"},
                "ui": {"widget": "switch", "group": "basic", "order": 2},
            },
        )
        theme: str = field(
            default="auto",
            metadata={
                "description": {"i18n": "HelpNext.cfg_theme", "default": "图片主题"},
                "ui": {
                    "widget": "select", "group": "render", "order": 3,
                    "options": [
                        {"label": {"i18n": "HelpNext.theme_auto", "default": "自动（跟随时间）"}, "value": "auto"},
                        {"label": {"i18n": "HelpNext.theme_light", "default": "浅色"}, "value": "light"},
                        {"label": {"i18n": "HelpNext.theme_dark", "default": "深色"}, "value": "dark"},
                    ],
                },
            },
        )
        utc_offset: int = field(
            default=8,
            metadata={
                "description": {"i18n": "HelpNext.cfg_utc_offset", "default": "UTC 时区偏移（用于昼夜切换）"},
                "min": -12, "max": 14,
                "ui": {"widget": "number", "group": "render", "order": 4},
            },
        )
        show_logo: bool = field(
            default=True,
            metadata={
                "description": {"i18n": "HelpNext.cfg_show_logo", "default": "头部显示 ErisPulse 图标"},
                "ui": {"widget": "switch", "group": "header", "order": 5},
            },
        )
        header_title: str = field(
            default="",
            metadata={
                "description": {"i18n": "HelpNext.cfg_header_title", "default": "自定义头部标题（留空使用默认）"},
                "ui": {"widget": "text", "group": "header", "order": 6},
            },
        )
        header_subtitle: str = field(
            default="",
            metadata={
                "description": {"i18n": "HelpNext.cfg_header_subtitle", "default": "自定义头部副标题（留空使用默认）"},
                "ui": {"widget": "text", "group": "header", "order": 7},
            },
        )

        _schema_meta = {
            "group_labels": {
                "basic": {"i18n": "HelpNext.group_basic", "default": "基本"},
                "render": {"i18n": "HelpNext.group_render", "default": "渲染"},
                "header": {"i18n": "HelpNext.group_header", "default": "头部"},
            },
        }

    class I18nClass(BaseI18n):
        title: I18nKey = I18nKey(default="Command Help", zh_CN="命令帮助", zh_TW="命令幫助", en="Command Help", ja="コマンドヘルプ", ru="Справка по командам")
        detail_title: I18nKey = I18nKey(default="Command Detail", zh_CN="命令详情", zh_TW="命令詳情", en="Command Detail", ja="コマンド詳細", ru="Подробности команды")
        group_default: I18nKey = I18nKey(default="General", zh_CN="通用命令", zh_TW="一般命令", en="General", ja="一般", ru="Общие")
        no_description: I18nKey = I18nKey(default="No description", zh_CN="暂无描述", zh_TW="暫無描述", en="No description", ja="説明なし", ru="Нет описания")
        usage_hint: I18nKey = I18nKey(default="Use {prefix}help <index> for details", zh_CN="使用 {prefix}help <序号> 查看命令详情", zh_TW="使用 {prefix}help <序號> 查看命令詳情", en="Use {prefix}help <index> for details", ja="{prefix}help <番号> で詳細を表示", ru="Введите {prefix}help <номер> для подробностей")
        command_count: I18nKey = I18nKey(default="{count} commands available", zh_CN="共 {count} 个可用命令", zh_TW="共 {count} 個可用命令", en="{count} commands available", ja="利用可能なコマンド {count} 件", ru="Доступно команд: {count}")
        other_prefixes: I18nKey = I18nKey(default="Other prefixes", zh_CN="其他触发前缀", zh_TW="其他觸發前綴", en="Other prefixes", ja="その他のプレフィックス", ru="Другие префиксы")

        label_description: I18nKey = I18nKey(default="Description", zh_CN="描述", zh_TW="描述", en="Description", ja="説明", ru="Описание")
        label_aliases: I18nKey = I18nKey(default="Aliases", zh_CN="别名", zh_TW="別名", en="Aliases", ja="エイリアス", ru="Псевдонимы")
        label_usage: I18nKey = I18nKey(default="Usage", zh_CN="用法", zh_TW="用法", en="Usage", ja="使い方", ru="Использование")
        label_permission: I18nKey = I18nKey(default="Permission", zh_CN="权限", zh_TW="權限", en="Permission", ja="権限", ru="Права")
        label_group: I18nKey = I18nKey(default="Group", zh_CN="分组", zh_TW="分組", en="Group", ja="グループ", ru="Группа")
        permission_required: I18nKey = I18nKey(default="Requires permission", zh_CN="需要特殊权限", zh_TW="需要特殊權限", en="Requires permission", ja="特殊権限が必要", ru="Требуются права")

        chip_commands: I18nKey = I18nKey(default="Commands", zh_CN="命令", zh_TW="命令", en="Commands", ja="コマンド", ru="Команды")
        chip_groups: I18nKey = I18nKey(default="Groups", zh_CN="分组", zh_TW="分組", en="Groups", ja="グループ", ru="Группы")

        err_out_of_range: I18nKey = I18nKey(default="Index out of range", zh_CN="序号超出范围", zh_TW="序號超出範圍", en="Index out of range", ja="番号が範囲外", ru="Номер вне диапазона")
        err_range_hint: I18nKey = I18nKey(default="Please enter a number between 1 and {count}", zh_CN="请输入 1-{count} 之间的序号", zh_TW="請輸入 1-{count} 之間的序號", en="Please enter a number between 1 and {count}", ja="1〜{count} の番号を入力してください", ru="Введите номер от 1 до {count}")
        err_invalid_arg: I18nKey = I18nKey(default="Invalid argument", zh_CN="参数错误", zh_TW="參數錯誤", en="Invalid argument", ja="引数エラー", ru="Неверный аргумент")
        err_invalid_hint: I18nKey = I18nKey(default="Please enter a valid number", zh_CN="请输入有效的序号", zh_TW="請輸入有效的序號", en="Please enter a valid number", ja="有効な番号を入力してください", ru="Введите корректный номер")
        err_fmt: I18nKey = I18nKey(default="Invalid output format: {fmt}", zh_CN="无效的输出格式：{fmt}", zh_TW="無效的輸出格式：{fmt}", en="Invalid output format: {fmt}", ja="出力形式が無効です: {fmt}", ru="Недопустимый формат вывода: {fmt}")
        err_unknown: I18nKey = I18nKey(default="Unknown argument: {arg}", zh_CN="未知参数：{arg}", zh_TW="未知參數：{arg}", en="Unknown argument: {arg}", ja="不明な引数: {arg}", ru="Неизвестный аргумент: {arg}")
        err_img_unavailable: I18nKey = I18nKey(default="Image output unavailable, falling back to text", zh_CN="图片输出不可用，已回退到文本", zh_TW="圖片輸出不可用，已回退到文字", en="Image output unavailable, falling back to text", ja="画像出力は利用できません。テキストにフォールバックします", ru="Вывод изображений недоступен, используется текст")

        cfg_show_hidden: I18nKey = I18nKey(key="HelpNext.cfg_show_hidden", default="Show hidden commands", zh_CN="显示隐藏命令", zh_TW="顯示隱藏命令", en="Show hidden commands", ja="非表示コマンドを表示", ru="Показывать скрытые команды")
        cfg_group_commands: I18nKey = I18nKey(key="HelpNext.cfg_group_commands", default="Group commands by category", zh_CN="按分组显示命令", zh_TW="按分組顯示命令", en="Group commands by category", ja="カテゴリ別にグループ化", ru="Группировать команды")
        cfg_theme: I18nKey = I18nKey(key="HelpNext.cfg_theme", default="Image theme", zh_CN="图片主题", zh_TW="圖片主題", en="Image theme", ja="画像テーマ", ru="Тема изображения")
        cfg_utc_offset: I18nKey = I18nKey(key="HelpNext.cfg_utc_offset", default="UTC offset for day/night switching", zh_CN="UTC 时区偏移（用于昼夜切换）", zh_TW="UTC 時區偏移（用於晝夜切換）", en="UTC offset (day/night switching)", ja="UTCオフセット（昼夜切替用）", ru="Смещение UTC (для смены темы)")
        cfg_show_logo: I18nKey = I18nKey(key="HelpNext.cfg_show_logo", default="Show ErisPulse icon in header", zh_CN="头部显示 ErisPulse 图标", zh_TW="頭部顯示 ErisPulse 圖示", en="Show ErisPulse icon in header", ja="ヘッダーに ErisPulse アイコンを表示", ru="Показывать иконку ErisPulse в шапке")
        cfg_header_title: I18nKey = I18nKey(key="HelpNext.cfg_header_title", default="Custom header title (empty for default)", zh_CN="自定义头部标题（留空使用默认）", zh_TW="自訂頭部標題（留空使用預設）", en="Custom header title (empty for default)", ja="カスタムヘッダータイトル（空でデフォルト）", ru="Свой заголовок шапки (пусто = по умолчанию)")
        cfg_header_subtitle: I18nKey = I18nKey(key="HelpNext.cfg_header_subtitle", default="Custom header subtitle (empty for default)", zh_CN="自定义头部副标题（留空使用默认）", zh_TW="自訂頭部副標題（留空使用預設）", en="Custom header subtitle (empty for default)", ja="カスタムヘッダーサブタイトル（空でデフォルト）", ru="Свой подзаголовок шапки (пусто = по умолчанию)")

        theme_auto: I18nKey = I18nKey(key="HelpNext.theme_auto", default="Auto (by time)", zh_CN="自动（跟随时间）", zh_TW="自動（跟隨時間）", en="Auto (by time)", ja="自動（時間帯）", ru="Авто (по времени)")
        theme_light: I18nKey = I18nKey(key="HelpNext.theme_light", default="Light", zh_CN="浅色", zh_TW="淺色", en="Light", ja="ライト", ru="Светлая")
        theme_dark: I18nKey = I18nKey(key="HelpNext.theme_dark", default="Dark", zh_CN="深色", zh_TW="深色", en="Dark", ja="ダーク", ru="Тёмная")
        group_basic: I18nKey = I18nKey(key="HelpNext.group_basic", default="Basic", zh_CN="基本", zh_TW="基本", en="Basic", ja="基本", ru="Основные")
        group_render: I18nKey = I18nKey(key="HelpNext.group_render", default="Rendering", zh_CN="渲染", zh_TW="渲染", en="Rendering", ja="レンダリング", ru="Отрисовка")
        group_header: I18nKey = I18nKey(key="HelpNext.group_header", default="Header", zh_CN="头部", zh_TW="頭部", en="Header", ja="ヘッダー", ru="Шапка")

    def __init__(self):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("HelpNext")
        self.command_map: Dict[int, Dict] = {}
        self.visualizer = Visualizer(sdk, {})
        self._help_handler = None

    @staticmethod
    def get_load_strategy():
        from ErisPulse.loaders import ModuleLoadStrategy
        return ModuleLoadStrategy(
            lazy_load=False,
            priority=60,
        )

    async def on_load(self, event):
        self._help_handler = self._make_handler()
        command(
            "help",
            aliases=["h", "帮助"],
            help="显示帮助信息",
            usage="help [序号] [--format <image|html|markdown|text>]",
        )(self._help_handler)
        self.logger.info("HelpNext 已加载")

    async def on_unload(self, event):
        if self._help_handler is not None:
            command.unregister(self._help_handler)
        self.logger.info("HelpNext 已卸载")
        return True

    def _cfg_view(self) -> Dict:
        cfg = self.cfg
        return {
            "show_hidden_commands": cfg.show_hidden_commands,
            "group_commands": cfg.group_commands,
            "theme": cfg.theme,
            "utc_offset": cfg.utc_offset,
            "show_logo": cfg.show_logo,
            "header_title": cfg.header_title,
            "header_subtitle": cfg.header_subtitle,
        }

    def _all_prefixes(self) -> List[str]:
        event_config = sdk.config.getConfig("ErisPulse.event", {}) or {}
        prefix = (event_config.get("command", {}) or {}).get("prefix", "/")
        if isinstance(prefix, list):
            return [str(p) for p in prefix] if prefix else ["/"]
        return [str(prefix)]

    def _build_command_list(self) -> List[Dict]:
        cfg = self._cfg_view()
        show_hidden = cfg["show_hidden_commands"]
        result: List[Dict] = []
        names = command.get_commands() if show_hidden else command.get_visible_commands()
        for name in names:
            info = command.get_command(name)
            if info and name == info.get("main_name"):
                result.append({"name": name, "info": info})
        return result

    def _make_handler(self):
        async def help_command(event):
            await self._handle(event)
        return help_command

    async def _handle(self, event) -> None:
        try:
            args = event.get_command_args()
            commands = self._build_command_list()
            prefixes = self._all_prefixes()
            prefix = prefixes[0] if prefixes else "/"
            cfg = self._cfg_view()
            self.visualizer.config = cfg

            self._index_commands(commands, cfg["group_commands"])

            index, fmt, err = self._parse_args(args)

            if err:
                if err[0] == "format":
                    msg = HelpTemplates._t("err_fmt", fmt=err[1] or "?")
                else:
                    msg = HelpTemplates._t("err_unknown", arg=err[1])
                title = HelpTemplates._t("err_invalid_arg")
                await self._send(event, HelpTemplates.build_error(title, msg), None, "auto-text")
                return

            image = None
            templates = None
            want_image = fmt in ("auto", "image")

            if index is not None:
                if index in self.command_map:
                    cmd = self.command_map[index]
                    if want_image:
                        image = self.visualizer.render_command_detail(cmd, prefix, prefixes)
                    templates = HelpTemplates.build_command_detail(cmd, prefix, prefixes)
                else:
                    title = HelpTemplates._t("err_out_of_range")
                    msg = HelpTemplates._t("err_range_hint", count=len(commands))
                    if want_image:
                        image = self.visualizer.render_error(title, msg)
                    templates = HelpTemplates.build_error(title, msg)
            else:
                if want_image:
                    image = self.visualizer.render_help_list(
                        commands, self.command_map, prefix, cfg["group_commands"], prefixes,
                    )
                templates = HelpTemplates.build_help_list(
                    commands, self.command_map, prefix, cfg["group_commands"], prefixes,
                )

            await self._send(event, templates, image, fmt)
        except Exception as e:
            self.logger.error(f"处理帮助命令出错: {e}", exc_info=True)

    @staticmethod
    def _normalize_format(v) -> Optional[str]:
        v = str(v).lower().strip()
        return {
            "image": "image", "img": "image",
            "html": "html", "h5": "html",
            "markdown": "markdown", "md": "markdown",
            "text": "text", "txt": "text",
        }.get(v)

    @staticmethod
    def _parse_args(args: List[str]) -> Tuple[Optional[int], str, Optional[Tuple[str, str]]]:
        index = None
        fmt = "auto"
        err = None
        i, n = 0, len(args)
        while i < n:
            low = str(args[i]).lower()
            if low.isdigit():
                if index is None:
                    index = int(low)
                else:
                    err = ("unknown", args[i])
                    break
            elif low == "--format":
                if i + 1 < n:
                    v = Main._normalize_format(args[i + 1])
                    if v is None:
                        err = ("format", str(args[i + 1]))
                        break
                    fmt = v
                    i += 1
                else:
                    err = ("format", "")
                    break
            elif low.startswith("--format="):
                v = Main._normalize_format(low.split("=", 1)[1])
                if v is None:
                    err = ("format", low.split("=", 1)[1])
                    break
                fmt = v
            else:
                err = ("unknown", args[i])
                break
            i += 1
        return index, fmt, err

    def _index_commands(self, commands: List[Dict], group_commands: bool) -> None:
        self.command_map = {}
        grouped: Dict[str, List[Dict]] = {}
        if group_commands:
            for cmd in commands:
                g = cmd["info"].get("group") or "default"
                grouped.setdefault(g, []).append(cmd)
        else:
            grouped["default"] = list(commands)
        idx = 1
        for _, cmds in grouped.items():
            for cmd in cmds:
                self.command_map[idx] = cmd
                idx += 1

    @staticmethod
    def _supports(event, method: str) -> bool:
        try:
            return event.supports(method)
        except Exception:
            return False

    def _select_text_format(self, event, templates) -> Tuple[str, str]:
        if self._supports(event, "Html"):
            return ("Html", templates["html"])
        if self._supports(event, "Markdown"):
            return ("Markdown", templates["markdown"])
        return ("Text", templates["text"])

    async def _send(self, event, templates, image: Optional[bytes], fmt: str) -> None:
        try:
            if fmt == "image":
                if image and self._supports(event, "Image"):
                    await event.reply(image, method="Image")
                    return
                note = HelpTemplates._t("err_img_unavailable")
                await event.reply(note)
                return

            if fmt in ("html", "markdown", "text"):
                await event.reply(templates[fmt], method=fmt.capitalize())
                return

            if fmt == "auto" and image and self._supports(event, "Image"):
                try:
                    await event.reply(image, method="Image")
                    return
                except Exception as e:
                    self.logger.warning(f"图片发送失败，回退到文本: {e}")

            method, content = self._select_text_format(event, templates)
            try:
                await event.reply(content, method=method)
            except Exception:
                await event.reply(templates["text"])
        except Exception as e:
            self.logger.error(f"发送帮助出错: {e}")
            try:
                await event.reply(templates["text"])
            except Exception:
                pass
