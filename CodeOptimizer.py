#!/usr/bin/env python3
"""
Скрипт для организации импортов в Python файлах:
1. Убирает лишние пустые строки между импортами
2. Группирует простые импорты (import x, import y -> import x, y)
3. Удаляет декоративные комментарии
4. Объединяет многострочные from импорты в одну строку
"""

import re, sys
from collections import defaultdict
from pathlib import Path
from typing import List, Tuple

def parse_imports(lines: List[str]) -> Tuple[List[str], int, int]:
    """
    Находит блок импортов в начале файла
    Returns:
        (import_lines, start_index, end_index)
    """
    import_lines = []
    start_index = -1
    end_index = -1
    in_import_block = False
    in_multiline_import = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Пропускаем shebang, encoding, docstrings
        if i == 0 and stripped.startswith("#!"):
            continue
        if stripped.startswith("#") and "coding" in stripped:
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue

        # Многострочный импорт — продолжаем до закрывающей скобки
        if in_multiline_import:
            import_lines.append(line)
            if ")" in line:
                in_multiline_import = False
                end_index = i
            continue

        # Начало многострочного импорта
        if stripped.startswith("from ") and "(" in stripped and ")" not in stripped:
            if start_index == -1:
                start_index = i
            in_import_block = True
            in_multiline_import = True
            import_lines.append(line)
            end_index = i
            continue

        # Начало блока импортов
        if stripped.startswith(("import ", "from ")):
            if start_index == -1:
                start_index = i
            in_import_block = True
            import_lines.append(line)
            end_index = i
            continue

        # Пустая строка внутри импортов
        if in_import_block and not stripped:
            import_lines.append(line)
            continue

        # Конец блока импортов
        if in_import_block and stripped and not stripped.startswith(("import ", "from ", "#")):
            break

    return import_lines, start_index, end_index

def parse_multiline_from_import(lines: List[str], start_idx: int) -> Tuple[str, int]:
    """
    Парсит многострочный from import, собирает все имена в одну строку.
    Возвращает (final_line, lines_consumed)
    """
    i = start_idx
    consumed = 0
    # Первая строка: from X import (
    first = lines[i].strip()
    m = re.match(r'from\s+(\S+)\s+import\s*\(', first)
    if not m:
        # Не стандартный случай — вернём первую строку как есть
        return lines[i].rstrip("\n") + "\n", 1

    source = m.group(1)
    items = []

    # Обрабатываем последующие строки, пока не найдём ')'
    while i < len(lines):
        line = lines[i].strip()
        # Пропускаем первую строку обработанной выше
        if i == start_idx:
            # уже взяли source
            pass
        else:
            # удаляем возможные скобки, запятые
            cleaned = line.replace("(", "").replace(")", "").strip()
            # разделим по запятым (на случай, если в одной строке несколько)
            parts = [p.strip() for p in cleaned.split(",") if p.strip()]
            items.extend(parts)
        consumed += 1
        if ")" in lines[i]:
            break
        i += 1

    # Финальная строка
    if items:
        final_line = f"from {source} import {', '.join(items)}\n"
    else:
        # Если ничего не нашли — вернуть оригинал(ы) в одну строку
        # соберём первые consumed строк в один
        block = " ".join(l.strip() for l in lines[start_idx:start_idx+consumed])
        block = re.sub(r"\s+", " ", block)
        final_line = (block.rstrip() + "\n")

    return final_line, consumed

def remove_extra_newlines(lines: List[str]) -> List[str]:
    """Удаляет лишние пустые строки (оставляет максимум одну подряд)"""
    result = []
    empty_count = 0
    for line in lines:
        if line.strip() == "":
            empty_count += 1
            if empty_count <= 1:
                result.append("\n")
            # если >1 — пропускаем
        else:
            empty_count = 0
            result.append(line)
    # Убедимся, что файл заканчивается одним переводом строки
    if result and result[-1].strip() != "":
        result.append("\n")
    return result

def remove_docstrings_before_imports(lines: List[str], start_idx: int) -> Tuple[List[str], int]:
    """
    Удаляет docstring перед импортами, если он есть и не является модульной документацией в самом начале.
    Возвращает (new_lines, new_start_idx)
    """
    if start_idx <= 0:
        return lines, start_idx

    i = start_idx - 1
    # Пропускаем пустые строки
    while i >= 0 and lines[i].strip() == "":
        i -= 1

    if i < 0:
        return lines, start_idx

    stripped = lines[i].strip()
    # Если конец docstring
    if stripped.endswith('"""') or stripped.endswith("'''"):
        quote = '"""' if '"""' in stripped else "'''"
        # Найдём начало docstring
        j = i
        if stripped.startswith(quote) and len(stripped) > len(quote):
            # однострочный docstring
            start_doc = i
        else:
            start_doc = -1
            j -= 1
            while j >= 0:
                if quote in lines[j]:
                    start_doc = j
                    break
                j -= 1

        if start_doc != -1:
            # Пропускаем shebang/encoding в начале
            skip_until = 0
            if lines and lines[0].strip().startswith("#!"):
                skip_until = 1
            if len(lines) > skip_until and lines[skip_until].strip().startswith("#") and "coding" in lines[skip_until]:
                skip_until += 1
            # Только если docstring не в самом начале файла (после shebang/encoding) — удаляем
            if start_doc > skip_until:
                new_lines = lines[:start_doc] + lines[i+1:]
                new_start_idx = start_idx - (i - start_doc + 1)
                return new_lines, new_start_idx

    return lines, start_idx

