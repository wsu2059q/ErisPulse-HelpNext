"""
HelpNext 内置主题包

每个主题文件（``themes/<name>.py``）声明以下模块级常量：

- ``DISPLAY``: 展示名（用于配置界面）
- ``LIGHT`` / ``DARK``: 色板令牌字典
  （page / card / ink / slate / steel / muted / sep / border / soft /
   codebg / numbg / numfg / err）
- ``CSS_EXTRA``: 可选的附加 CSS（主题个性化，如更大的圆角）
- ``Theme``: 可选的行为类，让主题定义渲染行为（如插入头图）。
  协议：``async on_attach(sdk)`` / ``async on_detach()`` /
  ``decorate(ctx, sdk)``（ctx 含 {kind, theme, config}，可就地修改
  ctx["body"] / ctx["css"]）

"""

import importlib
import pkgutil
from typing import Dict, List

THEMES: Dict[str, Dict] = {}


def _load() -> None:
    for mod_info in pkgutil.iter_modules(__path__):
        if mod_info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{mod_info.name}")
        THEMES[mod_info.name] = {
            "display": getattr(mod, "DISPLAY", mod_info.name),
            "light": getattr(mod, "LIGHT", {}),
            "dark": getattr(mod, "DARK", {}),
            "css_extra": getattr(mod, "CSS_EXTRA", ""),
            "behavior": getattr(mod, "Theme", None),
        }


_load()


def get_theme(name: str) -> Dict:
    return THEMES.get(name) or THEMES["default"]


def theme_names() -> List[str]:
    return list(THEMES.keys())


def theme_options() -> List[Dict]:
    return [
        # label 使用纯文本（主题展示名为动态加载，无 i18n 键）；
        # 若用 {"default": ...} 字典，旧版框架 schema 解析不会还原为文本，
        # 面板会渲染成 [object Object]
        {"value": name, "label": str(spec["display"])}
        for name, spec in THEMES.items()
    ]
