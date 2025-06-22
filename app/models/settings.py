from pydantic import BaseModel
from typing import Optional

class UserSetting(BaseModel):
    user_id: str
    setting_key: str
    setting_value: Optional[str] = None
