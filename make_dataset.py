"""Generate a STARTER synthetic dataset -> data/sms.csv  (label 1 = scam, 0 = safe).
IMPORTANT: synthetic data gives inflated accuracy. Replace/extend with real messages
(your own phone, friends, public SMS-spam datasets, reported scams)."""
import csv, random
random.seed(42)

STATES = ["TN", "KA", "MH", "DL", "KL", "AP", "TS", "GJ", "UP", "WB"]
LET = "ABCDEFGHJKLMNPRSTUVWXYZ"
def plate():
    return f"{random.choice(STATES)}{random.randint(1,99):02d}{''.join(random.choices(LET,k=2))}{random.randint(1000,9999)}"
def amt(): return random.choice([500, 1000, 1500, 2000, 250, 750])

BAD_DOMAINS = ["echallan-parivahan.xyz", "parivahan-gov.online", "challan-pay.top",
               "vahan-fine.click", "bit.ly/3xFine", "tinyurl.com/challan99",
               "echallan-india.info", "rto-payment.site", "cutt.ly/echln"]
SCAM = [
    "Your vehicle {p} has a pending e-challan of Rs {a}. Pay now: http://{d} to avoid legal action",
    "TRAFFIC FINE: {p} challan Rs {a} unpaid. Pay immediately at {d} or licence will be suspended",
    "Dear owner, e-challan issued for {p}. Final notice. Click {d} and pay Rs {a} within 24 hrs",
    "RTO Alert: vehicle fine pending for {p}. Pay here {d} . Ignore = court case",
    "Your vehicle {p} violated traffic rules. Penalty Rs {a}. Pay now {d}",
    "e-Challan notice {p}: Rs {a} due today. Avoid penalty, click {d}",
]
GOOD_DOMAINS = ["echallan.parivahan.gov.in", "parivahan.gov.in"]
# PLACEHOLDER genuine-style challan notices -> replace with real formats you collect
LEGIT_CHALLAN = [
    "Challan for vehicle {p} of Rs {a} generated. Check details at https://{d}",
    "Notice: e-challan against {p} amount Rs {a}. Visit https://{d} for details",
]
LEGIT_OTHER = [
    "Your OTP is {n}. Do not share it with anyone. -HDFC Bank",
    "Rs {a} debited from A/c XX{n} on 12-09-26. If not you call 1800-xxx",
    "Your order #{n} has been shipped and will arrive tomorrow.",
    "Hi, are we meeting at 6 pm today? Let me know.",
    "Your recharge of Rs {a} is successful. Thank you for using our service.",
    "Reminder: your vehicle {p} insurance renewal is due next month.",
    "Your FASTag balance is low. Recharge via the official app.",
    "Class rescheduled to 10 am tomorrow, please inform others.",
]

rows = []
for _ in range(600):
    rows.append((random.choice(SCAM).format(p=plate(), a=amt(), d=random.choice(BAD_DOMAINS)), 1))
for _ in range(200):
    rows.append((random.choice(LEGIT_CHALLAN).format(p=plate(), a=amt(), d=random.choice(GOOD_DOMAINS)), 0))
for _ in range(600):
    rows.append((random.choice(LEGIT_OTHER).format(p=plate(), a=amt(), n=random.randint(1000, 999999)), 0))
random.shuffle(rows)

with open("data/sms.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["text", "label"]); w.writerows(rows)
print(f"wrote {len(rows)} rows -> data/sms.csv")