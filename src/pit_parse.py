"""Parse HOSE 'CBTT Danh sach thanh phan VN30' PDFs (own parser; VN25 Script 1 is not in the repo)."""
import re, glob, sys
from pathlib import Path
import pdfplumber, pandas as pd

ROW = re.compile(r"^(\d{1,2})\s+([A-Z][A-Z0-9]{2})\s+(.*?)\s+(\d{1,3})%\s+([\d.]+)%.*$")
PERIOD = {"20180115":"2018-01-22","20210719":"2021-08-02","20220718":"2022-08-01","20230116":"2023-02-06",
          "20230717":"2023-08-07","20240115":"2024-02-05","20240715":"2024-08-05","20250120":"2025-02-03"}

def split_name_shares(body):
    """body = '<name> <shares>' ; shares = last token (+ preceding token iff it is a single digit)."""
    tk = body.split()
    last = tk[-1]
    if len(tk) >= 2 and re.fullmatch(r"\d", tk[-2]): last = tk[-2] + last
    return last
def shares(s):
    # share count is printed with ONE stray space after its first digit ("3 ,418,715,334", "8 1,860,938").
    s = s.strip()
    m = re.match(r"^(\d) ([\d,]+)$", s)
    s = (m.group(1)+m.group(2)) if m else s
    return int(s.replace(",","").replace(" ",""))

def parse(path):
    out=[]
    with pdfplumber.open(path) as p:
        n = 2 if "20180115" in str(path) else 1
        lines=[]
        for pg in p.pages[:n]: lines += (pg.extract_text() or "").split("\n")
    for l in lines:
        if "dự phòng" in l.lower() and out: break
        m = ROW.match(l.strip())
        if not m: continue
        stt,tk,body,ff,cap = m.groups()
        out.append(dict(ticker=tk,shares=shares(split_name_shares(body)),free_float=int(ff),cap_pct=float(cap),stt=int(stt)))
    return out

if __name__=="__main__":
    rows=[]
    for f in sorted(glob.glob("data/raw_pdf/*/*.pdf")):
        key=Path(f).stem
        r=parse(f)
        print(key,len(r),"rows; names:",[x['ticker'] for x in r if x['stt']>=30][:3], "stt max",max(x['stt'] for x in r))
        for x in r: rows.append(dict(period_key=key,effective=PERIOD[key],**x))
    pd.DataFrame(rows).to_csv("data/raw_pdf/parsed_pdfs.csv",index=False)
