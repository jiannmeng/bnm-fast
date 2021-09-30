import csv
import re
import xml.etree.ElementTree as etree
from collections import namedtuple
from pathlib import Path
from typing import Iterator, Union
import pandas as pd

from rich import print

from bnm_fast.common import OUTPUT_FOLDER, XML_FOLDER, logger

PathLike = Union[Path, str]
Row = namedtuple("Row", "date category subcategory tenor ytm")

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


def iter_xml(fp: PathLike) -> Iterator[Row]:
    fp = Path(fp)
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
                subcategory=subcategory.upper(),
                tenor=tenor,
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
    raise MissingInfoError("No valid regex exists for this tenor")


def main():
    rows: list[Row] = []
    count = 0
    for path in XML_FOLDER.iterdir():
        if path.suffix != ".xml":
            continue
        count += 1
        rows.extend(iter_xml(path))  # Add the rows to the list
        if count % 1000 == 0:
            logger.info(f"At {count} xml files: {len(rows)} rows so far")
    logger.info(f"Total: {count} xml files, {len(rows)} rows")

    def row_sort(elem: Row):
        return (
            elem.date,
            elem.category,
            elem.subcategory,
            elem.tenor[-1],
            int(elem.tenor[:-1]),
            elem.ytm,
        )

    rows.sort(key=row_sort)
    logger.info("Sorted all rows")

    csv_path = OUTPUT_FOLDER / "consolidated_iytm.csv"
    logger.info("Creating CSV file...")
    with open(csv_path, "w", newline="") as fp:
        writer = csv.writer(fp)
        writer.writerow(Row._fields)  # Header row
        for row in rows:
            writer.writerow(row)
    logger.info(f"CSV saved to {csv_path}")

    # Excel
    df = pd.read_csv(OUTPUT_FOLDER / "consolidated_iytm.csv")
    df.date = pd.to_datetime(df.date, format="%Y%m%d")
    df = df.astype({"ytm": float})

    xlsx_path = OUTPUT_FOLDER / "consolidated_iytm.xlsx"
    logger.info("Creating XLSX file...")
    with pd.ExcelWriter(xlsx_path, datetime_format="YYYY-MM-DD") as writer:
        df.to_excel(writer, index=False)
    logger.info(f"XLSX saved to {xlsx_path}")


if __name__ == "__main__":
    import time

    t0 = time.time()
    main()
    t1 = time.time()
    print(t1 - t0)
