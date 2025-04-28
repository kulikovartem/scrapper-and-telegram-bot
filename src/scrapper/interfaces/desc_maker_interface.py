from typing import Protocol, Dict


class DescMaker(Protocol):

    """
        Протокол для классов, создающих строковое описание на основе словаря.

        Классы, реализующие этот протокол, должны предоставлять метод `make_desc`, который принимает
        словарь строковых значений и возвращает строку, содержащую структурированное описание.

        Методы:
            make_desc(dictionary: Dict[str, str]) -> str:
                Создает строковое описание из переданного словаря.

        Использование:
            Любой класс, реализующий данный протокол, должен реализовать метод `make_desc`,
            который преобразует данные в текстовый формат.

        Пример:
            class MyDescMaker(DescMaker):
                def make_desc(self, dictionary: Dict[str, str]) -> str:
                    return ", ".join(f"{key}: {value}" for key, value in dictionary.items())
    """

    def make_desc(self, dictionary: Dict[str, str]) -> str:
        pass
