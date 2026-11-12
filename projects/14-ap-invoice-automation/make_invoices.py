"""Generate a synthetic accounts-payable dataset: vendor master, purchase orders, goods receipts
and invoice PDFs in three different vendor layouts, with known problems planted for testing.
Everything is fictitious; run `python make_invoices.py` to rebuild data/."""
from __future__ import annotations
import json, pathlib, random
from datetime import date, timedelta
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

OUT = pathlib.Path(__file__).resolve().parent / "data"
VENDORS = [
    ("V001", "Northwind Office Supply LLC", "Net 30", "****4421"), ("V002", "Bluepeak IT Services Inc", "Net 45", "****9087"),
    ("V003", "Harbor Janitorial Co", "Net 15", "****1132"), ("V004", "Summit Print & Mail", "Net 30", "****7765"),
    ("V005", "Keystone Facilities Group", "Net 30", "****3310"), ("V006", "Redline Courier Services", "Net 15", "****5528"),
    ("V007", "Greenfield Catering LLC", "Net 30", "****2049"), ("V008", "Atlas Software Licensing", "Net 60", "****6671"),
    ("V009", "Pioneer Electrical Contractors", "Net 30", "****8893"), ("V010", "Clearwater Bottled Water", "Net 15", "****4410"),
    ("V011", "Metro Security Systems", "Net 30", "****0937"), ("V012", "Brightline Consulting Partners", "Net 45", "****6254"),
]
ITEMS = {
    "V001": [("Copy paper, case", 42.50), ("Toner cartridge", 118.00), ("Binders, box of 12", 27.90)],
    "V002": [("Managed services, monthly", 2450.00), ("On-site support hour", 145.00), ("Laptop setup", 95.00)],
    "V003": [("Office cleaning, weekly", 380.00), ("Carpet shampoo", 260.00)],
    "V004": [("Brochure print run", 640.00), ("Postage, bulk", 0.58), ("Envelopes, 1000", 74.00)],
    "V005": [("HVAC maintenance visit", 520.00), ("Filter replacement", 36.00)],
    "V006": [("Same-day delivery", 38.00), ("Overnight parcel", 24.50)],
    "V007": [("Lunch for 20", 340.00), ("Coffee service", 85.00)],
    "V008": [("Accounting software seat, annual", 960.00), ("Support plan", 1200.00)],
    "V009": [("Electrician hour", 98.00), ("Light fixture", 145.00)],
    "V010": [("5-gallon bottle", 7.50), ("Cooler rental, monthly", 12.00)],
    "V011": [("Alarm monitoring, monthly", 210.00), ("Access card", 6.50)],
    "V012": [("Advisory hours", 225.00), ("Workshop facilitation", 1800.00)],
}
TAX = 0.06


def _layout_a(c, inv, v):            # classic header, table with qty / unit / amount
    c.setFont("Helvetica-Bold", 16); c.drawString(50, 740, v["name"])
    c.setFont("Helvetica", 10); c.drawString(50, 724, "123 Commerce Way, Baltimore, MD 21201")
    c.setFont("Helvetica-Bold", 20); c.drawRightString(560, 740, "INVOICE")
    c.setFont("Helvetica", 10)
    for i, (k, val) in enumerate([("Invoice No:", inv["invoice_no"]), ("Invoice Date:", inv["invoice_date"]),
                                  ("PO Number:", inv["po"] or "N/A"), ("Terms:", inv["terms"])]):
        c.drawString(380, 700 - 14 * i, k); c.drawRightString(560, 700 - 14 * i, str(val))
    c.drawString(50, 690, "Bill To: Example Organization, Accounts Payable"); y = 620
    c.setFont("Helvetica-Bold", 10)
    for x, h in [(50, "Description"), (330, "Qty"), (400, "Unit Price"), (490, "Amount")]: c.drawString(x, y, h)
    c.setFont("Helvetica", 10)
    for d, q, u, a in inv["lines"]:
        y -= 16; c.drawString(50, y, d); c.drawRightString(350, y, f"{q:g}"); c.drawRightString(460, y, f"{u:,.2f}"); c.drawRightString(560, y, f"{a:,.2f}")
    y -= 30
    for k, val in [("Subtotal", inv["subtotal"]), ("Sales Tax (6%)", inv["tax"]), ("Total Due", inv["total"])]:
        c.drawString(400, y, k); c.drawRightString(560, y, f"${val:,.2f}"); y -= 16
    c.drawString(50, 80, f"Remit to account {inv['bank']}  -  Thank you for your business.")


