import base64
import html
import math
import struct
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ErisPulse import i18n
from ErisPulse.Core.Event import command

class Visualizer:
    CARD_WIDTH = 880
    _PAGE_PAD = 36
    _CARD_PAD_V = 16
    _CARD_PAD_H = 18
    _CARD_GAP = 14
    _COL_GAP = 14
    _CARD_BORDER = 2
    _LOGO_W = 120

    _ICON_PATH = Path(__file__).parent / "assets" / "icon.png"
    _icon_cache: Optional[Tuple[str, Tuple[int, int]]] = None

    _FONT_SANS = (
        '"DM Sans", "Inter", "Helvetica Neue", Arial, "Noto Sans SC", '
        '"Source Han Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif'
    )
    _FONT_MONO = '"JetBrains Mono", "Source Code Pro", Consolas, monospace'

    _CSS_TPL = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
        font-family: __FONTSANS__;
        background: __PAGE__; color: __INK__; -webkit-font-smoothing: antialiased;
        padding: 36px;
    }
    .card {
        background: __CARD__; border: 1px solid __BORDER__; border-radius: 16px;
        padding: 16px 18px; margin-bottom: 12px;
    }
    .head-row { display: flex; align-items: center; gap: 14px; }
    .logo-side { display: block; }
    .head-text { min-width: 0; }
    .title { font-size: 20px; font-weight: 700; color: __INK__; letter-spacing: -0.5px; }
    .subtitle { font-size: 13px; color: __STEEL__; margin-top: 2px; }
    .divider { height: 1px; background: __SEP__; margin: 14px 0; }
    .chips { display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
    .chip {
        padding: 6px 14px; border-radius: 9999px; font-size: 13px;
        background: __SOFT__; color: __STEEL__; border: 1px solid __BORDER__;
    }
    .chip b { color: __INK__; font-weight: 700; margin-right: 4px; font-variant-numeric: tabular-nums; }
    .masonry { display: flex; gap: 14px; align-items: flex-start; }
    .mcol { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 14px; }
    .mcol .card { margin-bottom: 0; }
    .cmd-head { display: flex; align-items: center; gap: 10px; }
    .num {
        flex: 0 0 auto; min-width: 26px; height: 26px; padding: 0 9px;
        border-radius: 9999px; background: __NUMBG__; color: __NUMFG__;
        font-size: 12px; font-weight: 700;
        display: flex; align-items: center; justify-content: center;
        font-variant-numeric: tabular-nums;
    }
    .cmd-code {
        font-family: __FONTMONO__; font-size: 13.5px; font-weight: 700;
        color: __INK__; white-space: nowrap;
    }
    .cmd-code .pfx { color: __STEEL__; font-weight: 600; }
    .group-tag {
        margin-left: auto; font-size: 11px; font-weight: 600; color: __STEEL__;
        padding: 3px 10px; border-radius: 9999px; white-space: nowrap;
        background: __SOFT__; border: 1px solid __BORDER__;
    }
    .cmd-desc { font-size: 13px; color: __SLATE__; margin-top: 8px; line-height: 1.55; }
    .cmd-aliases { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
    .cmd-aliases .lbl { font-size: 11px; color: __STEEL__; margin-right: 2px; }
    .alias-tag {
        font-family: __FONTMONO__; font-size: 12px;
        background: __SOFT__; color: __SLATE__; padding: 3px 9px; border-radius: 9999px;
    }
    .cmd-usage {
        margin-top: 8px; font-family: __FONTMONO__; font-size: 12.5px;
        background: __CODEBG__; color: __SLATE__; padding: 7px 10px; border-radius: 8px;
        line-height: 1.5;
    }
    .detail-label { font-size: 11px; font-weight: 600; color: __STEEL__; letter-spacing: 0.8px; margin-bottom: 6px; text-transform: uppercase; }
    .detail-value { font-size: 15px; color: __INK__; line-height: 1.5; }
    .detail-value.mono { font-family: __FONTMONO__; background: __CODEBG__; padding: 8px 12px; border-radius: 8px; font-size: 14px; }
    .detail-value.warn { color: __ERR__; }
    .aliases { display: flex; flex-wrap: wrap; gap: 8px; }
    .foot { font-size: 12.5px; color: __MUTED__; text-align: center; margin-top: 14px; line-height: 1.7; }
    .foot code {
        color: __SLATE__; background: __SOFT__; border: 1px solid __BORDER__;
        padding: 1px 7px; border-radius: 9999px; font-family: __FONTMONO__;
    }
    .err-title { font-size: 18px; font-weight: 700; color: __ERR__; letter-spacing: -0.3px; }
    .err-msg { font-size: 14px; color: __INK__; margin-top: 8px; line-height: 1.5; }
    """

    def __init__(self, sdk, config: Dict):
        self.sdk = sdk
        self.logger = sdk.logger.get_child("HelpNext.Visualizer")
        self.config = config
        self._takumi_inst = None

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
        mode = self.config.get("theme", "auto")
        if mode == "auto":
            offset = self.config.get("utc_offset", 8)
            hour = int((time.time() / 3600 + offset) % 24)
            mode = "dark" if (hour >= 19 or hour < 7) else "light"
        if mode == "dark":
            return {
                "page": "#0a0a0a", "card": "#181e25", "ink": "#ffffff",
                "slate": "#a8aab2", "steel": "#8e8e93", "muted": "#7c8087",
                "sep": "rgba(255,255,255,0.08)", "border": "rgba(255,255,255,0.10)",
                "soft": "rgba(255,255,255,0.06)", "codebg": "rgba(255,255,255,0.06)",
                "numbg": "#ffffff", "numfg": "#0a0a0a", "err": "#ff7a70",
            }
        return {
            "page": "#f7f8fa", "card": "#ffffff", "ink": "#0a0a0a",
            "slate": "#45515e", "steel": "#8e8e93", "muted": "#a8aab2",
            "sep": "#eaecf0", "border": "#e5e7eb",
            "soft": "#f7f8fa", "codebg": "#f2f3f5",
            "numbg": "#0a0a0a", "numfg": "#ffffff", "err": "#d45656",
        }

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
    def _text_lines(text: str, width: int, cjk_w: float = 13.0, latin_w: float = 7.5) -> int:
        w = sum(cjk_w if ord(c) > 0x2E80 else latin_w for c in str(text))
        return max(1, math.ceil(w / max(1, width)))

    @staticmethod
    def _aliases_of(name: str, info: Dict) -> List[str]:
        main_name = info.get("main_name", name)
        return [
            a for a, m in command.aliases.items()
            if m == main_name and a != main_name
        ]

    def _render(self, body_html: str, height: int) -> Optional[bytes]:
        takumi = self.takumi
        if takumi is None or not hasattr(takumi, "render_html"):
            self.logger.warning("Takumi 不可用，跳过图片渲染")
            return None
        css, _ = self._css()
        try:
            return takumi.render_html(
                body_html, stylesheets=[css],
                width=self.CARD_WIDTH, height=height, lang="zh-CN",
            )
        except Exception as e:
            self.logger.error(f"Takumi 渲染失败: {e}")
            return None

    def _card(self, inner: str) -> str:
        return f"<div class='card'>{inner}</div>"

    def _h_card(self, inner_h: int) -> int:
        return self._CARD_PAD_V * 2 + inner_h + self._CARD_BORDER + self._CARD_GAP

    def _total_height(self, block_heights: List[int], footer_h: int = 0) -> int:
        return self._PAGE_PAD * 2 + sum(block_heights) + footer_h + 16

    @staticmethod
    def _num_cols(count: int) -> int:
        if count <= 8:
            return 1
        if count <= 24:
            return 2
        return 3

    def _header(self, subtitle: str, chips_html: str) -> Tuple[str, int]:
        cfg = self.config
        show_logo = cfg.get("show_logo", True)
        title = cfg.get("header_title") or "ErisPulse"
        sub = cfg.get("header_subtitle") or subtitle

        logo_html = ""
        logo_h = 0
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
                logo_h = dh

        text_html = (
            f"<div class='head-text'><div class='title'>{self._esc(title)}</div>"
            f"<div class='subtitle'>{self._esc(sub)}</div></div>"
        )
        inner = (
            f"<div class='head-row'>{logo_html}{text_html}</div>"
            f"<div class='divider'></div>{chips_html}"
        )
        row_h = max(logo_h, 44)
        inner_h = row_h + 33 + 32
        return inner, inner_h

    def _chips(self, cmd_count: int, group_count: Optional[int] = None) -> str:
        s = (
            f"<div class='chips'>"
            f"<div class='chip'><b>{cmd_count}</b>{self._esc(self._t('chip_commands'))}</div>"
        )
        if group_count is not None:
            s += f"<div class='chip'><b>{group_count}</b>{self._esc(self._t('chip_groups'))}</div>"
        s += "</div>"
        return s

    def _command_card(
        self,
        cmd: Dict,
        idx: int,
        prefix: str,
        avail: int,
        show_group: bool = False,
    ) -> Tuple[str, int]:
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

        desc_html = f"<div class='cmd-desc'>{self._esc(desc)}</div>"
        desc_h = 8 + self._text_lines(desc, avail) * 20

        extra_html = ""
        extra_h = 0
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
            a_w = sum((len(prefix) + len(a)) * 7.5 + 18 + 6 for a in aliases)
            a_rows = max(1, math.ceil(a_w / max(1, avail)))
            extra_h += 8 + a_rows * 24
        if info.get("usage"):
            usage = info["usage"].replace("/", prefix)
            extra_html += f"<div class='cmd-usage'>{self._esc(usage)}</div>"
            extra_h += 22 + self._text_lines(usage, avail, cjk_w=12.5, latin_w=7.5) * 19

        inner = head + desc_html + extra_html
        inner_h = 24 + desc_h + extra_h
        return inner, inner_h

    def _masonry(self, items: List[Tuple[str, int]], num_cols: int) -> Tuple[str, int]:
        cols: List[List[str]] = [[] for _ in range(num_cols)]
        col_h = [0] * num_cols
        for html, inner_h in items:
            card_h = inner_h + self._CARD_PAD_V * 2 + self._CARD_BORDER
            c = min(range(num_cols), key=lambda i: col_h[i])
            cols[c].append(html)
            col_h[c] += card_h + self._COL_GAP
        heights = [max(0, ch - self._COL_GAP) for ch in col_h]
        inner = "".join(f"<div class='mcol'>{''.join(col)}</div>" for col in cols)
        return f"<div class='masonry'>{inner}</div>", max(heights)

    def render_help_list(
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

        num_cols = self._num_cols(len(commands))
        avail = int(
            (self.CARD_WIDTH - self._PAGE_PAD * 2 - self._COL_GAP * (num_cols - 1))
            / num_cols - self._CARD_PAD_H * 2 - 2
        )

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
        head_inner, head_h = self._header(self._t("title"), chips)

        items = []
        for i, cmd in enumerate(ordered, start=1):
            inner, inner_h = self._command_card(
                cmd, i, prefix, avail,
                show_group=group_commands,
            )
            items.append((self._card(inner), inner_h))

        masonry_html, masonry_h = self._masonry(items, num_cols)

        foot_lines = [self._t("command_count", count=len(commands))]
        if others:
            foot_lines.append(f"{self._t('other_prefixes')}: {'、'.join(others)}")
        footer = "<div class='foot'>" + "<br>".join(foot_lines) + "</div>"
        footer_h = 34 + (20 if others else 0)

        body = self._card(head_inner) + masonry_html + footer
        height = self._total_height([self._h_card(head_h), masonry_h], footer_h)
        return self._render(body, height)

    def render_command_detail(
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
        head_inner, head_h = self._header(self._t("detail_title"), chips)

        blocks = [(self._card(head_inner), self._h_card(head_h))]

        def add_card(label: str, value_html: str, value_h: int, value_class: str = ""):
            vc = f" {value_class}" if value_class else ""
            inner = (
                f"<div class='detail-label'>{self._esc(label)}</div>"
                f"<div class='detail-value{vc}'>{value_html}</div>"
            )
            blocks.append((self._card(inner), self._h_card(30 + value_h)))

        add_card(
            self._t("label_description"),
            self._esc(info.get("help") or self._t("no_description")),
            24,
        )

        aliases = self._aliases_of(name, info)
        if aliases:
            tags = "".join(
                f"<span class='alias-tag'>{self._esc(prefix)}{self._esc(a)}</span>"
                for a in aliases
            )
            add_card(self._t("label_aliases"), f"<div class='aliases'>{tags}</div>", 32)

        if info.get("usage"):
            add_card(
                self._t("label_usage"),
                self._esc(info["usage"].replace("/", prefix)),
                24,
                value_class="mono",
            )

        if info.get("permission"):
            add_card(
                self._t("label_permission"),
                self._esc(self._t("permission_required")),
                22,
                value_class="warn",
            )

        if info.get("group"):
            gname = self._t("group_default") if info["group"] == "default" else info["group"]
            add_card(self._t("label_group"), self._esc(gname), 22)

        footer, footer_h = "", 0
        if others:
            footer = (f"<div class='foot'>{self._t('other_prefixes')}: "
                      f"{'、'.join(self._esc(p) for p in others)}</div>")
            footer_h = 40

        body = "".join(h for h, _ in blocks) + footer
        height = self._total_height([b for _, b in blocks], footer_h)
        return self._render(body, height)

    def render_error(self, title: str, message: str) -> Optional[bytes]:
        head_inner, head_h = self._header(self._t("title"), "")
        err = (f"<div class='err-title'>{self._esc(title)}</div>"
               f"<div class='err-msg'>{self._esc(message)}</div>")
        blocks = [
            (self._card(head_inner), self._h_card(head_h)),
            (self._card(err), self._h_card(70)),
        ]
        body = "".join(h for h, _ in blocks)
        height = self._total_height([b for _, b in blocks])
        return self._render(body, height)
