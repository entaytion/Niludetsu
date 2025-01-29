import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, Union
import json
import re

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
        self.server = f"https://srv13.akinator.com:9398/ws"
        self.lang = lang
        self.theme = theme
        self.child_mode = child_mode
        self.session: Optional[str] = None
        self.signature: Optional[str] = None
        self.question: Optional[str] = None
        self.progression: float = 0.0
        self.step: int = 0
        
        # Состояние игры
        self.name: Optional[str] = None
        self.description: Optional[str] = None
        self.photo: Optional[str] = None
        self.answer_id: Optional[int] = None
        self.akitude: str = "default.png"

        # Определение ID темы
        self.theme_ids = {
            "characters": 1,
            "objects": 2,
            "animals": 14
        }
        
        if theme not in self.theme_ids:
            raise AkinatorError("Тема должна быть 'characters' / 'objects' / 'animals'")

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Выполняет запрос к API Акинатора"""
        try:
            response = requests.get(f"{self.server}/{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise AkinatorError(f"Ошибка при запросе к API: {str(e)}")
        except json.JSONDecodeError:
            raise AkinatorError("Получен некорректный ответ от сервера")

    def start_game(self) -> str:
        """Начинает новую игру"""
        try:
            # Получаем новую сессию
            params = {
                'partner': 1,
                'player': 'website-desktop',
                'uid_ext_session': 1,
                'frontaddr': 'NDYuNDYuNDYuNDY=',
                'constraint': 'ETAT<>\'AV\'',
                'soft_constraint': self.theme_ids[self.theme],
                'question_filter': self.theme_ids[self.theme]
            }
            
            response = self._make_request('new_session', params)
            
            if response.get('completion') != 'OK':
                raise AkinatorError("Не удалось начать новую игру")
            
            self.session = response['parameters']['identification']['session']
            self.signature = response['parameters']['identification']['signature']
            self.question = response['parameters']['step_information']['question']
            self.step = 0
            self.progression = 0.0
            
            return self.question

        except Exception as e:
            raise AkinatorError(f"Ошибка при начале игры: {str(e)}")

    def post_answer(self, answer: str) -> Dict[str, Any]:
        """Отправляет ответ на вопрос"""
        if not self.session or not self.signature:
            raise AkinatorError("Игра не начата")

        answer_map = {
            "y": 0,    # Да
            "n": 1,    # Нет
            "idk": 2,  # Не знаю
            "p": 3,    # Вероятно
            "pn": 4    # Вероятно нет
        }
        
        if answer not in answer_map:
            raise AkinatorError("Ответ должен быть 'y' / 'n' / 'idk' / 'p' / 'pn'")

        try:
            params = {
                'session': self.session,
                'signature': self.signature,
                'step': self.step,
                'answer': answer_map[answer],
                'question_filter': self.theme_ids[self.theme]
            }
            
            response = self._make_request('answer', params)
            
            if response.get('completion') != 'OK':
                raise AkinatorError("Ошибка при отправке ответа")
            
            parameters = response['parameters']
            
            # Обновляем состояние
            self.step = parameters['step']
            self.progression = parameters['progression']
            self.question = parameters['question']
            
            # Проверяем, есть ли предположение
            if parameters.get('elements'):
                element = parameters['elements'][0]['element']
                self.name = element.get('name')
                self.description = element.get('description', 'Нет описания')
                self.photo = element.get('absolute_picture_path')
                self.answer_id = element.get('id')
            
            return response['parameters']

        except Exception as e:
            raise AkinatorError(f"Ошибка при отправке ответа: {str(e)}")

    def go_back(self) -> Dict[str, Any]:
        """Возвращается к предыдущему вопросу"""
        if not self.session or not self.signature:
            raise AkinatorError("Игра не начата")
            
        if self.step <= 0:
            raise AkinatorError("Это первый вопрос")

        try:
            params = {
                'session': self.session,
                'signature': self.signature,
                'step': self.step - 1,
                'question_filter': self.theme_ids[self.theme]
            }
            
            response = self._make_request('cancel_answer', params)
            
            if response.get('completion') != 'OK':
                raise AkinatorError("Не удалось вернуться назад")
            
            parameters = response['parameters']
            self.step = parameters['step']
            self.progression = parameters['progression']
            self.question = parameters['question']
            
            # Сбрасываем предположение
            self.name = None
            self.description = None
            self.photo = None
            self.answer_id = None
            
            return parameters

        except Exception as e:
            raise AkinatorError(f"Ошибка при возврате назад: {str(e)}")

    def exclude(self) -> Dict[str, Any]:
        """Исключает текущий вопрос"""
        if not self.session or not self.signature:
            raise AkinatorError("Игра не начата")

        try:
            params = {
                'session': self.session,
                'signature': self.signature,
                'step': self.step,
                'forward_answer': 1,
                'question_filter': self.theme_ids[self.theme]
            }
            
            response = self._make_request('exclusion', params)
            
            if response.get('completion') != 'OK':
                raise AkinatorError("Не удалось исключить вопрос")
            
            parameters = response['parameters']
            self.step = parameters['step']
            self.progression = parameters['progression']
            self.question = parameters['question']
            
            return parameters

        except Exception as e:
            raise AkinatorError(f"Ошибка при исключении вопроса: {str(e)}") 