from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.orm import Session, sessionmaker
from .database import Base, engine
from .models import SleepRecord
from .schemas import SleepRecordCreate, SleepRecordRead, SleepRecordUpdate, SleepStats
from .exceptions import InvalidSleepPeriodError, RecordNotFoundError

def create_app(custom_engine=None):
    db_engine = custom_engine or engine
    SessionFactory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        Base.metadata.create_all(bind=db_engine)
        yield

    app = FastAPI(title="Sleep Tracker API",
                  description="API приложения для отслеживания сна",
                  version="1.0.0", lifespan=lifespan)

    @app.exception_handler(RecordNotFoundError)
    async def record_not_found_handler(request: Request, exc: RecordNotFoundError):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidSleepPeriodError)
    async def invalid_period_handler(request: Request, exc: InvalidSleepPeriodError):
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/", include_in_schema=False)
    def browser_app():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    def get_session():
        db = SessionFactory()
        try:
            yield db
        finally:
            db.close()

    @app.get("/health")
    def health(db: Session = Depends(get_session)):
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}

    @app.get("/sleep", response_model=list[SleepRecordRead])
    def list_records(db: Session = Depends(get_session)):
        return db.scalars(select(SleepRecord).order_by(SleepRecord.sleep_start.desc())).all()

    @app.post("/sleep", response_model=SleepRecordRead, status_code=status.HTTP_201_CREATED)
    def create_record(payload: SleepRecordCreate, db: Session = Depends(get_session)):
        record = SleepRecord(**payload.model_dump())
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @app.get("/sleep/{record_id}", response_model=SleepRecordRead)
    def get_record(record_id: int, db: Session = Depends(get_session)):
        record = db.get(SleepRecord, record_id)
        if record is None:
            raise RecordNotFoundError("Запись не найдена")
        return record

    @app.put("/sleep/{record_id}", response_model=SleepRecordRead)
    def update_record(record_id: int, payload: SleepRecordUpdate, db: Session = Depends(get_session)):
        record = db.get(SleepRecord, record_id)
        if record is None:
            raise RecordNotFoundError("Запись не найдена")
        for key, value in payload.model_dump().items():
            setattr(record, key, value)
        db.commit()
        db.refresh(record)
        return record

    @app.delete("/sleep/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_record(record_id: int, db: Session = Depends(get_session)):
        record = db.get(SleepRecord, record_id)
        if record is None:
            raise RecordNotFoundError("Запись не найдена")
        db.delete(record)
        db.commit()
        return None

    @app.get("/stats", response_model=SleepStats)
    def stats(db: Session = Depends(get_session)):
        records = db.scalars(select(SleepRecord)).all()
        durations = [(r.sleep_end - r.sleep_start).total_seconds() / 3600 for r in records]
        average = round(sum(durations) / len(durations), 2) if durations else None
        return SleepStats(records_count=len(durations), average_duration_hours=average)

    return app

app = create_app()