def is_decorator_line(line: str) -> bool:
    """Проверяет, является ли строка декоративной линией (═, ─, -, _)"""
    stripped = line.strip()
    if not stripped.startswith("#"):
        return False
    content = stripped.lstrip("#").strip()
    if not content:
        return False
    decorative_chars = {"═", "─", "-", "_", "—", "━"}
    return all(c in decorative_chars for c in content) and len(content) > 3

def is_section_header(line: str) -> bool:
    """Проверяет, является ли строка заголовком секции (ЗАГЛАВНЫМИ БУКВАМИ)"""
    stripped = line.strip()
    if not stripped.startswith("#"):
        return False
    content = stripped.lstrip("#").strip()
    if not content:
        return False
    return content.isupper() and any(c.isalpha() for c in content)

def clean_trailing_decorators(line: str) -> str:
    """Удаляет декоративные символы в конце комментария, оставляя текст"""
    stripped = line.rstrip("\n\r")
    if not stripped.strip().startswith("#"):
        return line
    pattern = r"^(\s*#\s*.+?)\s+[-─═_—━]{3,}\s*$"
    match = re.match(pattern, stripped)
    if match:
        return match.group(1) + "\n"
    return line

def remove_decorative_comments(lines: List[str]) -> Tuple[List[str], int]:
    new_lines = []
    i = 0
    removed_count = 0
    modified_count = 0

    def is_checkmark_comment(line: str) -> bool:
        """Проверяет, является ли строка комментарием с символом ✅, ❌, ✔️ и т.д. в любом месте комментария."""
        stripped = line.strip()
        if not stripped.startswith("#"):
            return False

        # Убираем # и пробелы после него
        content = stripped[1:].strip()
        emojis = {"✅", "❌", "✔️", "❓", "⚠️", "🔴", "🟢"}

        # Проверяем, начинается ли содержимое с любого из эмодзи
        return any(content.startswith(emoji) for emoji in emojis)

    while i < len(lines):
        line = lines[i]

        # Удаляем шаблоны "декор → заголовок → декор"
        if (i + 2 < len(lines)
            and is_decorator_line(lines[i])
            and is_section_header(lines[i + 1])
            and is_decorator_line(lines[i + 2])):
            removed_count += 3
            i += 3
            continue
        # Удаляем декоративные строки или комментарии с эмодзи
        elif is_decorator_line(line) or is_checkmark_comment(line):
            removed_count += 1
            i += 1
            continue

        # Очищаем "хвосты" в комментариях (например, "# текст -----" → "# текст")
        cleaned = clean_trailing_decorators(line)
        if cleaned != line:
            modified_count += 1
        new_lines.append(cleaned)
        i += 1

    return new_lines, removed_count + modified_count

def remove_unwanted_comments_and_imports(lines: List[str]) -> Tuple[List[str], int]:
    """
    Удаляет нежелательные комментарии с путями файлов
    Returns: (new_lines, changes_count)
    """
    new_lines = []
    removed_count = 0

    for line in lines:
        stripped = line.strip()

        if (stripped.startswith("#") and 
            ".py" in stripped and 
            "/" in stripped):
            removed_count += 1
            continue

        new_lines.append(line)
    return new_lines, removed_count

