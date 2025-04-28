import argparse
import sys
from pathlib import Path


def validate_files(file_paths):
    """Проверяет существование всех файлов"""
    missing_files = [fp for fp in file_paths if not Path(fp).exists()]
    if missing_files:
        print("Ошибка: следующие файлы не найдены:", file=sys.stderr)
        for mf in missing_files:
            print(f"  - {mf}", file=sys.stderr)
        return False
    return True


def main():
    """Основная функция, запускает анализатор логов Django API"""

    from reports import LogAnalyzer, REPORTS # Отложенный импорт для уменьшения времени загрузки

    parser = argparse.ArgumentParser(
        description="Анализатор логов Django API",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Добавляем аргументы командной строки
    parser.add_argument(
        "log_files",
        type=str,
        nargs="+",
        help="Пути к файлам логов (можно указать несколько)",
    )

    # Получаем доступные отчеты только при необходимости
    report_choices = list(REPORTS.keys()) if 'REPORTS' in globals() else ['handlers']

    parser.add_argument(
        "--report",
        type=str,
        required=True,
        choices=report_choices,
        default="handlers",
        help="Тип отчёта (доступные: {})".format(", ".join(report_choices)),
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Путь для сохранения отчёта в файл (если не указано - вывод в консоль)",
    )

    args = parser.parse_args()

    # Проверяем существование файлов
    if not validate_files(args.log_files):
        sys.exit(1)

    try:
        # Анализируем логи
        analyzer = LogAnalyzer(args.log_files)
        analyzer.analyze()

        # Генерируем отчёт
        report = REPORTS[args.report](analyzer)

        # Выводим результат
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Отчёт сохранён в {args.output}")
            except IOError as e:
                print(f"Ошибка при сохранении отчёта: {str(e)}", file=sys.stderr)
                sys.exit(1)
        else:
            print(report)

    except Exception as e:
        print(f"Ошибка при обработке логов: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
