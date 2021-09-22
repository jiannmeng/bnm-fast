import requests
from bs4 import BeautifulSoup
from pathlib import Path
import logging
from rich import print

from rich.logging import RichHandler

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")

XML_FOLDER = Path("../xml")
CONSOLIDATED_IYTM_URL = "https://fast.bnm.gov.my/fastweb/public/FastPublicBrowseServlet.do?mode=MAIN&taskId=PB030100"
BROWSE_URL = "https://fast.bnm.gov.my/fastweb/public/FastPublicBrowseServlet.do"
INFO_URL = "https://fast.bnm.gov.my/fastweb/public/PublicInfoServlet.do"

# disable ssl warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def info_formdata(data_id: str) -> dict[str, str]:
    return dict(
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

def main():
    page_num = 1
    data_ids = set()
    while True:
        resp = requests.post(BROWSE_URL, data=browse_formdata(page_num), verify=False)
        page = BeautifulSoup(resp.text)
        checkboxes = page.find_all("input", id="chkBox")
        data_ids.update(cb["value"] for cb in checkboxes)
        next_page = page.find("a", string="[Next]")
        if next_page is None:
            break
        else:
            page_num += 1
        print(page_num)
    print(data_ids)
    pass


if __name__ == "__main__":
    main()
