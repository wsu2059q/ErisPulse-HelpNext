import base64
import html
import struct
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ErisPulse import i18n
from ErisPulse.Core.Event import command

from .themes import get_theme

class Visualizer:
    """卡片图渲染器。

    渲染管线开放装饰钩子：外部模块可通过 ``Visualizer.register_decorator(fn, priority)``
    在渲染前修改 ``{kind, body, css, theme, config}`` 上下文，实现主题美化、
    看板娘插图等装饰能力；核心默认保持简洁专业的外观。
    """

    CARD_WIDTH = 880
    _LOGO_W = 120

    _ICON_PATH = Path(__file__).parent / "assets" / "icon.png"
    _icon_cache: Optional[Tuple[str, Tuple[int, int]]] = None

    _DECORATORS: List[Tuple[int, int, Callable]] = []
    _DECORATOR_SEQ = 0

    _FONT_SANS = (
        '"DM Sans", "Inter", "Helvetica Neue", Arial, "Noto Sans SC", '
        '"Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'
    )
    _FONT_MONO = '"JetBrains Mono", "Source Code Pro", Consolas, monospace'

    _CSS_TPL = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: __FONTSANS__;
        color: __INK__; -webkit-font-smoothing: antialiased;
    }
    .page { background: __PAGE__; padding: 36px; }
    .card {
        background: __CARD__; border: 1px solid __BORDER__; border-radius: 16px;
        padding: 18px 20px; margin-bottom: 14px;
    }
    .head-row { display: flex; align-items: center; gap: 14px; }
    .logo-side { display: block; }
    .head-text { min-width: 0; }
    .title { font-size: 23px; font-weight: 700; color: __INK__; letter-spacing: -0.5px; }
    .subtitle { font-size: 14px; color: __STEEL__; margin-top: 3px; }
    .divider { height: 1px; background: __SEP__; margin: 14px 0; }
    .chips { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
    .chip {
        padding: 7px 16px; border-radius: 9999px; font-size: 14px;
        background: __SOFT__; color: __STEEL__; border: 1px solid __BORDER__;
    }
    .chip b { color: __INK__; font-weight: 700; margin-right: 5px; font-variant-numeric: tabular-nums; }
    .masonry { display: flex; gap: 14px; align-items: flex-start; }
    .mcol { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 14px; }
    .mcol .card { margin-bottom: 0; }
    .cmd-head { display: flex; align-items: center; gap: 10px; }
    .num {
        flex: 0 0 auto; min-width: 28px; height: 28px; padding: 0 10px;
        border-radius: 9999px; background: __NUMBG__; color: __NUMFG__;
        font-size: 13px; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
        font-variant-numeric: tabular-nums;
    }
    .cmd-code {
        font-family: __FONTMONO__; font-size: 15px; font-weight: 700;
        color: __INK__; white-space: nowrap;
    }
    .cmd-code .pfx { color: __STEEL__; font-weight: 600; }
    .group-tag {
        margin-left: auto; font-size: 12px; font-weight: 600; color: __STEEL__;
        padding: 4px 11px; border-radius: 9999px; white-space: nowrap;
        background: __SOFT__; border: 1px solid __BORDER__;
    }
    .cmd-desc { font-size: 14.5px; color: __SLATE__; margin-top: 9px; line-height: 1.55; }
    .cmd-aliases { margin-top: 9px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .cmd-aliases .lbl { font-size: 12px; color: __STEEL__; margin-right: 2px; }
    .alias-tag {
        font-family: __FONTMONO__; font-size: 13px;
        background: __SOFT__; color: __SLATE__; padding: 3px 10px; border-radius: 9999px;
    }
    .cmd-usage {
        margin-top: 9px; font-family: __FONTMONO__; font-size: 13.5px;
        background: __CODEBG__; color: __SLATE__; padding: 8px 11px; border-radius: 8px;
        line-height: 1.5;
    }
    .detail-label { font-size: 12px; font-weight: 600; color: __STEEL__; letter-spacing: 0.8px; margin-bottom: 6px; text-transform: uppercase; }
    .detail-value { font-size: 16.5px; color: __INK__; line-height: 1.5; }
    .detail-value.mono { font-family: __FONTMONO__; background: __CODEBG__; padding: 8px 12px; border-radius: 8px; font-size: 15px; }
    .detail-value.warn { color: __ERR__; }
    .aliases { display: flex; flex-wrap: wrap; gap: 8px; }
    .foot { font-size: 13px; color: __MUTED__; text-align: center; margin-top: 14px; line-height: 1.7; }
    .foot code {
        color: __SLATE__; background: __SOFT__; border: 1px solid __BORDER__;
        padding: 1px 8px; border-radius: 9999px; font-family: __FONTMONO__;
    }
    .err-title { font-size: 20px; font-weight: 700; color: __ERR__; letter-spacing: -0.3px; }
    .err-msg { font-size: 15px; color: __INK__; margin-top: 8px; line-height: 1.5; }
    """

    def __init__(self, sdk, config: Dict):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("HelpNext.Visualizer")
        self.config = config
        self._takumi_inst = None
        self._behavior = None
        self._behavior_style = None

    @classmethod
    def register_decorator(cls, fn: Callable, priority: int = 0) -> None:
        """注册渲染装饰器：``fn(ctx)`` 在渲染前收到
        ``{kind, body, css, theme, config}`` 上下文，可就地修改 ``body`` / ``css``。"""
        cls._DECORATOR_SEQ += 1
        cls._DECORATORS.append((priority, cls._DECORATOR_SEQ, fn))

    @classmethod
    def unregister_decorator(cls, fn: Callable) -> None:
        """注销渲染装饰器。"""
        cls._DECORATORS = [d for d in cls._DECORATORS if d[2] is not fn]

    @classmethod
    def clear_decorators(cls) -> None:
        """清空全部渲染装饰器。"""
        cls._DECORATORS.clear()

    @staticmethod
    def _t(key: str, **kwargs) -> str:
        full = f"HelpNext.{key}"
        return i18n.t(full, default=full, **kwargs)

    @property
    def takumi(self):
        if self._takumi_inst is None:
            inst = None
            try:
                inst = self.sdk.module.get("Takumi")
            except Exception:
                inst = None
            if inst is None:
                inst = getattr(self.sdk, "Takumi", None)
            self._takumi_inst = inst
        return self._takumi_inst

    def _theme(self) -> Dict:
        spec = get_theme(self.config.get("style", "default"))
        mode = self.config.get("theme", "auto")
        if mode == "auto":
            offset = self.config.get("utc_offset", 8)
            hour = int((time.time() / 3600 + offset) % 24)
            mode = "dark" if (hour >= 19 or hour < 7) else "light"
        return {"mode": mode, **(spec["dark"] if mode == "dark" else spec["light"])}

    def _css(self) -> Tuple[str, Dict]:
        t = self._theme()
        css = (
            self._CSS_TPL
            .replace("__FONTSANS__", self._FONT_SANS)
            .replace("__FONTMONO__", self._FONT_MONO)
            .replace("__PAGE__", t["page"]).replace("__CARD__", t["card"])
            .replace("__INK__", t["ink"]).replace("__SLATE__", t["slate"])
            .replace("__STEEL__", t["steel"]).replace("__MUTED__", t["muted"])
            .replace("__SEP__", t["sep"]).replace("__SOFT__", t["soft"])
            .replace("__CODEBG__", t["codebg"])
            .replace("__NUMBG__", t["numbg"]).replace("__NUMFG__", t["numfg"])
            .replace("__ERR__", t["err"])
            .replace("__BORDER__", t["border"])
        )
        extra = get_theme(self.config.get("style", "default"))["css_extra"]
        if extra:
            css += extra
        return css, t

    @staticmethod
    def _png_dims(data: bytes) -> Optional[Tuple[int, int]]:
        try:
            if data[:8] != b"\x89PNG\r\n\x1a\n":
                return None
            w, h = struct.unpack(">II", data[16:24])
            return w, h
        except Exception:
            return None

    @classmethod
    def _icon(cls) -> Optional[Tuple[str, Tuple[int, int]]]:
        if cls._icon_cache is None:
            try:
                data = cls._ICON_PATH.read_bytes()
                dims = cls._png_dims(data)
                b64 = base64.b64encode(data).decode()
                cls._icon_cache = (b64, dims) if dims else ("", None)
            except Exception:
                cls._icon_cache = ("", None)
        b64, dims = cls._icon_cache
        if not b64 or not dims:
            return None
        return b64, dims

    @staticmethod
    def _esc(text) -> str:
        return html.escape(str(text))

    @staticmethod
    def _aliases_of(name: str, info: Dict) -> List[str]:
        main_name = info.get("main_name", name)
        return [
            a for a, m in command.aliases.items()
            if m == main_name and a != main_name
        ]

    async def _attach_behavior(self, style: str):
        """获取当前主题的行为实例；风格切换时自动 detach 旧主题。"""
        if self._behavior is not None and self._behavior_style == style:
            return self._behavior
        if self._behavior is not None:
            try:
                await self._behavior.on_detach()
            except Exception as e:
                self.logger.warning(f"主题行为 on_detach 失败: {e}")
            self._behavior = None
        cls = get_theme(style)["behavior"]
        if cls is not None:
            behavior = cls()
            try:
                await behavior.on_attach(self.sdk)
            except Exception as e:
                self.logger.warning(f"主题行为 on_attach 失败: {e}")
                behavior = None
            self._behavior = behavior
        self._behavior_style = style
        return self._behavior

    async def _render(self, kind: str, body_html: str) -> Optional[bytes]:
        # 主题行为尽早挂载（含首次萌图拉取），不因 Takumi 懒加载而推迟
        style = self.config.get("style", "default")
        behavior = await self._attach_behavior(style)
        takumi = self.takumi
        if takumi is None or not hasattr(takumi, "render_html"):
            self.logger.warning("Takumi 不可用，跳过图片渲染")
            return None
        css, theme = self._css()
        # 实色画布：整体内容包裹于 .page，避免渲染画布透明
        body_html = f"<div class='page'>{body_html}</div>"
        if Visualizer._DECORATORS or behavior is not None:
            ctx = {
                "kind": kind, "body": body_html, "css": css,
                "theme": theme, "config": self.config,
            }
            if behavior is not None:
                try:
                    behavior.decorate(ctx, self.sdk)
                except Exception as e:
                    self.logger.warning(f"主题行为 decorate 失败，已跳过: {e}")
            for _, _, fn in sorted(Visualizer._DECORATORS, key=lambda d: (d[0], d[1])):
                try:
                    fn(ctx)
                except Exception as e:
                    self.logger.warning(f"装饰器执行失败，已跳过: {e}")
            body_html, css = ctx["body"], ctx["css"]
        try:
            kwargs = {}
            if behavior is not None and hasattr(behavior, "images"):
                try:
                    resources = behavior.images() or []
                except Exception as e:
                    self.logger.warning(f"主题渲染资源获取失败: {e}")
                    resources = []
                if resources:
                    kwargs["images"] = resources
            return takumi.render_html(
                body_html, stylesheets=[css],
                width=self.CARD_WIDTH, height=None, lang="zh-CN",
                **kwargs,
            )
        except Exception as e:
            self.logger.error(f"Takumi 渲染失败: {e}")
            return None

    def _card(self, inner: str) -> str:
        return f"<div class='card'>{inner}</div>"

    @staticmethod
    def _num_cols(count: int) -> int:
        if count <= 2:
            return 1
        if count <= 12:
            return 2
        return 3

    def _header(self, subtitle: str, chips_html: str) -> str:
        cfg = self.config
        show_logo = cfg.get("show_logo", True)
        title = cfg.get("header_title") or "ErisPulse"
        sub = cfg.get("header_subtitle") or subtitle

        logo_html = ""
        if show_logo:
            icon = self._icon()
            if icon:
                b64, (nw, nh) = icon
                dw = self._LOGO_W
                dh = round(nh * dw / nw)
                logo_html = (
                    f"<img class='logo-side' src='data:image/png;base64,{b64}' "
                    f"width='{dw}' height='{dh}' alt='ErisPulse'/>"
                )

        text_html = (
            f"<div class='head-text'><div class='title'>{self._esc(title)}</div>"
            f"<div class='subtitle'>{self._esc(sub)}</div></div>"
        )
        return (
            f"<div class='head-row'>{logo_html}{text_html}</div>"
            f"<div class='divider'></div>{chips_html}"
        )

    def _chips(self, cmd_count: int, group_count: Optional[int] = None) -> str:
        s = (
            f"<div class='chips'>"
            f"<div class='chip'><b>{cmd_count}</b>{self._esc(self._t('chip_commands'))}</div>"
        )
        if group_count is not None:
            s += f"<div class='chip'><b>{group_count}</b>{self._esc(self._t('chip_groups'))}</div>"
        s += "</div>"
        return s

    def _command_card(self, cmd: Dict, idx: int, prefix: str, show_group: bool = False) -> str:
        info = cmd["info"]
        name = cmd["name"]
        desc = info.get("help") or self._t("no_description")

        head = f"<div class='cmd-head'><div class='num'>{idx}</div>"
        head += (
            f"<div class='cmd-code'><span class='pfx'>{self._esc(prefix)}</span>"
            f"{self._esc(name)}</div>"
        )
        if show_group and info.get("group"):
            gname = self._t("group_default") if info["group"] == "default" else info["group"]
            head += f"<span class='group-tag'>{self._esc(gname)}</span>"
        head += "</div>"

        extra_html = ""
        aliases = self._aliases_of(name, info)
        if aliases:
            tags = "".join(
                f"<span class='alias-tag'>{self._esc(prefix)}{self._esc(a)}</span>"
                for a in aliases
            )
            extra_html += (
                f"<div class='cmd-aliases'><span class='lbl'>{self._esc(self._t('label_aliases'))}</span>"
                f"{tags}</div>"
            )
        if info.get("usage"):
            usage = info["usage"].replace("/", prefix)
            extra_html += f"<div class='cmd-usage'>{self._esc(usage)}</div>"

        return (
            f"{head}"
            f"<div class='cmd-desc'>{self._esc(desc)}</div>"
            f"{extra_html}"
        )

    @staticmethod
    def _masonry(items: List[str], num_cols: int) -> str:
        cols: List[List[str]] = [[] for _ in range(num_cols)]
        for i, card in enumerate(items):
            cols[i % num_cols].append(card)
        inner = "".join(f"<div class='mcol'>{''.join(col)}</div>" for col in cols)
        return f"<div class='masonry'>{inner}</div>"

    async def render_help_list(
        self,
        commands: List[Dict],
        command_map: Dict[int, Dict],
        prefix: str,
        group_commands: bool,
        prefixes: Optional[list] = None,
    ) -> Optional[bytes]:
        if not commands:
            return None

        others = [
            p for p in (prefixes or [prefix])
            if p != prefix and len(prefixes or []) > 1
        ]

        grouped: Dict[str, List[Dict]] = {}
        for cmd in commands:
            g = cmd["info"].get("group") or "default"
            grouped.setdefault(g, []).append(cmd)

        ordered: List[Dict] = []
        for g, cmds in grouped.items():
            ordered.extend(cmds)

        for i, cmd in enumerate(ordered, start=1):
            command_map[i] = cmd

        chips = self._chips(len(commands), len(grouped) if group_commands else None)
        head_inner = self._header(self._t("title"), chips)

        cards = [
            self._card(self._command_card(cmd, i, prefix, show_group=group_commands))
            for i, cmd in enumerate(ordered, start=1)
        ]

        foot_lines = [self._t("command_count", count=len(commands))]
        if others:
            foot_lines.append(f"{self._t('other_prefixes')}: {'、'.join(others)}")
        footer = "<div class='foot'>" + "<br>".join(foot_lines) + "</div>"

        body = self._card(head_inner) + self._masonry(cards, self._num_cols(len(commands))) + footer
        return await self._render("help_list", body)

    async def render_command_detail(
        self,
        cmd: Dict,
        prefix: str,
        prefixes: Optional[list] = None,
    ) -> Optional[bytes]:
        name = cmd["name"]
        info = cmd["info"]
        others = [
            p for p in (prefixes or [prefix])
            if p != prefix and len(prefixes or []) > 1
        ]

        chips = (
            f"<div class='chips'>"
            f"<div class='chip'><code style='font-family:{self._FONT_MONO};"
            f"font-size:12.5px;font-weight:600;'>"
            f"{self._esc(prefix)}{self._esc(name)}</code></div></div>"
        )
        head_inner = self._header(self._t("detail_title"), chips)

        cards = [self._card(head_inner)]

        def add_card(label: str, value_html: str, value_class: str = ""):
            vc = f" {value_class}" if value_class else ""
            inner = (
                f"<div class='detail-label'>{self._esc(label)}</div>"
                f"<div class='detail-value{vc}'>{value_html}</div>"
            )
            cards.append(self._card(inner))

        add_card(
            self._t("label_description"),
            self._esc(info.get("help") or self._t("no_description")),
        )

        aliases = self._aliases_of(name, info)
        if aliases:
            tags = "".join(
                f"<span class='alias-tag'>{self._esc(prefix)}{self._esc(a)}</span>"
                for a in aliases
            )
            add_card(self._t("label_aliases"), f"<div class='aliases'>{tags}</div>")

        if info.get("usage"):
            add_card(
                self._t("label_usage"),
                self._esc(info["usage"].replace("/", prefix)),
                value_class="mono",
            )

        if info.get("permission"):
            add_card(
                self._t("label_permission"),
                self._esc(self._t("permission_required")),
                value_class="warn",
            )

        if info.get("group"):
            gname = self._t("group_default") if info["group"] == "default" else info["group"]
            add_card(self._t("label_group"), self._esc(gname))

        body = "".join(cards)
        if others:
            body += (f"<div class='foot'>{self._t('other_prefixes')}: "
                     f"{'、'.join(self._esc(p) for p in others)}</div>")
        return await self._render("command_detail", body)

    async def render_error(self, title: str, message: str) -> Optional[bytes]:
        head_inner = self._header(self._t("title"), "")
        err = (f"<div class='err-title'>{self._esc(title)}</div>"
               f"<div class='err-msg'>{self._esc(message)}</div>")
        body = self._card(head_inner) + self._card(err)
        return await self._render("error", body)