def _layout_b(c, inv, v):            # "Bill #" wording, amounts first, totals labelled differently
    c.setFont("Times-Bold", 18); c.drawCentredString(306, 745, v["name"].upper())
    c.setFont("Times-Roman", 11); c.drawCentredString(306, 728, "Statement of charges")
    c.drawString(60, 690, f"Bill #: {inv['invoice_no']}"); c.drawString(60, 674, f"Date: {inv['invoice_date']}")
    c.drawString(330, 690, f"Purchase Order: {inv['po'] or 'none'}"); c.drawString(330, 674, f"Payment terms: {inv['terms']}")
    y = 630; c.setFont("Times-Bold", 11)
    for x, h in [(60, "Amount"), (150, "Item"), (420, "Quantity"), (500, "Rate")]: c.drawString(x, y, h)
    c.setFont("Times-Roman", 11)
    for d, q, u, a in inv["lines"]:
        y -= 16; c.drawString(60, y, f"{a:,.2f}"); c.drawString(150, y, d); c.drawString(420, y, f"{q:g}"); c.drawString(500, y, f"{u:,.2f}")
    y -= 28
    c.drawString(330, y, f"Net amount: {inv['subtotal']:,.2f}"); c.drawString(330, y - 15, f"Tax: {inv['tax']:,.2f}")
    c.setFont("Times-Bold", 12); c.drawString(330, y - 32, f"AMOUNT DUE USD {inv['total']:,.2f}")
    c.setFont("Times-Roman", 10); c.drawString(60, 90, f"Payments by ACH to {inv['bank']}.")


def _layout_c(c, inv, v):            # compact, key-value lines, no table rules
    c.setFont("Courier-Bold", 13); c.drawString(40, 750, f"{v['name']}  |  TAX INVOICE")
    c.setFont("Courier", 10)
    meta = [f"Ref.......: {inv['invoice_no']}", f"Issued....: {inv['invoice_date']}", f"Your PO...: {inv['po'] or '-'}", f"Terms.....: {inv['terms']}"]
    for i, m in enumerate(meta): c.drawString(40, 720 - 13 * i, m)
    y = 650
    for d, q, u, a in inv["lines"]:
        c.drawString(40, y, f"{d[:34]:34s} {q:>6g} x {u:>9,.2f} = {a:>10,.2f}"); y -= 13
    y -= 15
    c.drawString(40, y, f"{'Sub-total':>52s} {inv['subtotal']:>10,.2f}"); c.drawString(40, y - 13, f"{'Tax 6.00%':>52s} {inv['tax']:>10,.2f}")
    c.drawString(40, y - 26, f"{'TOTAL':>52s} {inv['total']:>10,.2f}"); c.drawString(40, 70, f"Bank: {inv['bank']}")


LAYOUTS = [_layout_a, _layout_b, _layout_c]


