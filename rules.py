"""Rule-based layer: extract plate/URLs and flag suspicious signals in an SMS."""
import re
from difflib import SequenceMatcher
from urllib.parse import urlparse

# e.g. TN09AB1234, TN 09 AB 1234, tn-09-ab-1234
PLATE_RE = re.compile(r"\b([A-Z]{2})[ -]?(\d{1,2})[ -]?([A-Z]{1,3})[ -]?(\d{4})\b", re.I)
URL_RE = re.compile(r"(?:https?://|www\.)[^\s]+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)+/[^\s]*", re.I)
CHALLAN_WORDS = ["challan", "e-challan", "echallan", "traffic fine", "vehicle fine",
                 "traffic violation", "rto", "parivahan", "vahan"]
URGENCY_WORDS = ["pay now", "immediately", "within 24", "final notice", "avoid",
                 "legal action", "court", "suspended", "penalty", "click", "pay here"]

# Verify/extend this list yourself against real government messages.
OFFICIAL_SUFFIXES = (".gov.in", ".nic.in")
OFFICIAL_REFERENCE = "echallan.parivahan.gov.in"
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "cutt.ly", "rb.gy", "is.gd",
              "goo.gl", "shorturl.at", "tiny.cc", "wa.me"}
RISKY_TLDS = (".xyz", ".top", ".click", ".online", ".site", ".icu", ".vip", ".cc", ".info")


def normalize_plate(m):
    return f"{m[0]}{m[1]:0>2}{m[2]}{m[3]}".upper()


def extract_plates(text):
    return list({normalize_plate(m) for m in PLATE_RE.findall(text)})


def extract_urls(text):
    return [u.rstrip(".,);") for u in URL_RE.findall(text)]


def host_of(url):
    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url
    return (urlparse(url).hostname or "").lower()


def analyze_url(url):
    host = host_of(url)
    flags = []
    official = host.endswith(OFFICIAL_SUFFIXES)
    if not official:
        if host in SHORTENERS:
            flags.append("url_shortener")
        if host.endswith(RISKY_TLDS):
            flags.append("risky_tld")
        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", host):
            flags.append("ip_address_host")
        if "parivahan" in host or "challan" in host or "vahan" in host:
            flags.append("lookalike_gov_domain")   # says 'parivahan' but isn't *.gov.in
        elif SequenceMatcher(None, host, OFFICIAL_REFERENCE).ratio() > 0.75:
            flags.append("near_match_official_domain")
        flags.append("not_official_domain")
    return {"url": url, "host": host, "official": official, "flags": flags}


def analyze(sms: str) -> dict:
    t = sms.lower()
    plates = extract_plates(sms)
    urls = [analyze_url(u) for u in extract_urls(sms)]
    claims_challan = any(w in t for w in CHALLAN_WORDS)
    urgency = [w for w in URGENCY_WORDS if w in t]

    score = 0.0
    if claims_challan:
        score += 0.2
    if urgency:
        score += min(0.2, 0.07 * len(urgency))
    for u in urls:
        if "lookalike_gov_domain" in u["flags"]:
            score += 0.4
        if "url_shortener" in u["flags"]:
            score += 0.3
        if "risky_tld" in u["flags"] or "ip_address_host" in u["flags"]:
            score += 0.2
        if "not_official_domain" in u["flags"] and claims_challan:
            score += 0.2
    return {
        "claims_challan": claims_challan,
        "plates": plates,
        "urls": urls,
        "urgency_words": urgency,
        "rule_score": round(min(score, 1.0), 2),
    }


if __name__ == "__main__":
    demo = ("Your vehicle TN09AB1234 has a pending e-challan of Rs 500. "
            "Pay now: http://echallan-parivahan.xyz/pay to avoid legal action")
    import json
    print(json.dumps(analyze(demo), indent=2))