from typing import Protocol
from typing import List, Tuple, Dict
from src.scrapper.schemas.link_dto import LinkDTO


class UpdateSender(Protocol):

    def send_update_request(self, links_info: List[Tuple[LinkDTO, Dict[str, str]]]) -> None:
        pass
