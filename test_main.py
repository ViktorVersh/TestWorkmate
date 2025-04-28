import os
import sys
import tempfile
import pytest
from unittest.mock import patch

# Импортируем основную функцию
from main import main, validate_files


@pytest.fixture
def log_file(tmp_path):
    """
    Создаем временный файл с содержимым лога
    """
    d = tmp_path / "subdir"
    d.mkdir()
    p = d / "test_log.txt"
    p.write_text("Some log content")
    return str(p)


@pytest.fixture
def nonexistent_file():
    """Путь к несуществующему файлу"""
    return "/path/to/nonexistent/file"


def test_validate_files_existing(log_file):
    """
    Проверяем, что функция возвращает True для существующего файла.
    """
    assert validate_files([log_file]) is True


def test_validate_files_nonexisting(nonexistent_file):
    """
    Проверяем, что функция возвращает False для несуществующего файла.
    """
    assert validate_files([nonexistent_file]) is False


def test_main_with_invalid_arguments(nonexistent_file):
    """
    Проверяем, что функция завершается с ошибкой при передаче неверных аргументов.
    """
    with patch.object(sys, 'argv', ["script_name", nonexistent_file]):
        with patch('reports.LogAnalyzer'):
            with patch('reports.REPORTS'):
                with pytest.raises(SystemExit):
                    main()


def test_main_save_to_file(log_file):
    """
    Проверяем, что функция сохраняет результаты анализа в файл.
    """
    output_file = tempfile.NamedTemporaryFile(delete=False)
    with patch.object(sys, 'argv', ["script_name", log_file, '--report', 'handlers', '--output', output_file.name]):
        with patch('reports.LogAnalyzer') as MockLogAnalyzer:
            instance = MockLogAnalyzer.return_value
            instance.analyze.return_value = None
            main()
            assert os.path.exists(output_file.name)
