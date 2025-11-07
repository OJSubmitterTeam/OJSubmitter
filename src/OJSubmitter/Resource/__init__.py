import os
from typing import Any, Dict

from typing_extensions import Self

from ..Constant.defaults import EMPTY_RESOURCE
from ..Constant.resource import RESOURCE_PATH
from ..Models.resource import ResourceParams


class Resource:
    _instances: Dict[str, Self] = {}

    def __new__(cls, path: str = RESOURCE_PATH) -> Self:
        if path not in cls._instances:
            cls._instances[path] = super(Resource, cls).__new__(cls)
        return cls._instances[path]

    def __init__(self, path: str = RESOURCE_PATH) -> None:
        self.path = path
        if not os.path.exists(self.path):
            os.makedirs(self.path.replace("\\", "/").rsplit("/", 1)[0], exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(EMPTY_RESOURCE.model_dump_json(indent=4))

        self.load()

    @property
    def resource(self) -> ResourceParams:
        return self._resource

    @property
    def local_config(self) -> Dict[str, Any]:
        return self._resource.local_config

    def local_config_get(self, key: str, default: Any = None) -> Any:
        return self.local_config.get(key, default)

    def local_config_set(self, key: str, value: Any) -> None:
        self.local_config[key] = value
        self.save()

    def update_local_config(self, configs: Dict[str, Any]) -> None:
        self.local_config.update(configs)
        self.save()

    def save(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(self._resource.model_dump_json(indent=4))

    def load(self) -> None:
        with open(self.path, "r", encoding="utf-8") as f:
            text = f.read()
        try:
            self._resource = ResourceParams.model_validate_json(text)
        except Exception:
            self._resource = EMPTY_RESOURCE
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    f.write(self._resource.model_dump_json(indent=4))
            except Exception:
                pass

    def reset(self) -> None:
        self._resource = EMPTY_RESOURCE
        self.save()

    def __repr__(self) -> str:
        return f"Resource(path={self.path}, resource={self._resource})"


instance = Resource()


__all__ = ["Resource", "instance"]
