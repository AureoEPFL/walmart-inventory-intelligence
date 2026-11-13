"""Retrieve Nixtla's public M5 archive, pin commit and record content SHA256.

No credentials. Original data rights remain with their owners; do not redistribute.
Only allowlisted CSVs are extracted, never archive paths.
"""
import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

FILES = {"sales_train_evaluation.csv", "sales_train_validation.csv", "calendar.csv", "sell_prices.csv"}

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "InventoryIntelligence/0.1"}), timeout=120)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", default="data/raw")
    parser.add_argument("--commit", help="Optional immutable Nixtla/m5-forecasts commit")
    args=parser.parse_args(); root=Path(args.output);root.mkdir(parents=True,exist_ok=True)
    manifest=root/"manifest.json"
    if manifest.exists() and (root/"sales_train_evaluation.csv").exists():
        print("Existing dataset preserved; manifest:",manifest);return
    if args.commit:
        commit=args.commit
    else:
        with fetch("https://api.github.com/repos/Nixtla/m5-forecasts/commits/main") as r:commit=json.load(r)["sha"]
    if len(commit)!=40 or any(c not in "0123456789abcdef" for c in commit):raise ValueError("Expected full commit SHA")
    url=f"https://raw.githubusercontent.com/Nixtla/m5-forecasts/{commit}/datasets/m5.zip"
    archive=root/"m5.zip";partial=root/"m5.zip.partial";digest=hashlib.sha256();size=0
    print("Downloading",url,flush=True)
    with fetch(url) as r,partial.open("wb") as f:
        while chunk:=r.read(1024*1024):
            size+=len(chunk)
            if size>1024**3:raise ValueError("Archive exceeds 1 GB limit")
            digest.update(chunk);f.write(chunk)
    partial.replace(archive)
    extracted={}
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            name=Path(member.filename).name
            if name not in FILES:continue
            if name in extracted:raise ValueError("Duplicate filename in archive")
            if member.file_size>2*1024**3:raise ValueError("CSV too large")
            target=root/name
            with z.open(member) as source,target.open("wb") as out:shutil.copyfileobj(source,out)
            extracted[name]=hashlib.sha256(target.read_bytes()).hexdigest()
    if "sales_train_evaluation.csv" not in extracted:raise ValueError("Missing evaluation sales file")
    manifest.write_text(json.dumps({"url":url,"commit":commit,"archive_sha256":digest.hexdigest(),"bytes":size,"files":extracted,"retrieved_utc":datetime.now(timezone.utc).isoformat()},indent=2),encoding="utf-8")
    print("Downloaded and fingerprinted",size,"bytes;",len(extracted),"CSVs",flush=True)

if __name__=="__main__":main()
