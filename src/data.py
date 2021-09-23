import re
import xml.etree.ElementTree as etree
from dataclasses import dataclass
import csv
from pathlib import Path
from typing import Union

from rich import print

PathLike = Union[Path, str]

# df = pd.read_xml("tests/200500000018-17092001-00000043-Government Securities (Conventional)-17092001.xml")


XML_FOLDER = Path(__file__).resolve().parent.parent / "xml"
TENOR_Y_REGEX = re.compile(r"(\d+)Y")
TENOR_M_REGEX = re.compile(r"(\d+)M")
TENOR_YEAR_REGEXES = [
    re.compile(r"(\d+) YEAR"),  # 1 YEAR, 15 YEARS
    re.compile(r"^(\d+)$"),  # 3
]
TENOR_MONTH_REGEXES = [
    re.compile(r"BAND (\d+)"),  # BAND 1, BAND 10
]


class MissingInfoError(Exception):
    pass


def find_one(element, tag: str) -> str:
    element = element.find(tag)
    if element is None or element.text is None:
        raise MissingInfoError(f"Could not find {tag} in xml")
    return element.text


@dataclass
class Row:
    date: str
    category: str
    subcategory: str
    tenor: str
    ytm: str

    def __lt__(self, other):
        return (
            self.date,
            self.category,
            self.subcategory,
            self.tenor,
            self.ytm,
        ) < (other.date, other.category, other.subcategory, other.tenor, other.ytm)

    def writeout(self):
        return


def iter_xml(fp: PathLike):
    tree = etree.parse(fp)
    ytmresult = tree.getroot()
    for ytm in ytmresult.findall("ytm"):
        category = find_one(ytm, "category")
        date = find_one(ytm, "Date")
        for ytm_details in ytm.findall("ytm_details"):
            subcategory = find_one(ytm_details, "profile_desc")
            tenor = find_one(ytm_details, "time_series_desc")
            tenor = parse_tenor(tenor)
            ytm = find_one(ytm_details, "ytm")
            row = Row(
                date=date,
                category=category,
                subcategory=subcategory,
                tenor=parse_tenor(tenor),
                ytm=ytm,
            )
            yield row


def parse_tenor(tenor: str) -> str:
    for regex in TENOR_YEAR_REGEXES:
        if (match := regex.search(tenor)) is not None:
            return match.group(1) + "Y"
    for regex in TENOR_MONTH_REGEXES:
        if (match := regex.search(tenor)) is not None:
            return match.group(1) + "M"

    return tenor
    # raise MissingInfoError("No valid regex exists for this tenor")


def main():
    allrows: list[Row] = []
    num = 1
    for xml in XML_FOLDER.iterdir():
        num += 1
        allrows.extend(iter_xml(xml))
        if num % 1000 == 0:
            print(f"file {num}, allrows={len(allrows)}")
    allrows.sort()

    with open("result.csv", "w", newline="") as fp:
        writer = csv.writer(fp)
        for row in allrows:
            writer.writerow(
                (
                    row.date,
                    row.category,
                    row.subcategory,
                    row.tenor,
                    row.ytm,
                )
            )


if __name__ == "__main__":
    import time

    t0 = time.time()
    main()
    t1 = time.time()
    print(t1 - t0)
    # main()
