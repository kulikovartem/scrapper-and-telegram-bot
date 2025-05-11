#  type: ignore

import pytest
from src.scrapper.repos.orm_link_repo import OrmLinkRepo    #  type: ignore
from src.scrapper.repos.sql_link_repo import SqlLinkRepo    #  type: ignore
from src.scrapper.factories.repo_factory import RepoFactory


@pytest.mark.parametrize(
    "repo_type, expected_repo_class",
    [
        ('ORM', OrmLinkRepo),
        ('SQL', SqlLinkRepo),
    ]
)
def test_create_repo_success(repo_type, expected_repo_class):
    repo = RepoFactory.create(repo_type)
    assert isinstance(repo, expected_repo_class), f"Expected {expected_repo_class} but got {type(repo)}"


def test_create_repo_invalid_type():
    with pytest.raises(ValueError, match="Неизвестный тип репозитория"):
        RepoFactory.create('INVALID_TYPE')

