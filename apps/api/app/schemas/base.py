from pydantic import BaseModel, ConfigDict


class RequestModel(BaseModel):
    """Schema đầu vào: từ chối trường lạ để client không ghi được field ngoài ý muốn."""

    model_config = ConfigDict(extra="forbid")
