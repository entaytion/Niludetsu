import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, Union

class AkinatorError(Exception):
    """Исключение для ошибок Akinator."""
    pass

class Akinator:
    """
    Класс для работы с Akinator API.
    
    Args:
        theme (str): Тема игры ('characters', 'objects', 'animals')
        lang (str): Язык игры (по умолчанию 'ru')
        child_mode (bool): Режим для детей
    """
    
    def __init__(self, theme: str = "characters", lang: str = "ru", child_mode: bool = False) -> None:
        self.ENDPOINT = f"https://{lang}.akinator.com/"
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.photo: Optional[str] = None
        self.answer_id: Optional[int] = None
        self.akitude: Optional[str] = None
        
        # Определение ID темы
        theme_ids = {
            "characters": 1,
            "objects": 2,
            "animals": 14
        }
        
        if theme not in theme_ids:
            raise AkinatorError("Тема должна быть 'characters' / 'objects' / 'animals'")
            
        self.json = {
            "step": 0,
            "progression": 0.0,
            "sid": theme_ids[theme],
            "cm": child_mode,
            "answer": 0,
        }

    def start_game(self) -> str:
        """
        Начинает новую игру.
        
        Returns:
            str: Первый вопрос
        """
        self.name = None
        self.description = None
        self.photo = None
        self.answer_id = None
        self.akitude = "https://en.akinator.com/assets/img/akitudes_670x1096/defi.png"
        
        game = requests.post(
            f"{self.ENDPOINT}game", 
            json={"sid": self.json["sid"], "cm": self.json["cm"]}
        ).text
        
        soup = BeautifulSoup(game, "html.parser")
        askSoundlike = soup.find(id="askSoundlike")
        question_label = soup.find(id="question-label").get_text()
        session_id = askSoundlike.find(id="session").get("value")
        signature_id = askSoundlike.find(id="signature").get("value")
        
        self.json["session"] = session_id
        self.json["signature"] = signature_id
        self.step = 0
        self.progression = 0.0
        self.question = question_label
        
        return question_label

    def post_answer(self, answer: str) -> Dict[str, Any]:
        """
        Отправляет ответ на вопрос.
        
        Args:
            answer (str): Ответ ('y', 'n', 'idk', 'p', 'pn')
            
        Returns:
            Dict[str, Any]: Ответ от API
            
        Raises:
            AkinatorError: Если ответ некорректный или произошла ошибка
        """
        answer_map = {
            "y": 0,   # Да
            "n": 1,   # Нет
            "idk": 2, # Не знаю
            "p": 3,   # Вероятно
            "pn": 4   # Вероятно нет
        }
        
        if answer not in answer_map:
            raise AkinatorError("Ответ должен быть 'y' / 'n' / 'idk' / 'p' / 'pn'")
            
        self.json["answer"] = answer_map[answer]
        
        try:
            progression = requests.post(f"{self.ENDPOINT}answer", json=self.json).json()
            
            if progression["completion"] == "KO":
                raise AkinatorError("completion : KO")
            elif progression["completion"] == "SOUNDLIKE":
                raise AkinatorError("completion : SOUNDLIKE")
                
            try:
                # Обновляем состояние игры
                self.json["step"] = int(progression["step"])
                self.json["progression"] = float(progression["progression"])
                self.step = int(progression["step"])
                self.progression = float(progression["progression"])
                self.question = progression["question"]
                self.question_id = progression["question_id"]
                self.akitude = f"https://en.akinator.com/assets/img/akitudes_670x1096/{progression['akitude']}"
            except:
                # Если получен ответ с предположением
                self.name = progression["name_proposition"]
                self.description = progression["description_proposition"]
                self.photo = progression["photo"]
                self.answer_id = progression["id_proposition"]
                self.json["step_last_proposition"] = int(self.json["step"])
                
            return progression
            
        except Exception as e:
            raise AkinatorError(str(e))

    def go_back(self) -> Dict[str, Any]:
        """
        Возвращается к предыдущему вопросу.
        
        Returns:
            Dict[str, Any]: Предыдущий вопрос
            
        Raises:
            AkinatorError: Если это первый вопрос или произошла ошибка
        """
        self.name = None
        self.description = None
        self.photo = None
        self.answer_id = None
        
        if self.json["step"] == 0:
            raise AkinatorError("Это первый вопрос")
            
        if "answer" in self.json:
            del self.json["answer"]
            
        try:
            goback = requests.post(f"{self.ENDPOINT}cancel_answer", json=self.json).json()
            
            self.json["step"] = int(goback["step"])
            self.json["progression"] = float(goback["progression"])
            self.step = int(goback["step"])
            self.progression = float(goback["progression"])
            self.question = goback["question"]
            self.question_id = goback["question_id"]
            self.akitude = f"https://en.akinator.com/assets/img/akitudes_670x1096/{goback['akitude']}"
            
            return goback
            
        except:
            raise AkinatorError("Не удалось вернуться назад")

    def exclude(self) -> Dict[str, Any]:
        """
        Исключает текущий вопрос.
        
        Returns:
            Dict[str, Any]: Следующий вопрос
            
        Raises:
            AkinatorError: Если произошла ошибка
        """
        self.name = None
        self.description = None
        self.photo = None
        self.answer_id = None
        
        if "answer" in self.json:
            del self.json["answer"]
            
        try:
            exclude = requests.post(f"{self.ENDPOINT}exclude", json=self.json).json()
            
            self.json["step"] = int(exclude["step"])
            self.json["progression"] = float(exclude["progression"])
            self.step = int(exclude["step"])
            self.progression = float(exclude["progression"])
            self.question = exclude["question"]
            self.question_id = exclude["question_id"]
            self.akitude = f"https://en.akinator.com/assets/img/akitudes_670x1096/{exclude['akitude']}"
            
            return exclude
            
        except:
            raise AkinatorError("Не удалось исключить вопрос") 