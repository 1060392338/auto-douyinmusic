"""Pipeline 抽象基类模块

定义所有 Pipeline 必须实现的接口规范。
"""

from abc import ABC, abstractmethod


class BasePipeline(ABC):
    """Pipeline 抽象基类。

    所有具体的 Pipeline 实现必须继承此类并实现 run() 方法。

    Attributes:
        tenant: TenantConfig 实例，包含租户级别的配置信息。
    """

    def __init__(self, tenant):
        """初始化 BasePipeline。

        Args:
            tenant: TenantConfig 实例。
        """
        self.tenant = tenant

    @abstractmethod
    def run(self) -> dict:
        """执行 Pipeline 的核心逻辑。

        Returns:
            dict: Pipeline 执行结果，具体结构由子类定义。
        """
        ...
