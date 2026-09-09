import asyncio
import time

DISPLAY = "Moe"

LIGHT = {
    "page": "#ffe9f3", "card": "#ffffff", "ink": "#5c4a55",
    "slate": "#8f7c87", "steel": "#b6a2ad", "muted": "#d9c8d1",
    "sep": "#f9e6ef", "border": "#ffd9ea",
    "soft": "#fff2f8", "codebg": "#f6f1fb",
    "numbg": "#ff9ec6", "numfg": "#ffffff", "err": "#f27d98",
}

DARK = {
    "page": "#171216", "card": "#251c22", "ink": "#f7edf3",
    "slate": "#cdb4c0", "steel": "#9c8791", "muted": "#74626c",
    "sep": "rgba(255,158,198,0.10)", "border": "rgba(255,158,198,0.18)",
    "soft": "rgba(255,158,198,0.08)", "codebg": "rgba(170,190,255,0.10)",
    "numbg": "#ff9ec6", "numfg": "#3a2530", "err": "#ff9fb4",
}

CSS_EXTRA = """
.chip b { color: #ff8fbf; }
.card { border-radius: 22px; }
"""

_MASCOT_APIS = [
    "https://www.loliapi.com/acg/",
    "https://api.paugram.com/wallpaper/",
    "https://www.dmoe.cc/random.php",
]

_HEAD_CSS = """
.hn-head { margin-bottom: 14px; }
.hn-hero { position: relative; border-radius: 22px; overflow: hidden; }
.hn-hero > img {
    position: absolute; left: 0; top: 0;
    width: 100%; height: 100%;
    object-fit: cover; object-position: center top;
}
.hn-hero-bar {
    position: absolute; left: 0; right: 0; bottom: 0;
    background: __SCRIM__;
    padding: 14px 20px;
    display: flex; align-items: center; gap: 12px;
}
.hn-hero-bar .head-row { flex: 1; min-width: 0; }
.hn-head .chips { justify-content: center; margin-top: 14px; }
.hn-hero-bar .chips { margin: 0 0 0 auto; flex: 0 0 auto; gap: 8px; }
.hn-hero-bar .chip { padding: 5px 12px; font-size: 12px; }
"""

_PAGE_CSS = """
.page { position: relative; }
.hn-page-bg {
    position: absolute; left: 0; top: 0; right: 0; bottom: 0;
    border-radius: 22px; overflow: hidden;
}
.hn-page-bg img {
    position: absolute; left: 0; top: 0;
    width: 100%; height: 100%;
    object-fit: cover; object-position: center top;
}
.hn-page-bg .hn-page-tint {
    position: absolute; left: 0; top: 0; right: 0; bottom: 0;
    background: __WASH__;
}
.hn-page-content { position: relative; }
"""

# 头图高度按图片宽高比自适应的边界
_COVER_W = 808.0   # 内容区宽度（CARD_WIDTH - 页面内边距）
_MIN_H = 220.0
_MAX_H = 520.0
_TTL = 600.0       # 萌图缓存时长（秒），到期后借下一次渲染顺手刷新


