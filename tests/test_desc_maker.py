from typing import Dict
import pytest
from src.scrapper.services.desc_maker_service import DescMakerService


@pytest.fixture()
def desc_maker():
    return DescMakerService()


def test_make_desc_with_empty_preview(desc_maker):   # type: ignore
    dictionary: Dict[str, str] = {
        "title": "Some title",
        "description": "Detailed description",
        "preview": ""
    }
    result = desc_maker.make_desc(dictionary)
    expected_result = "title: Some title\n" \
                      "description: Detailed description\n" \
                      "preview: \n"
    assert result == expected_result


def test_make_desc_without_preview_key(desc_maker):   # type: ignore
    dictionary: Dict[str, str] = {
        "title": "Some title",
        "description": "Detailed description"
    }
    result = desc_maker.make_desc(dictionary)
    expected_result = "title: Some title\n" \
                      "description: Detailed description\n"
    assert result == expected_result
# type: ignore


def test_make_desc_with_only_preview(desc_maker):  # type: ignore
    dictionary: Dict[str, str] = {
        "preview": "<p>Preview content with <b>HTML</b></p>"
    }
    result = desc_maker.make_desc(dictionary)
    expected_result = "preview: Preview content with HTML\n"
    assert result == expected_result


def test_make_desc_empty_dict(desc_maker):  # type: ignore
    dictionary: Dict[str, str] = {}
    result = desc_maker.make_desc(dictionary)
    expected_result = ""
    assert result == expected_result

