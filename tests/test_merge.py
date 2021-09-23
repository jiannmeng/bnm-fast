from src.flatten import Row, iter_xml, parse_tenor
from datetime import date
from decimal import Decimal

GOV_CONV_OLD_FILE = "tests/200500000018-17092001-00000043-Government Securities (Conventional)-17092001.xml"


def test_gov_old():
    result = iter_xml(GOV_CONV_OLD_FILE)
    assert (
        Row(
            date=date(2001, 9, 17),
            category="Government Securities (Conventional)",
            subcategory="MGS",
            tenor="5Y",
            ytm=Decimal("3.359"),
        )
        in result
    )
    assert (
        Row(
            date=date(2001, 9, 17),
            category="Government Securities (Conventional)",
            subcategory="MTB",
            tenor="10M",
            ytm=Decimal("2.885"),
        )
        in result
    )

def test_parse_tenor():
    assert parse_tenor('- 1 YEAR') == "1Y"
    assert parse_tenor('- 15 YEARS') == "15Y"
    assert parse_tenor('- BAND 1') == "1M"
    assert parse_tenor('- BAND 10') == "10M"
