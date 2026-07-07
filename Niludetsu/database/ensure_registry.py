from typing import Any, Callable, Dict, Tuple

KeyBuilder = Callable[..., Dict[str, Any]]
DefaultsBuilder = Callable[..., Dict[str, Any]]

class EnsureRegistry:
    """Минимальный реестр схем для ensure_record()."""

    def __init__(self) -> None:
        self._configs: Dict[str, Dict[str, Callable[..., Dict[str, Any]]]] = {}

    def register(
        self,
        table: str,
        *,
        keys_builder: KeyBuilder,
        defaults_builder: DefaultsBuilder,
    ) -> None:
        self._configs[table] = {
            "keys": keys_builder,
            "defaults": defaults_builder,
        }

    def resolve(self, table: str, **params) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        config = self._configs.get(table)
        if not config:
            raise ValueError(f"EnsureRegistry: нет конфигурации для таблицы '{table}'")
        keys = config["keys"](**params)
        defaults = config["defaults"](**params)
        return keys, defaults

