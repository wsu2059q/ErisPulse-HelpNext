from typing import Dict, List, Optional

from ErisPulse import i18n
from ErisPulse.Core.Event import command

class HelpTemplates:
    """i18n-aware fallback templates (html / markdown / text)."""

    PRIMARY_COLOR = "#0071e3"
    WARNING_COLOR = "#ff9f0a"
    ERROR_COLOR = "#ff453a"
    PRIMARY_BG = "rgba(0, 113, 227, 0.06)"

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
                f'<div style="font-size:13px;margin-bottom:8px;font-weight:600;'
                f'color:{cls.PRIMARY_COLOR};">{cls._group_name(group)}</div>'
            )
            for cmd in cmds:
                idx = next(
                    i for i, c in command_map.items() if c["name"] == cmd["name"]
                )
                name = cmd["name"]
                help_text = cmd["info"].get("help") or cls._t("no_description")
                sections += (
                    f'<div style="margin-bottom:6px;font-size:13px;">'
                    f'<b style="margin-right:6px;">{idx}.</b>'
                    f'<code style="background:rgba(0,0,0,0.05);padding:2px 6px;'
                    f'border-radius:4px;margin-right:6px;">{prefix}{name}</code>'
                    f'<span style="color:#666;">- {help_text}</span></div>'
                )
            sections += "\n"

        others_html = cls._prefix_note_html(others)
        return (
            f'<div style="padding:12px;border-radius:8px;">'
            f'<div style="color:{cls.PRIMARY_COLOR};font-size:16px;font-weight:700;'
            f'margin-bottom:12px;">{title}</div>'
            f'<div style="padding:8px;background:{cls.PRIMARY_BG};border-radius:6px;'
            f'margin-bottom:12px;font-size:13px;">{hint}</div>'
            f'{sections}'
            f'<div style="font-size:12px;color:#666;margin-top:8px;">{count}</div>'
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
        note = "、".join(f"<code style='font-size:11px;'>{p}</code>" for p in others)
        return (
            f'<div style="font-size:11px;color:#999;margin-top:4px;">'
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
            f'<div style="padding:12px;border-radius:8px;">'
            f'<div style="color:{cls.PRIMARY_COLOR};font-size:16px;font-weight:700;'
            f'margin-bottom:12px;">{title}: <code style="background:rgba(0,0,0,0.05);'
            f'padding:2px 6px;border-radius:4px;">{prefix}{name}</code></div>'
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
        color = cls.WARNING_COLOR if warn else "inherit"
        style = "font-family:monospace;background:rgba(0,0,0,0.03);padding:2px 6px;border-radius:4px;" if mono else ""
        return (
            f'<div style="margin-bottom:8px;">'
            f'<div style="font-size:13px;margin-bottom:4px;"><b>{label}:</b></div>'
            f'<div style="font-size:13px;color:{color};{style}">{value}</div></div>'
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
            f'<div style="padding:12px;border-radius:8px;">'
            f'<div style="color:{cls.ERROR_COLOR};font-size:14px;font-weight:700;'
            f'margin-bottom:8px;">{title}</div>'
            f'<div style="font-size:13px;">{message}</div></div>'
        )
        markdown = f"**{title}**\n\n{message}"
        text = f"{title}\n\n{message}"
        return {"html": html, "markdown": markdown, "text": text}
