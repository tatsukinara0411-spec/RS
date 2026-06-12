from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Lead(BaseModel):
    company_name: str
    address: str
    phone: Optional[str] = ""
    industry: str
    source_site: str
    source_url: str = ""
    detail_url: str = ""
    collected_at: str = ""

    def model_post_init(self, __context):
        if not self.collected_at:
            self.collected_at = datetime.now().isoformat()
