from typing import TypeAlias

JsonType: TypeAlias = (
    dict[str, 'JsonType'] | list['JsonType'] | str | int | float | bool | None
)
