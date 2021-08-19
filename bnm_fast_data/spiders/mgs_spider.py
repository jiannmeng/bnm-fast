import re
from datetime import date
from decimal import Decimal

import scrapy
from bnm_fast_data import utils

START_DT = date(2021, 1, 1)
END_DT = date(2021, 1, 31)


class MgsSpider(scrapy.Spider):
    name = "mgs"

    def start_requests(self):
        for dt in utils.daterange(START_DT, END_DT):
            yield scrapy.Request(utils.url(200700000001, 82, dt), meta={"dt": dt})

    def parse(self, response):
        dt = response.meta["dt"]

        out = {"date": dt}
        if response.body:

            data = []
            table = response.xpath(r"//text()[. = 'TENOR']/../../..")
            for row in table.xpath("tr"):
                cols = row.xpath("td/text()").getall()  # eg. ['BNMN BAND 1', '1.757']
                if cols:
                    first, second = cols

                    # Instrument
                    instrument = first.split()[0]  # First word inside string `first`

                    # Tenor
                    num = re.findall(r"\d+", first)[0]
                    if "BAND" in first:
                        period = "M"
                    elif "YEAR" in first:
                        period = "Y"
                    else:
                        raise Exception
                    tenor = num + period

                    # YTM
                    ytm = Decimal(second)

                    data.append(
                        dict(instrument=instrument, tenor=tenor, ytm=ytm, rating="GOV")
                    )

            out["exists"] = True
            out["data"] = data
        else:
            out["exists"] = False

        yield out
