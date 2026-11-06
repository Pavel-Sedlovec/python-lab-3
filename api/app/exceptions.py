class SleepTrackerError(Exception):
    """Базовая ошибка приложения."""


class InvalidSleepPeriodError(SleepTrackerError):
    """Время пробуждения должно быть позже времени засыпания."""


class RecordNotFoundError(SleepTrackerError):
    """Запись сна не найдена."""
