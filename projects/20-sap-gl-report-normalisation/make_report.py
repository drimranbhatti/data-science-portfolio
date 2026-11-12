"""Synthetic SAP Business One-style 'General Ledger' report export for a fictitious UAE manufacturer.

The real-world problem this reproduces: the GL report is exported in *report layout*, i.e. one block
per account with an account header row, transaction rows showing the offset account, a running
(cumulative) balance and a total row, rather than as a tidy table. Amounts are in AED with a separate
currency column. All companies, items and amounts are invented."""
from __future__ import annotations
import pathlib, random
from datetime import date, timedelta
import pandas as pd

OUT = pathlib.Path(__file__).resolve().parent / "data"
ACCTS = {"110100": ("Assets", "Bank - Operating Account"), "112000": ("Assets", "Accounts Receivable - Trade"),
         "131000": ("Assets", "Raw Materials"), "132000": ("Assets", "Finished Product"), "114500": ("Assets", "VAT Input 5%"),
         "208040": ("Liabilities", "Goods Received Not Invoiced (GRNI) Clearing"), "201000": ("Liabilities", "Accounts Payable - Trade"),
         "215000": ("Liabilities", "VAT Output 5%"), "400010": ("Revenue", "Sales - Finished Goods"),
         "500005": ("Expenses", "COSales - Finished Items"), "510000": ("Expenses", "Production Overhead Absorbed"),
         "300000": ("Equity", "Share Capital"), "610000": ("Expenses", "Salaries & Wages"), "620000": ("Expenses", "Rent"), "630000": ("Expenses", "Utilities")}
ITEMS = {"FG-100 Plastic crate": (14.0, 22.5), "FG-200 Storage drum": (38.0, 61.0), "FG-300 Pallet": (52.0, 79.0)}  # (std cost, price)
CUSTOMERS = ["C1001 Example Retail LLC", "C1002 Example Logistics FZE", "C1003 Example Foods Co.", "C1004 Example Hardware Trading"]


