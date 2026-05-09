"""配置加载模块

从 config.yaml 和 .env 文件加载配置，提供配置数据模型和便捷的配置获取接口。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

# ── 项目根目录 ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── 配置数据模型 ─────────────────────────────────────────────────────────────
@dataclass
class BrowserConfig:
    """浏览器配置"""
    chrome_port: int = 9223
    user_data_dir: str = ""


@dataclass
class PlatformConfig:
    """平台配置"""
    publisher: str = ""
    studio_url: str = ""
    chrome_data: str = ""
    phone: str = ""
    password: str = ""


@dataclass
class CreationConfig:
    """创作配置"""
    default_style: str = ""
    default_theme: str = ""
    export_mode: str = "轨道合并"
    export_sub_style: str = ""


@dataclass
class TenantConfig:
    """租户配置"""
    id: str = ""
    enabled: bool = False
    platform: str = ""
    account: str = ""
    display_name: str = ""
    config: Optional[BrowserConfig] = None
    platform_config: Optional[PlatformConfig] = None
    creation_config: Optional[CreationConfig] = None

    # 原始 dict 字段（在 __post_init__ 中转换）
    _raw_config: Optional[dict] = None
    _raw_platform_config: Optional[dict] = None
    _raw_creation_config: Optional[dict] = None

    def __post_init__(self):
        # 从原始 dict 转换为对应的数据模型
        if self._raw_config is not None and self.config is None:
            self.config = BrowserConfig(**self._raw_config)
        if self._raw_platform_config is not None and self.platform_config is None:
            self.platform_config = PlatformConfig(**self._raw_platform_config)
        if self._raw_creation_config is not None and self.creation_config is None:
            self.creation_config = CreationConfig(**self._raw_creation_config)


# ── 配置加载 ─────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """加载 config.yaml + .env，返回合并后的完整配置字典。

    Returns:
        dict: 包含 'global' 和 'tenants' 两个顶级键的配置字典。
    """
    # 加载 .env 文件
    dotenv_path = PROJECT_ROOT / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)

    # 加载 config.yaml
    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_tenant(tenant_id: str) -> Optional[TenantConfig]:
    """根据租户 ID 获取租户配置。

    Args:
        tenant_id: 租户 ID，对应 config.yaml 中 tenants[].id。

    Returns:
        TenantConfig 实例，如果未找到则返回 None。
    """
    config = load_config()
    tenants = config.get("tenants", [])

    for tenant_data in tenants:
        if tenant_data.get("id") == tenant_id:
            return TenantConfig(
                id=tenant_data.get("id", ""),
                enabled=tenant_data.get("enabled", False),
                platform=tenant_data.get("platform", ""),
                account=tenant_data.get("account", ""),
                display_name=tenant_data.get("display_name", ""),
                _raw_config=tenant_data.get("config"),
                _raw_platform_config=tenant_data.get("platform_config"),
                _raw_creation_config=tenant_data.get("creation_config"),
            )

    return None
