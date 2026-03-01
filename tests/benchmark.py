#!/usr/bin/env python3
"""
Бенчмарк скрипт для измерения производительности zxc_userbot.
Использование: python benchmark.py
"""

import time
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from implementations.plugins_tools import find_modules, get_module_path, is_module_enabled
from implementations.plugins_tools.modules import _get_cached_meta


def measure_time(func):
    """Декоратор для измерения времени выполнения."""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = end - start
        print(f"⏱️  {func.__name__}: {elapsed:.3f}s")
        return result, elapsed
    return wrapper


@measure_time
def benchmark_find_modules():
    """Тест производительности поиска модулей."""
    core_dir = get_module_path("", core=True).parent
    custom_dir = get_module_path("", core=False).parent
    
    core_modules = find_modules(core_dir)
    custom_modules = find_modules(custom_dir)
    
    total = len(core_modules) + len(custom_modules)
    print(f"   Найдено модулей: {len(core_modules)} core + {len(custom_modules)} custom = {total}")
    return total


@measure_time
def benchmark_metadata_parsing():
    """Тест производительности парсинга метаданных."""
    core_dir = get_module_path("", core=True).parent
    modules = find_modules(core_dir)[:10]  # Первые 10 модулей
    
    parsed = 0
    for module_name in modules:
        if not is_module_enabled(module_name):
            continue
        module_path = get_module_path(module_name, core=True)
        if module_path.exists():
            file_mtime = module_path.stat().st_mtime
            meta = _get_cached_meta(str(module_path), file_mtime)
            parsed += 1
    
    print(f"   Распарсено модулей: {parsed}")
    return parsed


@measure_time  
def benchmark_metadata_cache_hit():
    """Тест производительности кэша метаданных."""
    core_dir = get_module_path("", core=True).parent
    modules = find_modules(core_dir)[:10]
    
    # Второй проход - должен использовать кэш
    for module_name in modules:
        if not is_module_enabled(module_name):
            continue
        module_path = get_module_path(module_name, core=True)
        if module_path.exists():
            file_mtime = module_path.stat().st_mtime
            _get_cached_meta(str(module_path), file_mtime)
    
    # Статистика кэша
    cache_info = _get_cached_meta.cache_info()
    hit_rate = cache_info.hits / (cache_info.hits + cache_info.misses) * 100 if cache_info.hits else 0
    print(f"   Cache hits: {cache_info.hits}, misses: {cache_info.misses}, hit rate: {hit_rate:.1f}%")
    return cache_info


def print_separator():
    print("\n" + "="*60 + "\n")


def main():
    """Основная функция бенчмарка."""
    print("🚀 zxc_userbot Performance Benchmark\n")
    print("="*60)
    
    # Тест 1: Поиск модулей
    print("\n📁 Тест 1: Поиск модулей")
    modules_count, find_time = benchmark_find_modules()
    
    print_separator()
    
    # Тест 2: Парсинг метаданных (первый раз)
    print("📝 Тест 2: Парсинг метаданных (холодный старт)")
    parsed, parse_time = benchmark_metadata_parsing()
    
    print_separator()
    
    # Тест 3: Парсинг метаданных (из кэша)
    print("💾 Тест 3: Парсинг метаданных (горячий кэш)")
    cache_info, cache_time = benchmark_metadata_cache_hit()
    
    print_separator()
    
    # Итоги
    print("📊 Результаты:")
    print(f"   • Модулей найдено: {modules_count}")
    print(f"   • Время поиска: {find_time:.3f}s")
    print(f"   • Парсинг (первый): {parse_time:.3f}s")
    print(f"   • Парсинг (кэш): {cache_time:.3f}s")
    print(f"   • Ускорение от кэша: {parse_time/cache_time:.1f}x" if cache_time > 0 else "   • Ускорение: N/A")
    
    print_separator()
    
    # Прогноз времени загрузки
    estimated_sequential = parse_time * (modules_count / parsed)
    estimated_parallel = parse_time  # В параллельном режиме время ~= самому медленному модулю
    
    print("⏱️  Прогноз времени загрузки:")
    print(f"   • Последовательная загрузка: ~{estimated_sequential:.1f}s")
    print(f"   • Параллельная загрузка: ~{estimated_parallel:.1f}s")
    print(f"   • Ожидаемое ускорение: {estimated_sequential/estimated_parallel:.1f}x")
    
    print("\n" + "="*60)
    print("✅ Бенчмарк завершён!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Бенчмарк прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
