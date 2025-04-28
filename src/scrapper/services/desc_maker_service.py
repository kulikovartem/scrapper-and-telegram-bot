from bs4 import BeautifulSoup
from typing import Dict
from src.scrapper.interfaces.desc_maker_interface import DescMaker


class DescMakerService(DescMaker):

    """
        Сервис для формирования текстового описания на основе данных из словаря.

        Этот класс реализует интерфейс `DescMaker` и предоставляет метод `make_desc`,
        который формирует строковое описание из переданного словаря. Если ключ в словаре —
        `"preview"`, его значение интерпретируется как HTML, и из него извлекается чистый текст
        с помощью `BeautifulSoup`.

        Методы:
            make_desc(dictionary: Dict[str, str]) -> str:
                Создает строковое описание из переданного словаря, где каждый ключ и его значение
                представлены в формате "ключ: значение". Если ключ — `"preview"`, из его значения
                извлекается только текстовое содержимое.

        Пример:
            ```python
            dictionary = {
                "title": "Some title",
                "description": "Detailed description",
                "preview": "<p>Some HTML content</p>"
            }
            result = DescMakerService().make_desc(dictionary)
            print(result)
            # Вывод:
            # title: Some title
            # description: Detailed description
            # preview: Some HTML content
            ```
    """

    def make_desc(self, dictionary: Dict[str, str]) -> str:
        """
        Создает строковое описание на основе ключей и значений из словаря.

        Этот метод принимает словарь, где ключи и значения — строки. Для каждого ключа
        в словаре метод добавляет строку в результирующее описание. Если ключ — это "preview",
        то содержимое его значения обрабатывается с использованием BeautifulSoup, и из HTML
        извлекается текст.

        Параметры:
            dictionary (Dict[str, str]): Словарь, содержащий ключи и значения, которые будут
                                         использованы для создания строки описания.
                                         Если ключ — "preview", его значение интерпретируется как HTML.

        Возвращает:
            str: Сформированное описание в виде строки. Каждый элемент словаря будет добавлен
                 как строка "ключ: значение", а для ключа "preview" извлекается только текст.

        Пример:
            dictionary = {
                "title": "Some title",
                "description": "Detailed description",
                "preview": "<p>Some HTML content</p>"
            }
            result = DescMakerService.make_desc(dictionary)
            # result == "title: Some title\ndescription: Detailed description\npreview: Some HTML content\n"
        """

        desc = []
        for key in dictionary:
            if key != "preview":
                desc.append(f"{key}: {dictionary[key]}" + '\n')
            else:
                res = BeautifulSoup(dictionary[key], "html.parser")
                text = res.get_text()
                desc.append(f"{key}: {text}" + '\n')
        return ''.join(desc)
