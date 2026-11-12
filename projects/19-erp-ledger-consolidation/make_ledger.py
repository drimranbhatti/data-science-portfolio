"""Synthetic multi-file ERP ledger export for a fictitious Saudi contracting company.

Mimics the *shape* of real ERP exports (transaction types, 8-digit account codes, cost centres,
SAR amounts written as text, dd-mm-yyyy dates, bilingual Arabic/English narration) and the
problems typical of them: overlapping export files, inconsistent encodings, VAT-rate errors around
the July 2020 change from 5% to 15%, unbalanced vouchers and a voucher missing from the CSV
exports but present in the PDF trial balance. Every name and amount is invented."""
from __future__ import annotations
import pathlib, random
from datetime import date, timedelta
import pandas as pd

OUT = pathlib.Path(__file__).resolve().parent / "data"
COA = {  # code: (name, type)
    "11010001": ("Cash in Hand - Riyadh", "asset"), "11020001": ("Bank - Example National Bank", "asset"),
    "11020002": ("Bank - Example Islamic Bank", "asset"), "11510001": ("Advances to Suppliers", "asset"),
    "12170001": ("VAT Input Tax - On Purchases", "asset"), "13010001": ("Inventory - Construction Materials", "asset"),
    "21010001": ("Trade Payables", "liability"), "21270001": ("VAT Output Tax - On Sales", "liability"),
    "21300001": ("Advances from Customers", "liability"), "21500001": ("Retention Payable", "liability"),
    "22010001": ("End of Service Benefits Provision", "liability"), "31010001": ("Share Capital", "equity"),
    "41010001": ("Contract Revenue", "revenue"), "41020001": ("Maintenance Revenue", "revenue"),
    "51010001": ("Direct Materials", "cost"), "51020001": ("Subcontractor Costs", "cost"), "51030001": ("Direct Labour", "cost"),
    "51040001": ("Equipment Hire", "cost"), "61010001": ("Salaries - Admin", "expense"), "61020001": ("Office Rent", "expense"),
    "61030001": ("Utilities", "expense"), "61040001": ("Bank Charges", "expense"), "61050001": ("Travel", "expense"),
}
CUSTOMERS = [("12500101", "Customer A - City Municipality", "عميل أ - أمانة المدينة"), ("12500102", "Customer B - Regional Water Authority", "عميل ب - هيئة المياه"),
             ("12500103", "Customer C - Industrial Estates Co.", "عميل ج - شركة المدن الصناعية"), ("12500104", "Customer D - Private Developer", "عميل د - مطور عقاري"),
             ("12500105", "Customer E - Hospital Trust", "عميل هـ - مستشفى")]
for code, name, _ in CUSTOMERS: COA[code] = (f"ACC.R - {name}", "asset")
PROJECTS = ["PRJ-01 Road Rehabilitation Phase 1", "PRJ-02 Water Network Extension", "PRJ-03 Industrial Warehouse",
            "PRJ-04 Residential Compound", "PRJ-05 Clinic Fit-out", "HO - Head Office"]
PROJ_CUST = dict(zip(PROJECTS[:5], [c[0] for c in CUSTOMERS]))
AR_NARR = {"CUSTOMER INVOICE": "فاتورة عميل : مستخلص رقم", "RECEIPT FROM CUSTOMER": "تحصيل من العميل", "SUPPLIER INVOICE": "فاتورة مورد",
           "PAYMENT TO SUPPLIER": "سداد للمورد", "MANUAL JOURNAL": "قيد يومية", "BANK PAYMENT": "دفع بنكي", "CASH PAYMENT": "مصروف نقدي"}


def vat_rate(d: date) -> float:
    return 0.15 if d >= date(2020, 7, 1) else 0.05


