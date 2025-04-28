# Анализ журнала логирования
>cli-приложение, которое анализирует логи django-приложения и формирует отчеты. Отчет выводится в консоль или в файл.

Анализатор логов Django API

>positional arguments:
>
>log_files            Пути к файлам логов (можно указать несколько)

>options:
>
>-h, --help           show this help message and exit
> 
>--report {handlers}  Тип отчёта (доступные: handlers) (default: handlers)
> 
>--output OUTPUT      Путь для сохранения отчёта в файл (если не указано - вывод в консоль) (default: None)
> 

# Пример формирование отчёта:

```bash
python main.py logs/app1.log logs/app2.log logs/app3.log --report handlers
```
```bash
python main.py logs/app1.log logs/app2.log logs/app3.log --report handlers --output report.txt
```
Для запуска тестов:
```bash
pytest -v
```
# Для добавления нового отчета вносим изменения в файле reports.py: 
> - если отчет простой добавить функцию генерации отчета;

> - если требуется сложная логика, можно создать отдельный класс;

> - зарегистрировать новый отчет в словаре REPORTS в конце файла reports.py

Образец вывода в файле report.txt
<p>
Образец вывода тестов в файле test.txt

❗️Программа работает на 64-битных системах