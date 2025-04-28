import pytest
from collections import defaultdict
from reports import LogAnalyzer

# создаем тестовые данные
TEST_LOG_DATA = """
2023-01-01 12:00:00,123 INFO GET /api/users
2023-01-01 12:00:01,456 ERROR POST /api/login
2023-01-01 12:00:02,789 DEBUG GET /api/products
2023-01-01 12:00:03,111 WARNING PUT /api/cart
2023-01-01 12:00:04,222 CRITICAL DELETE /api/account
Internal Server Error: /api/payment
SELECT * FROM users WHERE id = 1
django.db.utils.IntegrityError
"""


@pytest.fixture
def log_analyzer():
    """Фикстура для создания объекта LogAnalyzer."""
    return LogAnalyzer(["test.log"])


@pytest.fixture
def mock_log_file(tmp_path):
    """Фикстура для создания временного файла с тестовыми данными."""
    log_file = tmp_path / "test.log"
    log_file.write_text(TEST_LOG_DATA)
    return str(log_file)


def test_log_analyzer_init(log_analyzer):
    """Тестирование инициализации объекта LogAnalyzer."""
    assert log_analyzer.log_files == ["test.log"]
    assert isinstance(log_analyzer.handlers_data, defaultdict)
    assert log_analyzer._buffer_size == 10000
    assert log_analyzer.total_requests == 0


# Тесты для обработки строк
@pytest.mark.parametrize("line,expected", [
    ("2023-01-01 12:00:00,123 INFO Test message", "INFO"),
    ("DEBUG Some debug message", "DEBUG"),
    ("[ERROR] Critical failure", "ERROR"),
    ("No level in this message", "INFO"),
    ("", "INFO"),
])
def test_extract_log_level(log_analyzer, line, expected):
    """Тестирование извлечения уровня логирования."""
    assert log_analyzer._extract_log_level(line) == expected


@pytest.mark.parametrize("line,expected", [
    ("GET /api/users HTTP/1.1", "/api/users"),
    ("POST /api/login?param=value", "/api/login"),
    ("Internal Server Error: /api/payment", "ERROR:/api/payment"),
    ("SELECT * FROM users", "SQL:users"),
    ("django.db.utils.IntegrityError", "django.db"),
    ("No endpoint here", None),
])
def test_extract_endpoint(log_analyzer, line, expected):
    """Тестирование извлечения endpoint."""
    assert log_analyzer._extract_endpoint(line) == expected


# Тесты для буферизации
def test_buffer_flushing(log_analyzer):
    """
    Тестирование очистки буфера и добавления данных в обработчики.
    :param log_analyzer:
    :return:
    """
    log_analyzer._buffer["/test"]["INFO"] = 5
    log_analyzer._flush_buffer()

    assert "/test" in log_analyzer.handlers_data
    assert log_analyzer.handlers_data["/test"]["INFO"] == 5
    assert not log_analyzer._buffer  # Буфер должен очиститься


def test_empty_report(log_analyzer):
    """Тестирование отчета без данных запросов."""
    report = list(log_analyzer.generate_handlers_report())
    assert report[0] == "No request data found in logs"


def test_reports_interface():
    """Тестирование интерфейса REPORTS."""
    from reports import REPORTS
    assert 'handlers' in REPORTS
    assert callable(REPORTS['handlers'])
