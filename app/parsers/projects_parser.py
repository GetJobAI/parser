from app.parsers.generic_list_parser import GenericListParser
from app.schemas.content import ProjectEntry, TextBlock


def _split_project(item: str) -> ProjectEntry:
    url = None
    url_match = None
    for marker in ("github.com/", "gitlab.com/", "bitbucket.org/", "http://", "https://"):
        if marker in item:
            start = item.find(marker)
            rest = item[start:]
            end = rest.find(" ")
            url_match = rest if end == -1 else rest[:end]
            break

    working = item.strip()
    if url_match:
        url = url_match.removeprefix("https://").removeprefix("http://").strip()
        working = working.replace(url_match, "").replace("  ", " ").strip(" -—")

    if "—" in working:
        name, description = [part.strip() for part in working.split("—", maxsplit=1)]
    elif "-" in working:
        name, description = [part.strip() for part in working.split("-", maxsplit=1)]
    else:
        name, description = working.strip(), None
    return ProjectEntry(name=name or None, description=description or None, url=url)


class ProjectsParser:
    def __init__(self) -> None:
        self._list_parser = GenericListParser()

    def parse(self, blocks: list[TextBlock]) -> list[ProjectEntry]:
        items = self._list_parser.parse_items(
            blocks,
            split_only_if_list_like=False,
            split_on_date_boundaries=True,
            max_item_length=260,
        )
        return [_split_project(item) for item in items]
