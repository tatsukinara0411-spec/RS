import hashlib


TOKYO_23_WARDS = [
    "千代田区", "中央区", "港区", "新宿区", "文京区",
    "台東区", "墨田区", "江東区", "品川区", "目黒区",
    "大田区", "世田谷区", "渋谷区", "中野区", "杉並区",
    "豊島区", "北区", "荒川区", "板橋区", "練馬区",
    "足立区", "葛飾区", "江戸川区",
]


def compute_fingerprint(company_name: str, address: str) -> str:
    key = f"{company_name.strip().lower()}|{address.strip()}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def is_tokyo_23ward(address: str) -> bool:
    return any(ward in address for ward in TOKYO_23_WARDS)
