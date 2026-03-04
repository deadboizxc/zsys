# -*- coding: utf-8 -*-
"""ZSYS Utils — general-purpose utilities for the zsys framework.

Aggregates filesystem, terminal, media, git, version, text, time, hash, and HTTP
helper modules into a single flat namespace for convenient importing.
See submodule docstrings for individual API documentation.
"""
# RU: Пакет вспомогательных утилит zsys — агрегирует модули файловой системы,
# RU: терминала, медиа, git, версий, текста, времени, хеширования и HTTP в одно пространство имён.

# Filesystem utilities
from .filesystem import (
    ensure_dir,
    get_ffmpeg_paths,
    get_frozen_info,
    get_home_dir,
    get_platform_info,
    get_project_root,
    get_temp_dir,
    is_android,
    is_frozen,
    is_termux,
    resource_path,
    set_project_root,
    userdata_path,
)

# Git utilities
from .git import (
    GitHubAPI,
    get_commit_hash,
    get_current_branch,
    git_checkout,
    git_fetch,
    git_pull,
    git_rebase,
    is_git_repo,
    run_command,
)

# Hash utilities
from .hash import (
    hash_file,
    hash_file_sync,
    hash_string,
    md5_hash,
    sha256_hash,
    sha512_hash,
)

# HTTP utilities
from .http import (
    download_file,
    fetch_json,
    fetch_status,
    fetch_url,
    post_json,
)

# Media utilities
from .media import (
    PIL_AVAILABLE,
    get_ffmpeg,
    get_ffprobe,
    get_image_info,
    resize_image,
)

# Terminal utilities
from .terminal import (
    get_cpu_usage,
    get_ram_usage,
    shell_exec,
    shell_exec_sync,
)

# Text formatting
from .text import (
    bold,
    code,
    escape_html,
    italic,
    link,
    mention,
    pre,
    preformatted,
    quote,
    spoiler,
    strikethrough,
    underline,
)

# Time utilities
from .time import (
    current_timestamp,
    format_uptime,
    human_time,
    human_time_delta,
    parse_duration,
    time_difference,
    timestamp_to_date,
    timestamp_to_datetime,
)

# Version utilities
from .versions import (
    PythonVersion,
    VersionInfo,
    __core_version__,
    __python_version__,
    __version__,
    __version_stage__,
)

__all__ = [
    # Filesystem
    "is_frozen",
    "get_frozen_info",
    "is_android",
    "is_termux",
    "get_platform_info",
    "get_home_dir",
    "get_temp_dir",
    "get_project_root",
    "set_project_root",
    "resource_path",
    "userdata_path",
    "get_ffmpeg_paths",
    "ensure_dir",
    # Terminal
    "shell_exec",
    "shell_exec_sync",
    "get_ram_usage",
    "get_cpu_usage",
    # Media
    "get_ffmpeg",
    "get_ffprobe",
    "resize_image",
    "get_image_info",
    "PIL_AVAILABLE",
    # Git
    "run_command",
    "is_git_repo",
    "git_pull",
    "git_fetch",
    "git_checkout",
    "git_rebase",
    "get_current_branch",
    "get_commit_hash",
    "GitHubAPI",
    # Versions
    "PythonVersion",
    "VersionInfo",
    "__python_version__",
    "__version__",
    "__version_stage__",
    "__core_version__",
    # Text
    "bold",
    "italic",
    "underline",
    "strikethrough",
    "code",
    "pre",
    "preformatted",
    "spoiler",
    "link",
    "mention",
    "quote",
    "escape_html",
    # Time
    "timestamp_to_date",
    "timestamp_to_datetime",
    "human_time",
    "human_time_delta",
    "current_timestamp",
    "time_difference",
    "parse_duration",
    "format_uptime",
    # Hash
    "md5_hash",
    "sha256_hash",
    "sha512_hash",
    "hash_string",
    "hash_file",
    "hash_file_sync",
    # HTTP
    "fetch_url",
    "fetch_json",
    "fetch_status",
    "download_file",
    "post_json",
]