class Theme:
    """Moe 主题行为：随机萌图头图 + 同图页面背景。

    激活主题后同步拉取一张萌图（多源容灾）作为整个头部的背景铺满展示：
    ErisPulse 标题行叠加在图片底部的透白色衬底上，头部不套卡片；
    同一张图以浓纱罩染铺在整页背景上（隐约透出纹理，命令保持可读），
    命令卡片与头部自然融合。缓存过期后借下一次渲染顺手刷新
    （fire-and-forget，无后台常驻任务）；API 不可用时自动隐藏，不影响渲染。
    """

    def __init__(self):
        self._sdk = None
        self._mascot_data = None  # 原始图片字节（经渲染资源注入，不内联进 HTML）
        self._mascot_size = None  # (w, h)
        self._last_fetch = 0.0
        self._refreshing = False

    async def on_attach(self, sdk) -> None:
        self._sdk = sdk
        # 首次同步拉取：保证挂载后的第一次渲染就有头图
        if self._mascot_data is None:
            await self._refresh_mascot()

    async def on_detach(self) -> None:
        return None

    def images(self):
        """渲染资源协议：返回 [(name, bytes), ...]，经 takumi images 参数注入。"""
        if self._mascot_data is None:
            return []
        return [("memory://mascot", self._mascot_data)]

    def _extract_chips(self, body: str):
        """从头图后的内容中摘出 chips 块，返回 (chips_html, 移除后的 body)。"""
        start = body.find("<div class='chips'>")
        if start < 0:
            return None, body
        i, depth, n = start, 0, len(body)
        while i < n:
            m_open = body.find("<div", i)
            m_close = body.find("</div>", i)
            if m_close < 0:
                return None, body
            if 0 <= m_open < m_close:
                depth += 1
                i = m_open + 4
            else:
                depth -= 1
                i = m_close + 6
                if depth == 0:
                    return body[start:i], body[:start] + body[i:]
        return None, body

    def decorate(self, ctx: dict, sdk) -> None:
        dark = ctx["theme"].get("mode") == "dark"
        scrim = "rgba(23,18,22,0.72)" if dark else "rgba(255,255,255,0.78)"
        # 页面纱与命令卡片均为透白（简洁玻璃感），深色模式对应暗纱
        wash = "rgba(23,18,22,0.78)" if dark else "rgba(255,255,255,0.72)"
        card_bg = "rgba(37,28,34,0.82)" if dark else "rgba(255,255,255,0.82)"
        ctx["css"] += _HEAD_CSS.replace("__SCRIM__", scrim)
        ctx["css"] += _PAGE_CSS.replace("__WASH__", wash)
        ctx["css"] += f".card{{background:{card_bg}}}"
        self._maybe_refresh()

        if ctx["kind"] != "help_list" or self._mascot_data is None:
            return
        body = ctx["body"]
        # 头图高度按图片宽高比自适应：横图完整展示，竖图限高并从顶部裁切
        hero_style = ""
        if self._mascot_size:
            w, h = self._mascot_size
            if w > 0:
                hero_h = int(min(max(_COVER_W * h / w, _MIN_H), _MAX_H))
                hero_style = f" style='height:{hero_h}px'"
        # 原子注入：萌图铺满头部，标题行叠加在图片底部的透白色衬底上；
        # 开标签与闭标签配平，任一未命中则整体放弃，避免半注入破坏结构
        opened = body.replace(
            "<div class='card'><div class='head-row'>",
            f"<div class='hn-head'><div class='hn-hero'{hero_style}>"
            f"<img src='memory://mascot'/>"
            f"<div class='hn-hero-bar'><div class='head-row'>",
            1,
        )
        if opened != body:
            # 摘出 chips 块，移入遮罩条（标题行右侧）；同时去掉头图与命令区之间的小横线
            chips, opened = self._extract_chips(opened)
            if chips:
                tail = "</div>" + chips + "</div></div>"
            else:
                tail = "</div></div>"
            opened = opened.replace(
                "</div><div class='divider'></div>",
                tail,
                1,
            )
            # 整页背景铺同一张萌图（浓纱罩染）：内容移入 hn-page-content，
            # 背景层垫底；结尾补齐 content 与 page 的闭合标签
            paged = opened.replace(
                "<div class='page'>",
                "<div class='page'><div class='hn-page-bg'>"
                "<img src='memory://mascot'/>"
                "<div class='hn-page-tint'></div></div>"
                "<div class='hn-page-content'>",
                1,
            )
            if paged != opened and paged.endswith("</div>"):
                opened = paged[:-6] + "</div></div>"
            ctx["body"] = opened

    def _maybe_refresh(self) -> None:
        """缓存过期时借当前渲染的异步上下文顺手刷新（不阻塞、不常驻）。"""
        if self._refreshing or not self._sdk:
            return
        if self._mascot_data is not None and time.time() - self._last_fetch < _TTL:
            return
        self._refreshing = True

        async def _job():
            try:
                await self._refresh_mascot()
            finally:
                self._refreshing = False

        asyncio.create_task(_job())

    async def _refresh_mascot(self):
        client = getattr(self._sdk, "client", None)
        if client is None:
            return
        for url in _MASCOT_APIS:
            try:
                resp = await client.get(url, timeout=8)
                if resp.status != 200:
                    continue
                data = await resp.read()
                if not data or len(data) > 6 * 1024 * 1024:
                    continue
                self._mascot_size = self._img_dims(data)
                self._mascot_data = data
                self._last_fetch = time.time()
                return
            except Exception as e:
                self._sdk.logger.debug(e)
                continue

    @staticmethod
    def _img_dims(data: bytes):
        """解析 PNG / JPEG / WebP 像素尺寸，失败返回 None。"""
        try:
            if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
                w = int.from_bytes(data[16:20], "big")
                h = int.from_bytes(data[20:24], "big")
                return (w, h) if w and h else None
            if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
                chunk = data[12:16]
                if chunk == b"VP8 ":
                    w = int.from_bytes(data[26:28], "little") & 0x3FFF
                    h = int.from_bytes(data[28:30], "little") & 0x3FFF
                    return (w, h) if w and h else None
                if chunk == b"VP8L":
                    bits = int.from_bytes(data[21:25], "little")
                    w = (bits & 0x3FFF) + 1
                    h = ((bits >> 14) & 0x3FFF) + 1
                    return (w, h)
                if chunk == b"VP8X":
                    w = int.from_bytes(data[24:27], "little") + 1
                    h = int.from_bytes(data[27:30], "little") + 1
                    return (w, h)
            if data[:2] == b"\xff\xd8":  # JPEG: 扫描 SOF 段
                i, n = 2, len(data)
                sof = set(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}
                while i + 9 < n:
                    if data[i] != 0xFF:
                        i += 1
                        continue
                    marker = data[i + 1]
                    if marker in sof:
                        h = int.from_bytes(data[i + 5:i + 7], "big")
                        w = int.from_bytes(data[i + 7:i + 9], "big")
                        return (w, h) if w and h else None
                    if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                        i += 2
                        continue
                    seg_len = int.from_bytes(data[i + 2:i + 4], "big")
                    if seg_len < 2:
                        return None
                    i += 2 + seg_len
        except Exception:
            pass
        return None
