import asyncio
import logging
from pathlib import Path
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup
from rich import print
from rich.logging import RichHandler

logging.basicConfig(
    level="DEBUG",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("rich")

XML_FOLDER = Path(__file__).resolve().parent.parent / "xml"
BROWSE_URL = "https://fast.bnm.gov.my/fastweb/public/FastPublicBrowseServlet.do"
INFO_URL = "https://fast.bnm.gov.my/fastweb/public/PublicInfoServlet.do"


# 200500000021æ07052021æ00000088èCorporate Bond
def to_xml_name(id: str) -> str:
    """Convert an encoded id from FAST website into filesystem-safe name with .xml
    extension.

    e.g. 200500000021æ14/09/2021æ00000088èCorporate Bond Ratingsè14/09/2021
    becomes 200500000021-14092021-00000088-Corporate Bond Ratings-14092021.xml
    """
    return id.replace("/", "").replace("æ", "-").replace("è", "-") + ".xml"


def browse_formdata(page: int) -> dict[str, str]:
    return dict(
        configButton="false",
        drawCheckBox="Y",
        linkButton="FIND",
        mode="MAIN",
        screenId="PB030100",
        taskId="PB030100",
        txtDefaultCriteria="",
        txtPageIndex=str(page),
        txtPageRange="1",
        txtRecPerPage="50",
        txtSearchCriteria="",
        txtSortingColumn="-1",
        txtSortingOrder="0",
        txtStartPageIndex="1",
    )


def info_formdata(data_id: str) -> str:
    data = dict(
        chkBox=data_id,
        taskId="PB030100",
        mode="FIND",
        linkButton="JOB46",
        screenId="PB030100",
        drawCheckBox="Y",
        configButton="false",
        txtHeader="YTM+Category%E8Consolidation+Date",
        txtHeaderLength="75%25%E825%25",
        txtHeaderAlign="LEFT%E8center",
        txtRecPerPage="50",
        txtStartPageIndex="1",
        txtPageIndex="1",
        txtPageRange="1",
        txtSortingColumn="-1",
        txtSortingOrder="0",
        txtDefaultCriteria="",
        txtSearchCriteria="",
    )

    data = {k: quote(v, encoding="windows-1252") for k, v in data.items()}

    x = "&".join("=".join(i) for i in data.items())
    return x


async def main():
    first_page = httpx.post(BROWSE_URL, data=browse_formdata(1), verify=False)
    soup = BeautifulSoup(first_page.text)
    last = soup.find("a", string="[Last]")
    last_page_num = 3
    # last_page_num = int(re.search(r"\d+", last["href"]).group(0))

    retreived_ids = set()

    async def get_page(page_num: int):
        async with httpx.AsyncClient(verify=False) as client:
            print(f"page {page_num}")
            response = await client.post(BROWSE_URL, data=browse_formdata(page_num))
            page = BeautifulSoup(response.text, features="html.parser")
            checkboxes = page.find_all("input", id="chkBox")
            # return [cb["values"] for cv in checkboxes]
            retreived_ids.update(cb["value"] for cb in checkboxes)

    tasks = [get_page(num) for num in range(1, last_page_num + 1)]
    await asyncio.gather(*tasks)

    # deduplicate
    downloaded_ids = set()
    new_ids = set()
    for xml in XML_FOLDER.iterdir():
        downloaded_ids.add(xml.name)
    for data_id in retreived_ids:
        if to_xml_name(data_id) not in downloaded_ids:
            new_ids.add(data_id)

    async def get_xml(data_id: str):
        async with httpx.AsyncClient(verify=False) as client:
            print(f"downloading {data_id}")

            response = await client.post(
                INFO_URL,
                content=info_formdata(data_id),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                },
            )
            with open(XML_FOLDER / to_xml_name(data_id), "wb") as f:
                f.write(response.content)

    tasks = [get_xml(data_id) for data_id in new_ids]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
