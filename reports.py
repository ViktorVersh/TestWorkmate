import re
import mmap
from typing import TypedDict, List, Dict, Optional, Generator
from collections import defaultdict


class LogLevels(TypedDict):
    """
    Типизированный словарь для хранения уровней логирования.
    """
    DEBUG: int
    INFO: int
    WARNING: int
    ERROR: int
    CRITICAL: int


HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD']  # Список методов HTTP
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']  # Список уровней логирования


class LogAnalyzer:
    """
    Основной класс для анализа логов.
    """

    def __init__(self, log_files: List[str], buffer_size: int = 10000):
        self.log_files = log_files
        self.handlers_data: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))  # Основная структура
        # для хранения результатов
        self._buffer_size = buffer_size  # Размер буфера (в строках по умолчанию - 10000)
        self._buffer = defaultdict(lambda: defaultdict(int))  # Буфер для накопления данных перед сохранением
        self._line_count = 0
        self._total_requests_counter = 0

    def analyze(self) -> None:
        """Метод анализа больших логов.
        Использует mmap для чтения больших файлов,
        файлы обрабатываются построчно и накапливает данные в буфере перед сохранением в основную структуру.
        """
        for file_path in self.log_files:
            try:
                with open(file_path, 'r+', encoding='utf-8', errors='replace') as f:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        for line in iter(mm.readline, b''):
                            self._process_line(line.decode('utf-8', errors='replace').strip())
                            self._line_count += 1

                            if self._line_count % self._buffer_size == 0:
                                self._flush_buffer()
            except FileNotFoundError:
                print(f"File not found - {file_path}")
                continue
            except Exception as e:
                print(f"Error processing file '{file_path}': {str(e)}")
                continue
            finally:
                self._flush_buffer()  # Гарантированный сброс буфера

    def _flush_buffer(self) -> None:
        """Перенос данных из буфера в основную структуру"""
        for endpoint, levels in self._buffer.items():
            for level, count in levels.items():
                self.handlers_data[endpoint][level] += count
                self._total_requests_counter += count  # Корректный подсчёт
        self._buffer.clear()

    def _process_line(self, line: str) -> None:
        """Обработка строки с буферизацией"""
        log_level = self._extract_log_level(line)
        endpoint = self._extract_endpoint(line)

        if endpoint:
            self._buffer[endpoint][log_level] += 1

    def _extract_log_level(self, line: str) -> str:
        """Извлечение уровня логирования"""
        if not line:
            return "INFO"

        line_start = line[:100].upper()

        # Проверка формата timestamp + уровень
        level_match = re.search(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} (\w+)', line_start)
        if level_match and level_match.group(1) in LOG_LEVELS:
            return level_match.group(1)

        # Проверка по ключевым словам
        for level in LOG_LEVELS:
            if level in line_start:
                return level

        return "INFO"  # Уровень по умолчанию

    def _extract_endpoint(self, line: str) -> Optional[str]:
        """Извлечение endpoint"""
        if not line:
            return None

        line_part = line[:200]

        # Обработка HTTP-запросов
        if any(method in line_part for method in [f"{m} " for m in HTTP_METHODS]):
            match = re.search(r'({})\s+([^\s\?]+)'.format('|'.join(HTTP_METHODS)), line_part)
            if match:
                return match.group(2)

        # Обработка ошибок
        if 'Internal Server Error:' in line_part:
            match = re.search(r'Internal Server Error:\s+([^\s]+)', line_part)
            if match:
                return f"ERROR:{match.group(1)}"

        # Обработка SQL-запросов
        if 'SELECT ' in line_part and 'FROM ' in line_part:
            match = re.search(r"SELECT\s.+FROM\s[\'\"`]?([^\s\,\'\"`]+)", line_part)
            if match:
                return f"SQL:{match.group(1)}"

        # Обработка Django-специфичных логов
        if 'django.' in line_part:
            match = re.search(r'django\.(\w+)', line_part)
            if match:
                return f"django.{match.group(1)}"

        return None

    @property
    def total_requests(self) -> int:
        """Получение общего количества запросов"""
        return self._total_requests_counter

    def generate_handlers_report(self) -> Generator[str, None, None]:
        """Генерация отчёта по частям"""
        if not self.handlers_data:
            yield "No request data found in logs"
            return

        # Собираем все уровни логирования
        all_levels = set()
        for counts in self.handlers_data.values():
            all_levels.update(counts.keys())

        active_levels = [level for level in LOG_LEVELS if level in all_levels]

        if not active_levels:
            yield "No log levels data found"
            return

        # Подготавливаем данные для вывода
        sorted_endpoints = sorted(self.handlers_data.keys())
        column_width = max(len(endpoint) for endpoint in self.handlers_data) if self.handlers_data else 20

        # Заголовок отчёта
        yield f"Total requests: {self.total_requests}\n"
        yield "HANDLER".ljust(column_width) + "\t" + "\t".join(level.ljust(5) for level in active_levels)

        # Данные по каждому endpoint
        for endpoint in sorted_endpoints:
            counts = self.handlers_data[endpoint]
            row = endpoint.ljust(column_width) + "\t" + "\t".join(
                str(counts.get(level, 0)).ljust(5) for level in active_levels
            )
            yield row

        # Итоговая строка
        total_counts = []
        for level in active_levels:
            total = sum(counts.get(level, 0) for counts in self.handlers_data.values())
            total_counts.append(str(total))

        yield "_" * column_width + "\t" + "\t".join(count.ljust(5) for count in total_counts)


# Интерфейс для отчётов
REPORTS = {
    'handlers': lambda analyzer: "\n".join(analyzer.generate_handlers_report()),
}
