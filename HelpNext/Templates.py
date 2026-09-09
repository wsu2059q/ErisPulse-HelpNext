from typing import Dict, List, Optional

from ErisPulse import i18n
from ErisPulse.Core.Event import command

class HelpTemplates:
    """i18n-aware fallback templates (html / markdown / text)."""

    INK = "#0a0a0a"
    SLATE = "#45515e"
    STEEL = "#8e8e93"
    MUTED = "#a8aab2"
    SOFT = "#f7f8fa"
    BORDER = "#e5e7eb"
    ERR = "#d45656"
    FONT = (
        "-apple-system,'Segoe UI',Roboto,'PingFang SC',"
        "'Microsoft YaHei','Noto Sans SC',sans-serif"
    )
    MONO = "'JetBrains Mono','Source Code Pro',Consolas,monospace"

    @classmethod
    def _t(cls, key: str, **kwargs) -> str:
        full = f"HelpNext.{key}"
        return i18n.t(full, default=full, **kwargs)

    @classmethod
    def _group_name(cls, group: str) -> str:
        if not group or group == "default":
            return cls._t("group_default")
        return group

    @classmethod
    def _aliases_of(cls, name: str, info: Dict) -> List[str]:
        main_name = info.get("main_name", name)
        return [
            alias
            for alias, mapped in command.aliases.items()
            if mapped == main_name and alias != main_name
        ]

    @classmethod
    def _other_prefixes(cls, prefixes: Optional[list], display: str) -> list:
        if not prefixes or len(prefixes) <= 1:
            return []
        return [p for p in prefixes if p != display]

    @classmethod
    def _code_chip(cls, text: str) -> str:
        return (
            f"<code style=\"font-family:{cls.MONO};font-size:12px;"
            f"background:{cls.SOFT};border:1px solid {cls.BORDER};"
            f"padding:2px 7px;border-radius:4px;color:{cls.INK};\">{text}</code>"
        )

    @classmethod
    def build_help_list(
        cls,
        commands: List[Dict],
        command_map: Dict[int, Dict],
        prefix: str,
        group_commands: bool = True,
        prefixes: Optional[list] = None,
    ) -> Dict[str, str]:
        others = cls._other_prefixes(prefixes or [prefix], prefix)
        grouped = cls._group(commands, group_commands)

        global_idx = 1
        for _, cmds in grouped.items():
            for cmd in cmds:
                command_map[global_idx] = cmd
                global_idx += 1

        return {
            "html": cls._list_html(commands, grouped, command_map, prefix, others),
            "markdown": cls._list_md(commands, grouped, command_map, prefix, others),
            "text": cls._list_text(commands, grouped, command_map, prefix, others),
        }

    @staticmethod
    def _group(commands: List[Dict], group_commands: bool) -> Dict[str, List[Dict]]:
        if not group_commands:
            return {"default": list(commands)}
        grouped: Dict[str, List[Dict]] = {}
        for cmd in commands:
            g = cmd["info"].get("group") or "default"
            grouped.setdefault(g, []).append(cmd)
        return grouped

    @classmethod
    def _list_html(cls, commands, grouped, command_map, prefix, others) -> str:
        title = cls._t("title")
        hint = cls._t("usage_hint", prefix=prefix)
        count = cls._t("command_count", count=len(commands))

        sections = ""
        for group, cmds in grouped.items():
            sections += (
                f'<div style="font-size:12px;font-weight:700;letter-spacing:0.5px;'
                f'color:{cls.STEEL};margin:16px 0 8px;">{cls._group_name(group)}</div>'
            )
            for cmd in cmds:
                idx = next(
                    i for i, c in command_map.items() if c["name"] == cmd["name"]
                )
                name = cmd["name"]
                help_text = cmd["info"].get("help") or cls._t("no_description")
                sections += (
                    f'<div style="margin-bottom:8px;font-size:13px;line-height:1.5;">'
                    f'<span style="color:{cls.STEEL};font-weight:600;margin-right:8px;'
                    f'font-variant-numeric:tabular-nums;">{idx}</span>'
                    f'{cls._code_chip(prefix + name)}'
                    f'<span style="color:{cls.SLATE};margin-left:8px;">{help_text}</span></div>'
                )

        others_html = cls._prefix_note_html(others)
        return (
            f'<div style="font-family:{cls.FONT};color:{cls.INK};padding:4px 2px;">'
            f'<div style="font-size:16px;font-weight:700;letter-spacing:-0.3px;'
            f'margin-bottom:12px;">{title}</div>'
            f'<div style="padding:8px 12px;background:{cls.SOFT};'
            f'border:1px solid {cls.BORDER};border-radius:8px;margin-bottom:4px;'
            f'font-size:13px;color:{cls.SLATE};">{hint}</div>'
            f'{sections}'
            f'<div style="font-size:12px;color:{cls.STEEL};margin-top:14px;">{count}</div>'
            f'{others_html}'
            f'</div>'
        )

    @classmethod
    def _list_md(cls, commands, grouped, command_map, prefix, others) -> str:
        lines = [
            f"**{cls._t('title')}**",
            "",
            cls._t("usage_hint", prefix=prefix),
            "",
        ]
        for group, cmds in grouped.items():
            lines.append(f"**{cls._group_name(group)}**")
            lines.append("")
            for cmd in cmds:
                idx = next(i for i, c in command_map.items() if c["name"] == cmd["name"])
                help_text = cmd["info"].get("help") or cls._t("no_description")
                lines.append(f"{idx}. `{prefix}{cmd['name']}` - {help_text}")
            lines.append("")

        lines.append("---")
        lines.append(cls._t("command_count", count=len(commands)))
        if others:
            lines.append("")
            lines.append(f"{cls._t('other_prefixes')}: {'、'.join(others)}")
        return "\n".join(lines)

    @classmethod
    def _list_text(cls, commands, grouped, command_map, prefix, others) -> str:
        lines = [
            cls._t("title"),
            "----------",
            cls._t("usage_hint", prefix=prefix),
            "",
        ]
        for group, cmds in grouped.items():
            lines.append(f"[{cls._group_name(group)}]")
            lines.append("")
            for cmd in cmds:
                idx = next(i for i, c in command_map.items() if c["name"] == cmd["name"])
                help_text = cmd["info"].get("help") or cls._t("no_description")
                lines.append(f"{idx}. {prefix}{cmd['name']} - {help_text}")
            lines.append("")

        lines.append("----------")
        lines.append(cls._t("command_count", count=len(commands)))
        if others:
            lines.append("")
            lines.append(f"{cls._t('other_prefixes')}: {'、'.join(others)}")
        return "\n".join(lines)

    @classmethod
    def _prefix_note_html(cls, others) -> str:
        if not others:
            return ""
        note = "、".join(f"<code style='font-family:{cls.MONO};font-size:11px;'>{p}</code>" for p in others)
        return (
            f'<div style="font-size:11px;color:{cls.MUTED};margin-top:6px;">'
            f'{cls._t("other_prefixes")}: {note}</div>'
        )

    @classmethod
    def build_command_detail(cls, cmd: Dict, prefix: str, prefixes: Optional[list] = None) -> Dict[str, str]:
        others = cls._other_prefixes(prefixes or [prefix], prefix)
        return {
            "html": cls._detail_html(cmd, prefix, others),
            "markdown": cls._detail_md(cmd, prefix, others),
            "text": cls._detail_text(cmd, prefix, others),
        }

    @classmethod
    def _detail_html(cls, cmd: Dict, prefix: str, others) -> str:
        name = cmd["name"]
        info = cmd["info"]
        title = cls._t("detail_title")
        parts = [
            f'<div style="font-family:{cls.FONT};color:{cls.INK};padding:4px 2px;">'
            f'<div style="font-size:16px;font-weight:700;letter-spacing:-0.3px;'
            f'margin-bottom:14px;">{title} {cls._code_chip(prefix + name)}</div>'
        ]

        parts.append(cls._kv_html(cls._t("label_description"),
                                  info.get("help") or cls._t("no_description")))

        aliases = cls._aliases_of(name, info)
        if aliases:
            parts.append(cls._kv_html(cls._t("label_aliases"),
                                      ", ".join(f"{prefix}{a}" for a in aliases)))

        if info.get("usage"):
            parts.append(cls._kv_html(cls._t("label_usage"),
                                      info["usage"].replace("/", prefix), mono=True))

        if info.get("permission"):
            parts.append(cls._kv_html(cls._t("label_permission"),
                                      cls._t("permission_required"), warn=True))

        if info.get("group"):
            parts.append(cls._kv_html(cls._t("label_group"),
                                      cls._group_name(info["group"])))

        if others:
            parts.append(cls._prefix_note_html(others))

        parts.append("</div>")
        return "\n".join(parts)

    @classmethod
    def _kv_html(cls, label: str, value: str, mono: bool = False, warn: bool = False) -> str:
        color = cls.ERR if warn else cls.INK
        style = (
            f"font-family:{cls.MONO};background:{cls.SOFT};"
            f"border:1px solid {cls.BORDER};padding:6px 10px;border-radius:6px;"
            if mono else ""
        )
        return (
            f'<div style="margin-bottom:10px;">'
            f'<div style="font-size:11px;font-weight:600;letter-spacing:0.5px;'
            f'text-transform:uppercase;color:{cls.STEEL};margin-bottom:4px;">{label}</div>'
            f'<div style="font-size:13px;line-height:1.5;color:{color};{style}">{value}</div></div>'
        )

    @classmethod
    def _detail_md(cls, cmd: Dict, prefix: str, others) -> str:
        name = cmd["name"]
        info = cmd["info"]
        lines = [
            f"**{cls._t('detail_title')}:** `{prefix}{name}`",
            "",
            f"**{cls._t('label_description')}:** {info.get('help') or cls._t('no_description')}",
            "",
        ]
        aliases = cls._aliases_of(name, info)
        if aliases:
            lines.append(f"**{cls._t('label_aliases')}:** {', '.join(f'`{prefix}{a}`' for a in aliases)}")
            lines.append("")
        if info.get("usage"):
            lines.append(f"**{cls._t('label_usage')}:** `{info['usage'].replace('/', prefix)}`")
            lines.append("")
        if info.get("permission"):
            lines.append(f"**{cls._t('label_permission')}:** {cls._t('permission_required')}")
            lines.append("")
        if info.get("group"):
            lines.append(f"**{cls._t('label_group')}:** {cls._group_name(info['group'])}")
            lines.append("")
        if others:
            lines.append(f"{cls._t('other_prefixes')}: {'、'.join(others)}")
        return "\n".join(lines)

    @classmethod
    def _detail_text(cls, cmd: Dict, prefix: str, others) -> str:
        name = cmd["name"]
        info = cmd["info"]
        lines = [
            f"{cls._t('detail_title')}: {prefix}{name}",
            "----------",
            f"{cls._t('label_description')}: {info.get('help') or cls._t('no_description')}",
            "",
        ]
        aliases = cls._aliases_of(name, info)
        if aliases:
            lines.append(f"{cls._t('label_aliases')}: {', '.join(f'{prefix}{a}' for a in aliases)}")
            lines.append("")
        if info.get("usage"):
            lines.append(f"{cls._t('label_usage')}: {info['usage'].replace('/', prefix)}")
            lines.append("")
        if info.get("permission"):
            lines.append(f"{cls._t('label_permission')}: {cls._t('permission_required')}")
            lines.append("")
        if info.get("group"):
            lines.append(f"{cls._t('label_group')}: {cls._group_name(info['group'])}")
            lines.append("")
        if others:
            lines.append(f"{cls._t('other_prefixes')}: {'、'.join(others)}")
        return "\n".join(lines)

    @classmethod
    def build_error(cls, title: str, message: str) -> Dict[str, str]:
        html = (
            f'<div style="font-family:{cls.FONT};padding:4px 2px;">'
            f'<div style="font-size:14px;font-weight:700;letter-spacing:-0.2px;'
            f'color:{cls.ERR};margin-bottom:8px;">{title}</div>'
            f'<div style="font-size:13px;line-height:1.5;color:{cls.SLATE};">'
            f'{message}</div></div>'
        )
        markdown = f"**{title}**\n\n{message}"
        text = f"{title}\n\n{message}"
        return {"html": html, "markdown": markdown, "text": text}
