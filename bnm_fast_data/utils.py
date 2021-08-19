from datetime import timedelta, date


def daterange(start: date, end: date) -> list[date]:
    return [start + timedelta(n) for n in range(int((end - start).days))]


def url(id1: int, id2: int, dt: date) -> str:
    return (
        r"https://fast.bnm.gov.my/fastweb/public/PublicInfoServlet.do?"
        rf"chkBox={id1}"
        rf"%E6{dt.day:02}%2F{dt.month:02}%2F{dt.year:04}%E6"
        rf"{id2:08}"
        r"&mode=DISPLAY&info=INDYTM&screenId=PB030100"
    )


def section_url(id: str) -> str:
    return (
        r"https://fast.bnm.gov.my/fastweb/public/FastPublicBrowseServlet.do?"
        rf"mode=MAIN&taskId={id}"
    )
