import html

import scrapy
from scrapy.http import FormRequest
import re

# START_DT = date(2021, 1, 1)
# END_DT = date(2021, 1, 31)

FAST_URL = "https://fast.bnm.gov.my/fastweb/public/FastPublicBrowseServlet.do"
NUM_REGEX = re.compile(r"\d+")


def form(page: int) -> dict[str, str]:
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


class ConIytmSpider(scrapy.Spider):
    name = "con_iytm"

    def start_requests(self):
        yield FormRequest(url=FAST_URL, formdata=form(1), callback=self.find_pages)

    def find_pages(self, response):
        elem = response.xpath("//a[contains(., '[Last]')]")
        last_page = int(elem.re_first(NUM_REGEX))
        for page in range(1, last_page + 1):
            yield FormRequest(url=FAST_URL, formdata=form(page), callback=self.parse)

    def parse(self, response):
        checkboxes = response.css("#chkBox")
        for selector in checkboxes:
            value = html.escape(selector.attrib["value"])
            yield {"data_id": value}

        # out = {"date": dt}
        # if response.body:

        #     data = []
        #     table = response.xpath(r"//text()[. = 'TENOR']/../../..")
        #     for row in table.xpath("tr"):
        #         cols = row.xpath("td/text()").getall()  # eg. ['BNMN BAND 1', '1.757']
        #         if cols:
        #             first, second = cols

        #             # Instrument
        #             instrument = first.split()[0]  # First word inside string `first`

        #             # Tenor
        #             num = re.findall(r"\d+", first)[0]
        #             if "BAND" in first:
        #                 period = "M"
        #             elif "YEAR" in first:
        #                 period = "Y"
        #             else:
        #                 raise Exception
        #             tenor = num + period

        #             # YTM
        #             ytm = Decimal(second)

        #             data.append(
        #                 dict(instrument=instrument, tenor=tenor, ytm=ytm, rating="GOV")
        #             )

        #     out["exists"] = True
        #     out["data"] = data
        # else:
        #     out["exists"] = False

        # yield out
