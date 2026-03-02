# -*- coding: utf-8 -*-
"""Git utilities for zsys core.

Provides functions for git operations, GitHub API interactions,
and release management.
"""
# RU: Git-утилиты — выполнение команд, работа с ветками и взаимодействие с GitHub API.

import os
import platform
import subprocess
from typing import Optional, Dict, List, Any
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def run_command(command: List[str], cwd: Optional[str] = None) -> str:
    """Execute a shell command synchronously.
    
    Args:
        command: List of command arguments.
        cwd: Working directory for the command.
    
    Returns:
        str: Command output.
    
    Raises:
        subprocess.CalledProcessError: If command fails.
    """
    # RU: Запускает подпроцесс, собирает stdout/stderr и пробрасывает ошибку при ненулевом коде возврата.
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=cwd
    )
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode, command, stdout, stderr
        )
    
    return stdout.strip()


def is_git_repo(path: Optional[str] = None) -> bool:
    """Check if the path is a Git repository.
    
    Args:
        path: Path to check. Defaults to current directory.
    
    Returns:
        bool: True if path is a git repository.
    """
    # RU: Проверяет наличие директории .git в указанном или текущем пути.
    check_path = Path(path) if path else Path.cwd()
    return (check_path / ".git").exists()


def git_pull(branch: str = "main", cwd: Optional[str] = None) -> str:
    """Execute git pull with fast-forward only.
    
    Args:
        branch: Branch name to pull from.
        cwd: Working directory.
    
    Returns:
        str: Command output.
    """
    # RU: Использует --ff-only для предотвращения случайных merge-коммитов.
    return run_command(["git", "pull", "origin", branch, "--ff-only"], cwd=cwd)


def git_fetch(cwd: Optional[str] = None) -> str:
    """Fetch all remotes.
    
    Args:
        cwd: Working directory.
    
    Returns:
        str: Command output.
    """
    # RU: Обновляет все удалённые ссылки без слияния с локальными ветками.
    return run_command(["git", "fetch", "--all"], cwd=cwd)


def git_checkout(branch: str, cwd: Optional[str] = None) -> str:
    """Checkout a branch.
    
    Args:
        branch: Branch name to checkout.
        cwd: Working directory.
    
    Returns:
        str: Command output.
    """
    # RU: Переключает рабочую директорию на указанную ветку.
    return run_command(["git", "checkout", branch], cwd=cwd)


def git_rebase(branch: str = "main", cwd: Optional[str] = None) -> str:
    """Execute git rebase.
    
    Args:
        branch: Branch name to rebase onto.
        cwd: Working directory.
    
    Returns:
        str: Command output.
    """
    # RU: Перебазирует текущую ветку поверх origin/{branch}.
    return run_command(["git", "rebase", f"origin/{branch}"], cwd=cwd)


def get_current_branch(cwd: Optional[str] = None) -> str:
    """Get the current git branch name.
    
    Args:
        cwd: Working directory.
    
    Returns:
        str: Current branch name.
    """
    # RU: Использует --abbrev-ref HEAD для получения читаемого имени ветки вместо SHA.
    return run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)


def get_commit_hash(short: bool = True, cwd: Optional[str] = None) -> str:
    """Get the current commit hash.
    
    Args:
        short: Return short hash (7 chars).
        cwd: Working directory.
    
    Returns:
        str: Commit hash.
    """
    # RU: Добавляет флаг --short для сокращённого 7-символьного хэша.
    cmd = ["git", "rev-parse"]
    if short:
        cmd.append("--short")
    cmd.append("HEAD")
    return run_command(cmd, cwd=cwd)


class GitHubAPI:
    """GitHub API client for release management.
    
    Attributes:
        owner: Repository owner (user or organisation).
        repo: Repository name.
        token: Optional GitHub personal access token for authenticated requests.
        base_url: Base API URL composed from owner and repo.
    
    Example:
        api = GitHubAPI("octocat", "Hello-World", token=os.environ["GH_TOKEN"])
        release = api.get_latest_release()
    """
    # RU: Клиент для работы с GitHub Releases API — получение релизов и загрузка платформенных ассетов.
    
    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        """Initialize GitHub API client.
        
        Args:
            owner: Repository owner.
            repo: Repository name.
            token: GitHub API token (optional).
        """
        # RU: Формирует базовый URL и сохраняет учётные данные для последующих запросов.
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for GitHubAPI")
        
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"
        
    @property
    def headers(self) -> Dict[str, str]:
        """Get API headers with optional authorization.
        
        Returns:
            Dict[str, str]: Headers dict including Accept, API version, and optional Bearer token.
        """
        # RU: Добавляет Authorization только при наличии токена, чтобы не отправлять пустой заголовок.
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def get_releases(self) -> Optional[List[Dict[str, Any]]]:
        """Get all releases from the repository.
        
        Returns:
            List of release data or None on error.
        """
        # RU: Возвращает None при любой сетевой ошибке, не пробрасывая исключение.
        try:
            response = requests.get(
                f"{self.base_url}/releases",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """Get the latest release from the repository.
        
        Returns:
            Latest release data or None on error.
        """
        # RU: Использует эндпоинт /releases/latest для получения последнего опубликованного релиза.
        try:
            response = requests.get(
                f"{self.base_url}/releases/latest",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None
    
    def download_asset_for_platform(
        self, 
        release: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Download release asset matching current platform.
        
        Args:
            release: Release data. Uses latest if not provided.
        
        Returns:
            Downloaded filename or None on error.
        """
        # RU: Определяет текущую платформу и ищет ассет по ключевым словам в имени файла.
        if release is None:
            release = self.get_latest_release()
        
        if not release:
            return None
        
        current_platform = platform.system().lower()
        platform_keywords = {
            "windows": ["windows", "win", ".exe"],
            "linux": ["linux"],
            "darwin": ["macos", "darwin"],
            "android": ["termux", "android"]
        }  # RU: Ключевые слова для сопоставления имён ассетов с текущей платформой
        
        keywords = platform_keywords.get(current_platform, [])
        if not keywords:
            return None
        
        for asset in release.get("assets", []):
            asset_name = asset.get("name", "").lower()
            if any(kw in asset_name for kw in keywords):
                return self._download_asset(asset)
        
        return None
    
    def _download_asset(self, asset: Dict[str, Any]) -> Optional[str]:
        """Download a specific asset.
        
        Args:
            asset: Asset data from GitHub API.
        
        Returns:
            Downloaded filename or None on error.
        """
        # RU: Скачивает ассет потоковой передачей чанками по 8 КБ для экономии памяти.
        download_url = asset.get("browser_download_url")
        file_name = asset.get("name")
        
        if not download_url or not file_name:
            return None
        
        try:
            with requests.get(
                download_url, 
                headers=self.headers, 
                stream=True, 
                timeout=60
            ) as r:
                r.raise_for_status()
                with open(file_name, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):  # RU: Потоковая запись по 8 КБ — не загружает весь файл в память
                        f.write(chunk)
            return file_name
        except requests.RequestException:
            return None
