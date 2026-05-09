"""歌曲相关的数据模型"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Lyrics:
    """歌词数据模型"""
    raw_text: str = ""
    structure: dict = field(default_factory=dict)
    is_refined: bool = False


@dataclass
class CompositionPrompt:
    """作曲提示数据模型"""
    style_description: str = ""
    lyrics: Optional[Lyrics] = None
    external_prompt: str = ""


@dataclass
class MusicAsset:
    """音乐资产数据模型"""
    asset_id: str = ""
    name: str = ""
    duration_seconds: float = 0.0


@dataclass
class Song:
    """歌曲数据模型"""
    title: str = ""
    lyrics: Optional[Lyrics] = None
    music_assets: list = field(default_factory=list)
    audio_file_path: str = ""
    cover_image_path: str = ""


@dataclass
class PublishInfo:
    """发布信息数据模型"""
    song_title: str = ""
    lyrics_text: str = ""
    cover_image_path: str = ""
    contract_type: str = ""
    success: bool = False
    error: str = ""
    publish_url: str = ""
