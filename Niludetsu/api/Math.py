"""
Модуль для безопасных математических вычислений
"""

import ast, math, operator, re
from discord.ext import commands
from Niludetsu import Embed, Colors
from typing import Union, Tuple

class MathCalculatorAPI:
    """Класс для безопасных математических вычислений"""

    def __init__(self):
        """Инициализация калькулятора"""
        # Разрешенные операторы
        self.safe_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Mod: operator.mod,
        }

        # Разрешенные функции
        self.safe_functions = {
            # Основные математические функции
            'abs': abs,
            'round': round,
            'int': int,
            'float': float,
            'max': max,
            'min': min,
            'sum': sum,

            # Тригонометрические функции
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'atan2': math.atan2,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,

            # Логарифмические функции
            'log': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'exp': math.exp,

            # Степенные функции
            'sqrt': math.sqrt,
            'pow': pow,

            # Другие математические функции
            'ceil': math.ceil,
            'floor': math.floor,
            'factorial': math.factorial,
            'degrees': math.degrees,
            'radians': math.radians,
        }

        # Математические константы
        self.safe_constants = {
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau if hasattr(math, 'tau') else math.pi * 2,
            'inf': math.inf,
        }

        # Максимальная длина выражения
        self.max_expression_length = 500

        # Максимальное значение результата
        self.max_result_value = 10**50

    def normalize_expression(self, expression: str) -> str:
        """
        Нормализует математическое выражение

        Parameters
        ----------
        expression : str
            Исходное выражение

        Returns
        -------
        str
            Нормализованное выражение
        """
        if not expression:
            return ""

        # Удаляем лишние пробелы
        expression = expression.strip()

        # Заменяем альтернативные символы
        replacements = {
            '×': '*',
            '÷': '/',
            '^': '**',
            '–': '-',  # длинное тире
            '−': '-',  # минус Unicode
            '＋': '+',  # плюс Unicode
            '（': '(',  # скобки Unicode
            '）': ')',
        }

        for old, new in replacements.items():
            expression = expression.replace(old, new)

        # Добавляем пробелы вокруг операторов для лучшей читаемости
        expression = re.sub(r'([+\-*/()^])', r' \1 ', expression)

        # Убираем множественные пробелы
        expression = re.sub(r'\s+', ' ', expression).strip()

        # Добавляем знак умножения где он подразумевается
        expression = self._add_implicit_multiplication(expression)

        return expression

    def _add_implicit_multiplication(self, expression: str) -> str:
        """
        Добавляет знак умножения где он подразумевается

        Parameters
        ----------
        expression : str
            Выражение

        Returns
        -------
        str
            Выражение с явным умножением
        """
        # Число перед скобкой: 2(3+4) -> 2*(3+4)
        expression = re.sub(r'(\d)\s*\(', r'\1 * (', expression)

        # Скобка после числа: (3+4)2 -> (3+4)*2
        expression = re.sub(r'\)\s*(\d)', r') * \1', expression)

        # Скобка после скобки: (3+4)(5+6) -> (3+4)*(5+6)
        expression = re.sub(r'\)\s*\(', r') * (', expression)

        # Число перед функцией: 2sin(x) -> 2*sin(x)
        for func_name in self.safe_functions.keys():
            pattern = rf'(\d)\s*({func_name})\s*\('
            expression = re.sub(pattern, rf'\1 * \2(', expression)

        # Константа перед числом: pi2 -> pi*2
        for const_name in self.safe_constants.keys():
            pattern = rf'({const_name})\s*(\d)'
            expression = re.sub(pattern, rf'\1 * \2', expression)

        # Число перед константой: 2pi -> 2*pi
        for const_name in self.safe_constants.keys():
            pattern = rf'(\d)\s*({const_name})'
            expression = re.sub(pattern, rf'\1 * \2', expression)

        return expression

    def validate_expression(self, expression: str) -> Tuple[bool, str]:
        """
        Валидирует математическое выражение

        Parameters
        ----------
        expression : str
            Математическое выражение

        Returns
        -------
        Tuple[bool, str]
            Кортеж (валидность, сообщение об ошибке)
        """
        if not expression or not expression.strip():
            return False, "Выражение не может быть пустым"

        if len(expression) > self.max_expression_length:
            return False, f"Выражение слишком длинное (максимум {self.max_expression_length} символов)"

        # Проверяем на подозрительные паттерны
        suspicious_patterns = [
            r'__',  # dunder методы
            r'import',  # импорты
            r'exec',  # выполнение кода
            r'eval',  # eval
            r'open',  # работа с файлами
            r'input',  # ввод
            r'print',  # вывод
            r'while\s+True',  # бесконечные циклы
            r'for.*in.*range\(\d{4,}\)',  # большие циклы
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return False, "Выражение содержит недопустимые конструкции"

        # Проверяем баланс скобок
        if not self._check_parentheses_balance(expression):
            return False, "Несбалансированные скобки"

        # Проверяем на допустимые символы (расширенный набор)
        allowed_pattern = r'^[0-9a-zA-Z+\-*/(). _,\^]+$'
        if not re.match(allowed_pattern, expression):
            return False, "Выражение содержит недопустимые символы"

        return True, ""

    def _check_parentheses_balance(self, expression: str) -> bool:
        """
        Проверяет баланс скобок в выражении

        Parameters
        ----------
        expression : str
            Выражение для проверки

        Returns
        -------
        bool
            True, если скобки сбалансированы
        """
        balance = 0
        for char in expression:
            if char == '(':
                balance += 1
            elif char == ')':
                balance -= 1
                if balance < 0:
                    return False
        return balance == 0

    def safe_eval(self, expression: str) -> Union[float, int]:
        """
        Безопасно вычисляет математическое выражение

        Parameters
        ----------
        expression : str
            Математическое выражение

        Returns
        -------
        Union[float, int]
            Результат вычисления

        Raises
        ------
        ValueError
            Если выражение небезопасно или некорректно
        OverflowError
            Если результат слишком большой
        """
        try:
            # Создаем безопасное пространство имен
            safe_dict = {}
            safe_dict.update(self.safe_functions)
            safe_dict.update(self.safe_constants)

            # Вычисляем выражение
            result = eval(expression, {"__builtins__": {}}, safe_dict)

            # Проверяем размер результата
            if isinstance(result, (int, float)):
                if abs(result) > self.max_result_value:
                    raise OverflowError("Результат слишком большой")

                # Проверяем на NaN и infinity
                if math.isnan(result):
                    raise ValueError("Результат не является числом (NaN)")
                if math.isinf(result):
                    raise ValueError("Результат бесконечен")

            return result

        except ZeroDivisionError:
            raise ValueError("Деление на ноль")
        except OverflowError:
            raise ValueError("Результат слишком большой")
        except (SyntaxError, NameError) as e:
            raise ValueError(f"Синтаксическая ошибка: {str(e)}")
        except Exception as e:
            raise ValueError(f"Ошибка вычисления: {str(e)}")

    def format_result(self, result: Union[float, int]) -> str:
        """
        Форматирует результат для отображения

        Parameters
        ----------
        result : Union[float, int]
            Результат вычисления

        Returns
        -------
        str
            Отформатированный результат
        """
        if isinstance(result, complex):
            # Комплексные числа
            if result.imag == 0:
                result = result.real
            else:
                return f"{result.real:g} + {result.imag:g}i"

        if isinstance(result, float):
            # Проверяем, является ли число целым
            if result.is_integer():
                result = int(result)
            else:
                # Округляем до разумного количества знаков
                if abs(result) < 1e-10:
                    result = 0
                elif abs(result) < 1:
                    result = round(result, 10)
                elif abs(result) < 1000:
                    result = round(result, 6)
                else:
                    result = round(result, 2)

                # Убираем .0 если получилось целое число
                if isinstance(result, float) and result.is_integer():
                    result = int(result)

        # Форматируем большие числа с разделителями
        if isinstance(result, int) and abs(result) >= 1000:
            return f"{result:,}".replace(',', ' ')
        else:
            return str(result)

    async def calculate(self, ctx: commands.Context, expression: str):
        """
        Вычисляет математическое выражение и отправляет результат

        Parameters
        ----------
        ctx : commands.Context
            Контекст команды Discord
        expression : str
            Математическое выражение
        """
        if not expression:
            embed = Embed.error(
                title="Недостаточно параметров",
                description="Укажите математическое выражение!\n"
                           "**Примеры:**\n"
                           "`!calc 2 + 2`\n"
                           "`!calc sin(pi/2)`\n"
                           "`!calc sqrt(16) * 3`\n"
                           "`!calc 2(3+4)` - неявное умножение\n"
                           "`!calc log(e^2)`"
            )
            await ctx.reply(embed=embed)
            return

        try:
            # Сохраняем оригинальное выражение
            original_expression = expression

            # Нормализуем выражение
            expression = self.normalize_expression(expression)

            # Валидируем выражение
            is_valid, error_message = self.validate_expression(expression)
            if not is_valid:
                await ctx.reply(embed=Embed.error(
                    title="Ошибка валидации",
                    description=error_message
                ))
                return

            # Вычисляем результат
            result = self.safe_eval(expression)

            # Форматируем результат
            formatted_result = self.format_result(result)

            # Создаем эмбед с результатом
            embed = Embed(
                title="🔢 Калькулятор",
                color=Colors.PRIMARY
            )

            # Показываем оригинальное и нормализованное выражение если они отличаются
            if original_expression.strip() != expression.strip():
                embed.add_field(
                    name="Исходное выражение",
                    value=f"`{original_expression}`",
                    inline=False
                )
                embed.add_field(
                    name="Обработанное выражение",
                    value=f"`{expression}`",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Выражение",
                    value=f"`{expression}`",
                    inline=False
                )

            embed.add_field(
                name="Результат",
                value=f"```{formatted_result}```",
                inline=False
            )

            # Добавляем дополнительную информацию если результат интересный
            self._add_result_info(embed, result)

            await ctx.reply(embed=embed)

        except ValueError as e:
            await ctx.reply(embed=Embed.error(
                title="Ошибка вычисления",
                description=str(e)
            ))
        except Exception as e:
            await ctx.reply(embed=Embed.error(
                title="Неожиданная ошибка",
                description="Произошла ошибка при вычислении выражения"
            ))

    def _add_result_info(self, embed: Embed, result: Union[float, int]):
        """
        Добавляет дополнительную информацию о результате

        Parameters
        ----------
        embed : Embed
            Эмбед для добавления информации
        result : Union[float, int]
            Результат вычисления
        """
        info_parts = []

        if isinstance(result, (int, float)):
            # Информация о больших числах
            if isinstance(result, int) and result > 1000000:
                # Научная нотация
                scientific = f"{result:.2e}"
                info_parts.append(f"Научная нотация: `{scientific}`")

                # Количество цифр
                digit_count = len(str(abs(result)))
                info_parts.append(f"Количество цифр: `{digit_count}`")

            # Информация о дробных числах
            elif isinstance(result, float) and not result.is_integer():
                # Процентное представление если число меньше 1
                if 0 < abs(result) < 1:
                    percentage = result * 100
                    info_parts.append(f"В процентах: `{percentage:.4f}%`")

        # Добавляем информацию в эмбед если есть что добавить
        if info_parts:
            embed.add_field(
                name="Дополнительная информация",
                value="".join(info_parts),
                inline=False
            )

    # Методы для обратной совместимости
    async def calculate_math(self, ctx: commands.Context, expression: str):
        """Старый метод для обратной совместимости"""
        await self.calculate(ctx, expression)

# Создаем экземпляр для импорта
math_calculator_api = MathCalculatorAPI()

