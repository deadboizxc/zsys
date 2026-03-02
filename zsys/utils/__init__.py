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
    is_frozen,
    get_frozen_info,
    is_android,
    is_termux,
    get_platform_info,
    get_home_dir,
    get_temp_dir,
    get_project_root,
    set_project_root,
    resource_path,
    userdata_path,
    get_ffmpeg_paths,
    ensure_dir,
)

# Terminal utilities
from .terminal import (
    shell_exec,
    shell_exec_sync,
    get_ram_usage,
    get_cpu_usage,
)

# Media utilities
from .media import (
    get_ffmpeg,
    get_ffprobe,
    resize_image,
    get_image_info,
    PIL_AVAILABLE,
)

# Git utilities
from .git import (
    run_command,
    is_git_repo,
    git_pull,
    git_fetch,
    git_checkout,
    git_rebase,
    get_current_branch,
    get_commit_hash,
    GitHubAPI,
)

# Version utilities
from .versions import (
    PythonVersion,
    VersionInfo,
    __python_version__,
    __version__,
    __version_stage__,
    __core_version__,
)

# Text formatting
from .text import (
    bold,
    italic,
    underline,
    strikethrough,
    code,
    pre,
    preformatted,
    spoiler,
    link,
    mention,
    quote,
    escape_html,
)

# Time utilities
from .time import (
    timestamp_to_date,
    timestamp_to_datetime,
    human_time,
    human_time_delta,
    current_timestamp,
    time_difference,
    parse_duration,
    format_uptime,
)

# Hash utilities
from .hash import (
    md5_hash,
    sha256_hash,
    sha512_hash,
    hash_string,
    hash_file,
    hash_file_sync,
)

# HTTP utilities
from .http import (
    fetch_url,
    fetch_json,
    fetch_status,
    download_file,
    post_json,
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
