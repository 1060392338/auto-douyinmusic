"""Pipeline 工厂模块

提供 Pipeline 注册和获取机制，支持按类型创建不同的执行管道。
自动导入 pipelines 包下的所有子模块，确保 @register 装饰器被执行。
"""

import importlib
import pkgutil

PIPELINE_MAP = {}


def register(pipeline_type: str):
    """注册 Pipeline 类的装饰器。

    Args:
        pipeline_type: Pipeline 类型标识，如 "music_creation"。

    Returns:
        decorator: 将 Pipeline 类注册到 PIPELINE_MAP 的装饰器。
    """

    def decorator(cls):
        PIPELINE_MAP[pipeline_type] = cls
        return cls

    return decorator


def _auto_import_modules():
    """自动导入 pipelines 包下的所有子模块，确保 @register 被执行"""
    pkg_path = __path__[0]
    for _, module_name, _ in pkgutil.iter_modules([pkg_path]):
        if module_name != "__init__":
            importlib.import_module(f".{module_name}", __package__)


def get_pipeline(pipeline_type: str, tenant):
    """根据类型获取 Pipeline 实例。

    Args:
        pipeline_type: Pipeline 类型标识。
        tenant: TenantConfig 实例，传递给 Pipeline 构造函数。

    Returns:
        BasePipeline 子类实例。

    Raises:
        ValueError: 如果指定的 pipeline_type 未注册。
    """
    cls = PIPELINE_MAP.get(pipeline_type)
    if not cls:
        raise ValueError(
            f"未知的 Pipeline 类型: '{pipeline_type}'，"
            f"可用类型: {list(PIPELINE_MAP.keys())}"
        )
    return cls(tenant)


# ── 启动时自动注册所有 Pipeline 模块 ───────────────────────────────────────
_auto_import_modules()
