import scrapy
from scrapy.http import FormRequest
import re
import jsonlines

# START_DT = date(2021, 1, 1)
# END_DT = date(2021, 1, 31)

BROWSE_URL = "https://fast.bnm.gov.my/fastweb/public/FastPublicBrowseServlet.do"
INFO_URL = "https://fast.bnm.gov.my/fastweb/public/PublicInfoServlet.do"
NUM_REGEX = re.compile(r"\d+")


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


class ConIytmSpider(scrapy.Spider):
    name = "con_iytm"

    def start_requests(self):
        yield FormRequest(
            url=BROWSE_URL, formdata=browse_formdata(1), callback=self.find_pages
        )

    def find_pages(self, response):
        elem = response.xpath("//a[contains(., '[Last]')]")
        last_page = int(elem.re_first(NUM_REGEX))
        for page in range(1, last_page + 1):
            yield FormRequest(
                url=BROWSE_URL,
                formdata=browse_formdata(page),
                callback=self.find_data_ids,
            )

    def find_data_ids(self, response):
        with jsonlines.open("test.jsonl", mode="r") as reader:
            scraped_ids = set(line["data_id"] for line in reader)
        rows = response.xpath("//input[@id='chkBox']/../..")
        for r in rows:
            data_id = r.xpath("td/input").attrib["value"]
            if data_id in scraped_ids:
                continue  # Already scraped, we can ignore it.
            # Otherwise, we add it to our list of pages to scrape.
            ytm_category, dt = r.xpath("descendant::*/text()").getall()

            # Dispatch to the correct parsing function based on ytm_category.
            # If no parsing function exists (i.e. None), don't yield anything and skip
            # this data_id
            cb_dispatch = {
                "Government Securities (Islamic) New": self.parse_gov,
                "Government Securities (Conventional) New": self.parse_gov,
            }
            cb_func = cb_dispatch.get(ytm_category, None)
            if cb_func is None:
                continue
            yield FormRequest(
                url=INFO_URL,
                encoding="windows-1252",
                formdata=info_formdata(data_id),
                callback=cb_func,
                meta={"out": dict(data_id=data_id, ytm_category=ytm_category, dt=dt)},
            )

    def parse_gov(self, response):
        out = response.meta["out"]
        out["data"] = []
        for ytm_details in response.xpath("//YTMResult/ytm/ytm_details"):
            rating = "GOV"
            instrument = ytm_details.xpath("profile_desc/text()").get().upper()
            desc = ytm_details.xpath("time_series_desc/text()").get().upper()
            if "BAND" in desc:
                period = "M"
            elif "YEAR" in desc:
                period = "Y"
            else:
                raise Exception
            tenor = re.findall(r"\d+", desc)[0] + period
            # Leave the ytm as string instead of converting to float or Decimal.
            ytm = ytm_details.xpath("ytm/text()").get()

            out["data"].append(
                dict(rating=rating, instrument=instrument, tenor=tenor, ytm=ytm)
            )
        yield out
