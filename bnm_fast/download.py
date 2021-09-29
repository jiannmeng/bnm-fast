import asyncio
import re
from urllib.parse import quote
from bs4.element import NavigableString

import httpx
from bs4 import BeautifulSoup

from bnm_fast.common import XML_FOLDER, logger


BROWSE_URL = "https://fast.bnm.gov.my/fastweb/public/FastPublicBrowseServlet.do"
INFO_URL = "https://fast.bnm.gov.my/fastweb/public/PublicInfoServlet.do"

MAX_CONCURRENT_TASKS = 8  # Any higher is too much for BNM's servers...
HTTP_TIMEOUT_SECS = 30


class WebsiteError(Exception):
    pass


def to_xml_name(fast_id: str) -> str:
    """Convert an encoded id from FAST website into filesystem-safe name with .xml
    extension.

    e.g. 200500000021æ14/09/2021æ00000088èCorporate Bond Ratingsè14/09/2021
    becomes 200500000021-14092021-00000088-Corporate Bond Ratings-14092021.xml
    """
    return fast_id.replace("/", "").replace("æ", "-").replace("è", "-") + ".xml"


def browse_form(page: int) -> dict[str, str]:
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


def info_form_str(data_id: str) -> str:
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


async def gather_with_concurrency(n: int, *tasks):
    """Asyncio gather, but with a limit of how many tasks can run concurrently.

    Ref: https://stackoverflow.com/a/61478547
    """
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


async def main():
    # Load the Consolidated IYTM main page, and find the page number of the last page
    page = httpx.post(BROWSE_URL, data=browse_form(1), verify=False)
    soup = BeautifulSoup(page.text, features="html.parser")
    last_elem = soup.find("a", string="[Last]")
    if isinstance(last_elem, NavigableString) or last_elem is None:
        raise WebsiteError("Could not find a DOM element containing string [Last]")
    last_js = last_elem.attrs["href"]
    last_match = re.search(r"\d+", last_js)
    if last_match is None:
        raise WebsiteError("DOM element containing [Last] did not have a page number")
    last_page = int(last_match.group(0))
    logger.info(f"Consolidated IYTM has {last_page} pages")

    # Paginate through all the pages and determine the set of all valid FAST IDs
    fast_ids = set()

    async def get_page(page_num: int):
        async with httpx.AsyncClient(verify=False, timeout=HTTP_TIMEOUT_SECS) as client:
            logger.info(f"Accessing page {page_num} of Consolidated IYTM listing")
            response = await client.post(BROWSE_URL, data=browse_form(page_num))
            page = BeautifulSoup(response.text, features="html.parser")
            checkboxes = page.find_all("input", id="chkBox")
            # return [cb["values"] for cv in checkboxes]
            fast_ids.update(cb["value"] for cb in checkboxes)  # type:ignore

    tasks = [get_page(num) for num in range(1, last_page + 1)]
    await gather_with_concurrency(MAX_CONCURRENT_TASKS, *tasks)
    # At this point, fast_ids will have all of the ids available on FAST website

    # Now, we check which ids we have already downloaded
    downloaded_xmls = set()
    new_ids = set()
    for xml in XML_FOLDER.iterdir():
        downloaded_xmls.add(xml.name)
    for data_id in fast_ids:
        if to_xml_name(data_id) not in downloaded_xmls:
            new_ids.add(data_id)

    # Download all of the remaining xml files, and save to disk
    async def get_xml(fast_id: str):
        async with httpx.AsyncClient(verify=False, timeout=HTTP_TIMEOUT_SECS) as client:
            logger.info(f"Downloading new id: {fast_id}")

            # httpx requests using the data parameter sends a url-encoded form with
            # utf-8 encoding. Unfortunately, the FAST id uses Windows-1252 encoding,
            # so we need to send a properly encoded string and the appropriate headers
            # instead.
            response = await client.post(
                INFO_URL,
                content=info_form_str(fast_id),
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                },
            )

            # Save the file to the xml folder
            xml_path = XML_FOLDER / to_xml_name(fast_id)
            with open(xml_path, "wb") as f:
                f.write(response.content)
            logger.info(f"XML saved to {xml_path}")

    tasks = [get_xml(data_id) for data_id in new_ids]
    await gather_with_concurrency(MAX_CONCURRENT_TASKS, *tasks)


if __name__ == "__main__":
    asyncio.run(main())
