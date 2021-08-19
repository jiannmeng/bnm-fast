from datetime import date
from decimal import Decimal

import scrapy
from bnm_fast_data import utils

START_DT = date(2021, 1, 1)
END_DT = date(2021, 1, 31)


class CorpSpider(scrapy.Spider):
    name = "corp"

    def start_requests(self):
        for dt in utils.daterange(START_DT, END_DT):
            yield scrapy.Request(utils.url(200500000021, 88, dt), meta={"dt": dt})

    def parse(self, response):
        dt = response.meta["dt"]

        out = {"date": dt}
        if response.body:

            data = []
            table = response.xpath(r"//text()[. = 'RATINGS']/../../..")

            # Get the tenors
            tenors = table.xpath("th/text()").getall()  # ['3', '5', '7', '10', '15']
            tenors = [t + "Y" for t in tenors]  # '3' -> '3Y'

            instrument = "CORP"

            for row in table.xpath("tr"):
                cols = row.xpath("td/text()").getall()  # eg. ['BNMN BAND 1', '1.757']
                if cols:
                    rating, *ytms = cols
                    for tenor, ytm in zip(tenors, ytms):
                        ytm = Decimal(ytm)
                        data.append(
                            dict(
                                instrument=instrument,
                                tenor=tenor,
                                ytm=ytm,
                                rating=rating,
                            )
                        )

            out["exists"] = True
            out["data"] = data
        else:
            out["exists"] = False

        yield out
