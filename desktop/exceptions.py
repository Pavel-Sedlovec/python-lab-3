class DesktopAppError(Exception):
    """Базовая ошибка десктопного приложения."""


class InvalidSleepPeriodError(DesktopAppError):
    pass


class NoRecordSelectedError(DesktopAppError):
    pass


class ApiConnectionError(DesktopAppError):
    pass