def build(seed: int = 3):
    rng = random.Random(seed)
    OUT.mkdir(exist_ok=True)
    tx, tno = [], 0
    docs = {"PD": 0, "PU": 0, "PR": 0, "DN": 0, "IN": 0, "RC": 0, "PS": 0, "JE": 0}

    def post(d, series, remarks, legs, due=None):
        nonlocal tno
        tno += 1; docs[series] += 1
        doc = f"{series} {docs[series] + (3200000 if series == 'DN' else 0)}"
        for acct, dr, cr, off in legs:
            tx.append({"date": d, "due": due or d, "doc": doc, "trans_no": tno, "remarks": remarks, "account": acct, "offset": off, "debit": dr, "credit": cr})
    grni_open, ap_open, ar_open = [], [], []
    d = date(2019, 6, 1)
    post(d, "JE", "Opening capital injection", [("110100", 1_500_000.0, 0, "300000"), ("300000", 0, 1_500_000.0, "110100")])
    while d <= date(2020, 12, 31):
        if d.weekday() == 4:   # Friday off
            d += timedelta(days=1); continue
        if rng.random() < 0.65:   # goods receipt PO: raw materials in, GRNI out
            amt = round(rng.uniform(6_000, 40_000), 2); po = f"Goods Receipt PO - 9000{rng.randint(1000, 9999)}"
            post(d, "PD", po, [("131000", amt, 0, "208040"), ("208040", 0, amt, "131000")]); grni_open.append((d, amt, po))
        if grni_open and rng.random() < 0.62:   # A/P invoice clears GRNI (oldest first), 5% VAT
            g = grni_open.pop(0 if rng.random() < 0.8 else -1); vat = round(g[1] * 0.05, 2)
            post(d, "PU", f"A/P Invoice - {g[2][-8:]}", [("208040", g[1], 0, "201000"), ("114500", vat, 0, "201000"), ("201000", 0, round(g[1] + vat, 2), "208040")], due=d + timedelta(days=45))
            ap_open.append((d + timedelta(days=45), round(g[1] + vat, 2)))
        for item, (cost, price) in ITEMS.items():
            if rng.random() < 0.45:   # production receipt then delivery and invoice
                q = rng.randint(50, 600); val = round(q * cost, 2)
                post(d, "PR", f"Receipt from Production - {item.split()[0]}", [("132000", val, 0, "131000"), ("131000", 0, round(val * 0.7, 2), "132000"), ("510000", 0, round(val * 0.3, 2), "132000")])
                cust = rng.choice(CUSTOMERS); qs = rng.randint(int(q * 0.6), q)
                post(d, "DN", f"Deliveries - {cust.split()[0]}", [("500005", round(qs * cost, 2), 0, "132000"), ("132000", 0, round(qs * cost, 2), "500005")])
                rev = round(qs * price * rng.uniform(0.95, 1.0), 2); vat = round(rev * 0.05, 2)
                post(d, "IN", f"A/R Invoice - {cust}", [("112000", round(rev + vat, 2), 0, "400010"), ("400010", 0, rev, "112000"), ("215000", 0, vat, "112000")], due=d + timedelta(days=60))
                ar_open.append((d + timedelta(days=rng.randint(45, 110)), round(rev + vat, 2)))
        for lst, series, legs_fn in [(ar_open, "RC", lambda a: [("110100", a, 0, "112000"), ("112000", 0, a, "110100")]),
                                     (ap_open, "PS", lambda a: [("201000", a, 0, "110100"), ("110100", 0, a, "201000")])]:
            due_now = [x for x in lst if x[0] <= d]
            if due_now:
                amt = round(sum(x[1] for x in due_now), 2)
                for x in due_now: lst.remove(x)
                post(d, series, "Incoming Payment" if series == "RC" else "Outgoing Payment", legs_fn(amt))
        if d.day == 28 or (d.day == 27 and (d + timedelta(days=1)).weekday() == 4):
            for a, lo, hi in [("610000", 60_000, 75_000), ("620000", 18_000, 18_000), ("630000", 3_000, 7_000)]:
                amt = round(rng.uniform(lo, hi), 2); post(d, "JE", f"Monthly accrual - {ACCTS[a][1]}", [(a, amt, 0, "110100"), ("110100", 0, amt, a)])
        d += timedelta(days=1)
    t = pd.DataFrame(tx)
    # report layout: one block per account, header row, rows with running balance, total row
    rows = []
    for acct in sorted(t.account.unique()):
        grp, name = ACCTS[acct]
        rows.append([grp, acct, None, None, None, name, None, None, None, None, None, None, "AED", 0.0])
        bal = 0.0
        for r in t[t.account == acct].sort_values(["date", "trans_no"]).itertuples():
            bal = round(bal + r.debit - r.credit, 2)
            rows.append([r.date.strftime("%d/%m/%Y"), r.due.strftime("%d/%m/%Y"), "Primary", r.doc, float(r.trans_no), r.remarks, float(r.offset), ACCTS[r.offset][1],
                         "AED" if r.debit else None, r.debit or None, "AED" if r.credit else None, r.credit or None, "AED", bal])
        sub = t[t.account == acct]
        rows.append(["Total", None, None, None, None, f"Total {acct} {name}", None, None, "AED", round(sub.debit.sum(), 2), "AED", round(sub.credit.sum(), 2), "AED", bal])
        rows.append([None] * 14)
    cols = ["Posting Date", "Due Date", "Series", "Doc. No.", "Trans. No.", "Remarks", "Offset Acct", "Offset Acct Name", "Debit (LC) (currency)", "Debit (LC)",
            "Credit (LC) (currency)", "Credit (LC)", "Cumulative Balance (LC) (currency)", "Cumulative Balance (LC)"]
    rep = pd.DataFrame(rows, columns=cols)
    # plant a corruption: one hand-edited amount, so the running balance and the double entry no longer tie
    i = rep.index[(rep["Doc. No."].astype(str).str.startswith("IN")) & rep["Credit (LC)"].notna()][40]
    rep.loc[i, "Credit (LC)"] = round(rep.loc[i, "Credit (LC)"] * 1.1, 2)
    rep.to_excel(OUT / "GL_report_export.xlsx", index=False)
    return t.shape, rep.shape


if __name__ == "__main__":
    print(build())
