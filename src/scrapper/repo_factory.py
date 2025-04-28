from src.scrapper.interfaces.link_repo_interface import LinkRepo
from src.scrapper.repos.orm_link_repo import OrmLinkRepo
from src.scrapper.repos.sql_link_repo import SqlLinkRepo


class RepoFactory:
    """
    Фабрика для создания репозиториев. В зависимости от типа репозитория (ORM или SQL),
    создается соответствующий объект репозитория.

    Методы:
        create(repo_type: str) -> LinkRepo: Создает экземпляр репозитория в зависимости от переданного типа.
    """

    @staticmethod
    def create(repo_type: str) -> LinkRepo:
        """
        Создает экземпляр репозитория в зависимости от переданного типа репозитория.

        Параметры:
            repo_type (str): Тип репозитория, который должен быть создан. Поддерживаются 'ORM' и 'SQL'.

        Возвращает:
            LinkRepo: Экземпляр соответствующего репозитория (OrmLinkRepo или SqlLinkRepo).

        Исключения:
            ValueError: Если передан неизвестный тип репозитория.
        """
        if repo_type == 'ORM':
            return OrmLinkRepo()
        elif repo_type == 'SQL':
            return SqlLinkRepo()
        else:
            raise ValueError(f"Неизвестный тип репозитория")
