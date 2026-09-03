class NiludetsuException(Exception):
    def __init__(self, message: str = "Произошла неизвестная ошибка.", **kwargs):
        self.message = message
        self.kwargs = kwargs
        super().__init__(message)

class ActiveGameExists(NiludetsuException):
    def __init__(self, game_name: str):
        super().__init__(f"У вас уже есть активная игра «{game_name}». Завершите её, чтобы начать новую.", game_name=game_name)

class NotEnoughMoney(NiludetsuException):
    def __init__(self, amount: int):
        super().__init__(f"Недостаточно средств! Вам не хватает {amount}.", amount=amount)

class BetTooLow(NiludetsuException):
    def __init__(self, min_bet: int):
        super().__init__(f"Ставка слишком мала, минимальная: {min_bet}.", min_bet=min_bet)

class ValidationError(NiludetsuException):
    def __init__(self, message: str):
        super().__init__(message)

class CooldownError(NiludetsuException):
    def __init__(self, retry_after: int):
        super().__init__(f"Не спешите, подождите еще {retry_after} секунд.", retry_after=retry_after)

class InsufficientPermissions(NiludetsuException):
    def __init__(self, missing_perms: list[str]):
        super().__init__(f"Недостаточно прав. Требуются: {', '.join(missing_perms)}", missing_perms=missing_perms)

class UserHierarchyError(NiludetsuException):
    def __init__(self):
        super().__init__("Вам запрещено выполнять действия над этим пользователем (он выше или равен вам по роли).")

