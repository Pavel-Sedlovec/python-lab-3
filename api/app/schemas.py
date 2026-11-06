from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .exceptions import InvalidSleepPeriodError

class SleepRecordBase(BaseModel):
    sleep_start: datetime
    sleep_end: datetime
    quality: int = Field(default=3, ge=1, le=5, description="Качество сна от 1 до 5")
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_period(self):
        if self.sleep_end <= self.sleep_start:
            raise InvalidSleepPeriodError("Время пробуждения должно быть позже времени засыпания")
        return self

class SleepRecordCreate(SleepRecordBase):
    pass

class SleepRecordUpdate(SleepRecordBase):
    pass

class SleepRecordRead(SleepRecordBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class SleepStats(BaseModel):
    records_count: int
    average_duration_hours: float | None
