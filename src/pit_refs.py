"""Reference share/free-float tables for ALL HOSE-Index stocks (VNAllShare sections), used to fill the
gap periods for which no VN30 CBTT PDF could be located."""
import re, sys
import pdfplumber, pandas as pd
sys.path.insert(0, "src")
from pit_parse import split_name_shares, shares
ROW3 = re.compile(r"^(\d{1,3})\s+([A-Z][A-Z0-9]{2})\s+(.*?)\s+(\d{1,3})%\s+([\d.]+)%.*$")
SRC = {"2018-01-22": "data/raw_pdf/p9/20180115_allshare.pdf", "2021-08-02": "data/raw_pdf/p2/20210719.pdf",
       "2022-08-01": "data/raw_pdf/p3/20220718.pdf"}
def allshare(path):
    cur=None; out=[]
    with pdfplumber.open(path) as p:
        for pg in p.pages:
            for l in (pg.extract_text() or "").split("\n"):
                m = re.search(r"(?:Chỉ số|Chi so)\s+(VN\w+)", l, re.I)
                if ("Danh mục" in l or "Danh muc" in l) and m: cur = m.group(1).upper()
                if "dự phòng" in l.lower(): cur = "RESERVE"
                r = ROW3.match(l.strip())
                if r and cur in ("VNALLSHARE", "VN30", "VNMIDCAP", "VNSMALLCAP", "VN100") or (r and "allshare" in path):
                    stt,tk,body,ff,cap = r.groups()
                    out.append(dict(ticker=tk, shares=shares(split_name_shares(body)), free_float=int(ff), cap_pct=float(cap), section=cur))
    return pd.DataFrame(out)
if __name__ == "__main__":
    rows=[]
    for d,f in SRC.items():
        t = allshare(f); t = t[t.section.isin(["VNALLSHARE"]) | t.section.isna() | (t.section!="RESERVE")] if "allshare" in f else t[t.section=="VNALLSHARE"]
        t = t.drop_duplicates("ticker"); t["ref_date"]=d; rows.append(t); print(d, len(t))
    pd.concat(rows).to_csv("data/raw_pdf/ref_allshare.csv", index=False)