def organize_imports(import_lines: List[str]) -> List[str]:
    """
    Организует импорты:
      - сворачивает многострочные from (...) в одну строку
      - группирует простые импорты в одну строчку `import a, b, c`
      - сортирует элементы внутри групп
      - добавляет ровно один пустой рядок в конце блока импортов
    """
    simple_imports = []
    from_imports = []
    future_imports = []
    aliased_imports = []

    i = 0
    n = len(import_lines)
    while i < n:
        line = import_lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # from __future__ — отдельная группа
        if stripped.startswith("from __future__"):
            future_imports.append(stripped)
            i += 1
            continue

        # Многострочный from import
        if stripped.startswith("from ") and "(" in stripped and ")" not in stripped:
            parsed, consumed = parse_multiline_from_import(import_lines, i)
            from_imports.append(parsed.rstrip("\n"))
            i += consumed
            continue

        # Обычный from import
        if stripped.startswith("from "):
            # убираем лишние пробелы
            one = re.sub(r"\s+", " ", stripped)
            from_imports.append(one)
            i += 1
            continue

        # import ...
        if stripped.startswith("import "):
            modules = stripped[7:].strip()
            if " as " in modules:
                aliased_imports.append(re.sub(r"\s+", " ", stripped))
            else:
                parts = [m.strip() for m in modules.split(",") if m.strip()]
                simple_imports.extend(parts)
            i += 1
            continue

        i += 1

    result_lines: List[str] = []

    # 1) __future__
    if future_imports:
        for line in sorted(set(future_imports), key=str.lower):
            result_lines.append(line + "\n")

    # 2) Простые import
    if simple_imports:
        uniques = sorted(set(simple_imports), key=str.lower)
        result_lines.append(f"import {', '.join(uniques)}\n")

    # 3) Алиасы (каждый в своей строке)
    if aliased_imports:
        for line in sorted(set(aliased_imports), key=str.lower):
            result_lines.append(line + "\n")

    # 4) from imports
    if from_imports:
        for line in sorted(set(from_imports), key=str.lower):
            # убедимся, что формат 'from X import a, b'
            one = re.sub(r"\s*,\s*", ", ", line)
            result_lines.append(one + "\n")

    # очистка: убрать лишние подряд пустые строки, оставить максимум одну
    cleaned = []
    empty = 0
    for ln in result_lines:
        if ln.strip() == "":
            empty += 1
            if empty <= 1:
                cleaned.append("\n")
        else:
            empty = 0
            cleaned.append(ln)

    # Если результат не пустой — гарантируем ровно одну пустую строку в конце блока
    if cleaned:
        if cleaned[-1].strip() != "":
            cleaned.append("\n")
        # еще: если в конце несколько пустых — оставим одну
        while len(cleaned) > 1 and cleaned[-2].strip() == "" and cleaned[-1].strip() == "":
            cleaned.pop()

    return cleaned

def clean_file(file_path: Path) -> Tuple[int, int]:
    """
    Очищает импорты и декоративные комментарии в файле
    Returns: (total_changes, total_lines)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Ошибка чтения {file_path}: {e}")
        return 0, 0

    original_lines = lines.copy()
    total_changes = 0

    # 1) Найти блок импортов
    import_lines, start_idx, end_idx = parse_imports(lines)

    # 2) Удалить docstring перед импортами, если нужно
    if start_idx != -1:
        lines, start_idx = remove_docstrings_before_imports(lines, start_idx)
        # переопределим импортный блок после возможного удаления docstring
        import_lines, start_idx, end_idx = parse_imports(lines)

    # 3) Организуем импорты
    if start_idx != -1:
        organized = organize_imports(import_lines)
        original_imports = lines[start_idx:end_idx + 1]
        if organized != original_imports:
            lines = lines[:start_idx] + organized + lines[end_idx + 1:]
            import_changes = len(organized) - len(original_imports)
            total_changes += abs(import_changes)

    # 4) Удаляем лишние пустые строки по всему файлу (максимум одна подряд)
    lines = remove_extra_newlines(lines)

    # 5) Удаляем декоративные комментарии
    lines, decorator_changes = remove_decorative_comments(lines)
    total_changes += decorator_changes

    # 6) Удаляем нежелательные комментарии и импорты
    lines, unwanted_changes = remove_unwanted_comments_and_imports(lines)
    total_changes += unwanted_changes

    # Если ничего не изменилось
    if lines == original_lines:
        return 0, len(original_lines)

    # Записываем изменения (без dry-run)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"✅ {file_path.name}: внесено {total_changes} изменений")
    except Exception as e:
        print(f"❌ Ошибка записи {file_path}: {e}")
        return 0, len(original_lines)

    return total_changes, len(original_lines)

def process_directory(directory: Path, pattern: str = "*.py"):
    """Обрабатывает все Python файлы в директории"""
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 'dist', 'build', '.eggs'}
    files = []
    for file_path in directory.rglob(pattern):
        if any(excluded in file_path.parts for excluded in exclude_dirs):
            continue
        files.append(file_path)

    if not files:
        print(f"❌ Файлы {pattern} не найдены в {directory}")
        return

    print(f"🔎 Найдено {len(files)} файлов\n")

    total_changes = 0
    total_files_changed = 0

    for file_path in files:
        changes, _ = clean_file(file_path)
        if changes > 0:
            total_changes += changes
            total_files_changed += 1

    print("\n" + "=" * 60)
    print("📊 Итого:")
    print(f"   Обработано файлов: {len(files)}")
    print(f"   Изменено файлов: {total_files_changed}")
    print(f"   Всего изменений: {total_changes}")

def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    if not path.exists():
        print(f"❌ Путь не существует: {path}")
        sys.exit(1)

    if path.is_file():
        changes, total = clean_file(path)
        print(f"\n📊 Изменено: {changes} строк из {total}")
    else:
        process_directory(path, pattern="*.py")

if __name__ == "__main__":
    main()