def build(n_invoices: int = 72, seed: int = 11):
    rng = random.Random(seed)
    OUT.mkdir(exist_ok=True); (OUT / "invoices").mkdir(exist_ok=True)
    for f in (OUT / "invoices").glob("*.pdf"): f.unlink()
    vm = pd.DataFrame(VENDORS, columns=["vendor_id", "name", "terms", "bank"]).assign(layout=[i % 3 for i in range(len(VENDORS))])
    vm.to_csv(OUT / "vendor_master.csv", index=False)
    pos, grs, invs, truth = [], [], [], []
    start = date(2026, 8, 28)
    for k in range(n_invoices):
        v = vm.iloc[rng.randrange(len(vm))]
        items = ITEMS[v.vendor_id]
        lines = []
        for d, u in rng.sample(items, rng.randint(1, len(items))):
            q = rng.choice([1, 1, 2, 3, 4, 5, 10, 12, 20]) if u < 500 else rng.choice([1, 1, 2])
            lines.append([d, q, u])
        po = f"PO-{26000 + k}"
        pos.append({"po": po, "vendor_id": v.vendor_id, **{"lines": json.dumps(lines)}, "po_total": round(sum(q * u for _, q, u in lines), 2)})
        grs.append({"po": po, "received_qty": sum(q for _, q, _ in lines)})
        inv_date = start + timedelta(days=rng.randint(0, 74))
        inv = {"vendor_id": v.vendor_id, "invoice_no": f"{v.vendor_id[-2:]}-{rng.randint(1000, 9999)}", "invoice_date": inv_date.isoformat(),
               "po": po, "terms": v.terms, "bank": v.bank, "lines": [[d, q, u, round(q * u, 2)] for d, q, u in lines]}
        issue = None
        r = rng.random()
        if r < 0.06: issue = "math_error"                    # one line amount wrong
        elif r < 0.11: issue = "price_variance"                # unit price above PO
        elif r < 0.15: issue = "bank_change"                   # remit-to account differs from master
        elif r < 0.19: issue = "no_po"
        elif r < 0.22: issue = "qty_over_receipt"
        if issue == "math_error": inv["lines"][0][3] = round(inv["lines"][0][3] * 1.1 + 10, 2)
        if issue == "price_variance":
            inv["lines"][0][2] = round(inv["lines"][0][2] * 1.12, 2); inv["lines"][0][3] = round(inv["lines"][0][1] * inv["lines"][0][2], 2)
        if issue == "bank_change": inv["bank"] = f"****{rng.randint(1000, 9999)}"
        if issue == "no_po": inv["po"] = None
        if issue == "qty_over_receipt":
            inv["lines"][0][1] += 2; inv["lines"][0][3] = round(inv["lines"][0][1] * inv["lines"][0][2], 2)
        inv["subtotal"] = round(sum(l[3] for l in inv["lines"]) if issue != "math_error" else sum(l[1] * l[2] for l in inv["lines"]), 2)
        inv["tax"] = round(inv["subtotal"] * TAX, 2); inv["total"] = round(inv["subtotal"] + inv["tax"], 2)
        invs.append((inv, v)); truth.append({"file": f"inv_{k + 1:03d}.pdf", "planted_issue": issue or "", **{x: inv[x] for x in ["vendor_id", "invoice_no", "invoice_date", "po", "subtotal", "tax", "total", "bank"]}})
    # duplicates: resubmit 3 invoices (one exact, one with a new number, one with a reformatted number)
    for j, kind in zip([5, 17, 40], ["exact", "new_number", "reformatted"]):
        inv, v = invs[j]; d = json.loads(json.dumps(inv))
        d["invoice_date"] = (date.fromisoformat(inv["invoice_date"]) + timedelta(days=rng.randint(3, 20))).isoformat()
        if kind == "new_number": d["invoice_no"] = inv["invoice_no"][:-1] + str((int(inv["invoice_no"][-1]) + 1) % 10)
        if kind == "reformatted": d["invoice_no"] = inv["invoice_no"].replace("-", "")
        invs.append((d, v)); truth.append({"file": f"inv_{len(invs):03d}.pdf", "planted_issue": f"duplicate_{kind}", **{x: d[x] for x in ["vendor_id", "invoice_no", "invoice_date", "po", "subtotal", "tax", "total", "bank"]}})
    for i, (inv, v) in enumerate(invs, 1):
        c = canvas.Canvas(str(OUT / "invoices" / f"inv_{i:03d}.pdf"), pagesize=letter)
        LAYOUTS[int(v.layout)](c, inv, v); c.showPage(); c.save()
    pd.DataFrame(pos).to_csv(OUT / "purchase_orders.csv", index=False)
    pd.DataFrame(grs).to_csv(OUT / "goods_receipts.csv", index=False)
    pd.DataFrame(truth).to_csv(OUT / "ground_truth.csv", index=False)
    return len(invs)


if __name__ == "__main__":
    print("invoices written:", build())
