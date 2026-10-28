from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Lead(BaseModel):
    company_name: str        # 屋号（求人サイト掲載名）
    legal_name: Optional[str] = ""   # 法人名（国税庁登録の正式名称）
    corporate_number: Optional[str] = ""
    address: str
    phone: Optional[str] = ""          # 会社の代表番号（Googleマップ優先）
    listing_phone: Optional[str] = ""  # 求人ページに載っていた番号（応募受付用のことが多い）
    phone_source: str = ""             # phone の出どころ：google（代表番号）／listing（求人ページの番号）
    job_text: str = ""                 # 業種判定用のカード本文（シートには書かない）
    industry: str
    source_site: str
    source_url: str = ""
    detail_url: str = ""
    collected_at: str = ""

    def model_post_init(self, __context):
        if not self.collected_at:
            self.collected_at = datetime.now().isoformat()