def build(seed: int = 7):
    rng = random.Random(seed)
    OUT.mkdir(exist_ok=True)
    lines, vno = [], {"CI": 0, "SI": 0, "RC": 0, "PS": 0, "MJ": 0, "BP": 0, "CP": 0}
    truth = []

    def add(ttype, prefix, d, cc, legs, narr_en, issue=""):
        vno[prefix] += 1
        v = f"{prefix}{d.year % 100:02d}{vno[prefix]:06d}"
        for acct, dr, cr in legs:
            lines.append({"Transaction Type": ttype, "Voucher No": v, "Date": d, "Account Code": acct, "Account Name": COA[acct][0],
                          "Cost Center": cc, "Currency": "Saudi Riyal", "Narration": f"{AR_NARR.get(ttype, '')} : {narr_en}",
                          "Debit": dr, "Credit": cr})
        if issue: truth.append({"voucher": v, "issue": issue})
        return v

    d = date(2018, 1, 1)
    while d <= date(2021, 12, 31):
        if d.weekday() in (4, 5):  # Friday/Saturday weekend
            d += timedelta(days=1); continue
        for _ in range(rng.randint(1, 4)):
            r = rng.random(); cc = rng.choice(PROJECTS[:5])
            if r < 0.12:   # progress-billing invoice
                net = round(rng.lognormvariate(12.2, 0.8), 2); rate = vat_rate(d); issue = ""
                if d >= date(2020, 7, 1) and rng.random() < 0.10: rate, issue = 0.05, "vat_old_rate_after_change"
                vat = round(net * rate, 2)
                add("CUSTOMER INVOICE", "CI", d, cc, [(PROJ_CUST[cc], net + vat, None), ("41010001", None, net), ("21270001", None, vat)],
                    f"Progress claim {rng.randint(1, 30)} - {cc.split(' ', 1)[1]}", issue)
            elif r < 0.22:  # customer receipt
                amt = round(rng.lognormvariate(12.0, 0.8), 2)
                add("RECEIPT FROM CUSTOMER", "RC", d, cc, [("11020001", amt, None), (PROJ_CUST[cc], None, amt)], "Collection against claims")
            elif r < 0.45:  # supplier invoice (materials / subcontractor) with input VAT
                net = round(rng.lognormvariate(10.8, 1.0), 2); vat = round(net * vat_rate(d), 2)
                acct = rng.choice(["51010001", "51020001", "51040001"])
                add("SUPPLIER INVOICE", "SI", d, cc, [(acct, net, None), ("12170001", vat, None), ("21010001", None, net + vat)], f"Supplier bill - {COA[acct][0]}")
            elif r < 0.60:
                amt = round(rng.lognormvariate(10.9, 0.9), 2)
                add("PAYMENT TO SUPPLIER", "PS", d, cc, [("21010001", amt, None), ("11020002", None, amt)], "Supplier payment")
            elif r < 0.75:
                amt = round(rng.lognormvariate(9.5, 0.7), 2); acct = rng.choice(["51030001", "61010001", "61020001", "61030001", "61050001"])
                cc2 = "HO - Head Office" if acct.startswith("61") else cc
                add("BANK PAYMENT", "BP", d, cc2, [(acct, amt, None), ("11020001", None, amt)], COA[acct][0])
            elif r < 0.80:
                amt = round(rng.uniform(20, 400), 2)
                add("CASH PAYMENT", "CP", d, "HO - Head Office", [("61050001", amt, None), ("11010001", None, amt)], "Petty cash")
            else:
                amt = round(rng.lognormvariate(8.0, 0.6), 2)
                add("MANUAL JOURNAL", "MJ", d, "HO - Head Office", [("61040001", amt, None), ("11020001", None, amt)], "Bank charges")
        d += timedelta(days=1)
    gl = pd.DataFrame(lines)
    # unbalanced vouchers: drop one leg from 4 manual journals (export truncation)
    mj = gl[gl["Transaction Type"] == "MANUAL JOURNAL"]["Voucher No"].drop_duplicates().sample(4, random_state=seed).tolist()
    for v in mj:
        gl = gl.drop(gl[(gl["Voucher No"] == v)].index[-1]); truth.append({"voucher": v, "issue": "unbalanced"})
    # one voucher present in the ERP but missing from the CSV exports (shows up only in the PDF trial balance)
    missing = gl[(gl["Transaction Type"] == "CUSTOMER INVOICE") & (gl.Date.astype(str).str.startswith("2021-11"))]["Voucher No"].iloc[0]
    truth.append({"voucher": missing, "issue": "missing_from_csv_export"})
    full = gl.copy()
    gl = gl[gl["Voucher No"] != missing]

    def fmt(x):
        return "" if pd.isna(x) else f"{x:,.2f}"
    # five export files by period, with overlapping months and different encodings
    cuts = [("2018-01-01", "2018-12-31", "utf-8-sig"), ("2018-12-01", "2019-12-31", "utf-8-sig"), ("2019-12-01", "2020-12-31", "cp1256"),
            ("2021-01-01", "2021-06-30", "utf-8-sig"), ("2021-06-01", "2021-12-31", "utf-8-sig")]
    for i, (a, b, enc) in enumerate(cuts, 1):
        part = gl[(gl.Date >= date.fromisoformat(a)) & (gl.Date <= date.fromisoformat(b))].copy()
        part["Date"] = pd.to_datetime(part["Date"]).dt.strftime("%d-%m-%Y")
        part["Balance"] = (part["Debit"].fillna(0) - part["Credit"].fillna(0)).map(lambda x: f"{x:,.2f}")
        part["Debit"], part["Credit"] = part["Debit"].map(fmt), part["Credit"].map(fmt)
        part.to_csv(OUT / f"export_{i}.csv", index=False, encoding=enc)
    pd.DataFrame(truth).to_csv(OUT / "planted_issues.csv", index=False)
    # PDF trial balance for November 2021 (period movements), generated from the *full* ERP ledger
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    nov = full[(pd.to_datetime(full.Date) >= "2021-11-01") & (pd.to_datetime(full.Date) <= "2021-11-30")]
    tb = nov.groupby("Account Code").agg(debit=("Debit", "sum"), credit=("Credit", "sum")).reset_index()
    c = canvas.Canvas(str(OUT / "trial_balance_2021_11.pdf"), pagesize=A4)
    c.setFont("Helvetica-Bold", 13); c.drawString(40, 800, "Example Contracting Co. - Trial Balance (period movements)")
    c.setFont("Helvetica", 10); c.drawString(40, 784, "Period: 01-11-2021 to 30-11-2021    Currency: SAR")
    y = 755; c.setFont("Helvetica-Bold", 9)
    for x, h in [(40, "Account"), (110, "Account Name"), (400, "Debit"), (490, "Credit")]: c.drawString(x, y, h)
    c.setFont("Helvetica", 9)
    for r in tb.itertuples():
        y -= 14; c.drawString(40, y, r[1]); c.drawString(110, y, COA[r[1]][0][:48]); c.drawRightString(460, y, f"{r.debit:,.2f}"); c.drawRightString(550, y, f"{r.credit:,.2f}")
    y -= 18; c.setFont("Helvetica-Bold", 9); c.drawString(110, y, "TOTAL"); c.drawRightString(460, y, f"{tb.debit.sum():,.2f}"); c.drawRightString(550, y, f"{tb.credit.sum():,.2f}")
    c.save()
    pd.DataFrame([(k, v[0], v[1]) for k, v in COA.items()], columns=["account_code", "account_name", "type"]).to_csv(OUT / "chart_of_accounts.csv", index=False)
    return gl.shape


if __name__ == "__main__":
    print(build())
