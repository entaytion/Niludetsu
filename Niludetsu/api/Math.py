from ..locale import _
from ..tools.Embed import Colors, Embed
"""
Модуль для безпечних математичних обчислень
"""

import ast, math, operator, re
from discord.ext import commands

from typing import Union, Tuple

class MathCalculatorAPI:

    def __init__(self):
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

        self.safe_functions = {
            'abs': abs,
            'round': round,
            'int': int,
            'float': float,
            'max': max,
            'min': min,
            'sum': sum,

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

            'log': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'exp': math.exp,

            'sqrt': math.sqrt,
            'pow': pow,

            'ceil': math.ceil,
            'floor': math.floor,
            'factorial': math.factorial,
            'degrees': math.degrees,
            'radians': math.radians,
        }

        self.safe_constants = {
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau if hasattr(math, 'tau') else math.pi * 2,
            'inf': math.inf,
        }

        self.max_expression_length = 500

        self.max_result_value = 10**50

    def normalize_expression(self, expression: str) -> str:
        if not expression:
            return ""

        expression = expression.strip()

        replacements = {
            '×': '*',
            '÷': '/',
            '^': '**',
            '–': '-',
            '−': '-',
            '＋': '+',
            '（': '(',
            '）': ')',
        }

        for old, new in replacements.items():
            expression = expression.replace(old, new)

        expression = re.sub(r'([+\-*/()^])', r' \1 ', expression)

        expression = re.sub(r'\s+', ' ', expression).strip()

        expression = self._add_implicit_multiplication(expression)

        return expression

    def _add_implicit_multiplication(self, expression: str) -> str:
        expression = re.sub(r'(\d)\s*\(', r'\1 * (', expression)

        expression = re.sub(r'\)\s*(\d)', r') * \1', expression)

        expression = re.sub(r'\)\s*\(', r') * (', expression)

        for func_name in self.safe_functions.keys():
            pattern = rf'(\d)\s*({func_name})\s*\('
            expression = re.sub(pattern, rf'\1 * \2(', expression)

        for const_name in self.safe_constants.keys():
            pattern = rf'({const_name})\s*(\d)'
            expression = re.sub(pattern, rf'\1 * \2', expression)

        for const_name in self.safe_constants.keys():
            pattern = rf'(\d)\s*({const_name})'
            expression = re.sub(pattern, rf'\1 * \2', expression)

        return expression

    def validate_expression(self, expression: str) -> Tuple[bool, str]:
        if not expression or not expression.strip():
            return False, "Выражение не может быть пустым"

        if len(expression) > self.max_expression_length:
            return False, f"Выражение слишком длинное (максимум {self.max_expression_length} символов)"

        suspicious_patterns = [
            r'__',
            r'import',
            r'exec',
            r'eval',
            r'open',
            r'input',
            r'print',
            r'while\s+True',
            r'for.*in.*range\(\d{4,}\)',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return False, "Выражение содержит недопустимые конструкции"

        if not self._check_parentheses_balance(expression):
            return False, "Несбалансированные скобки"

        allowed_pattern = r'^[0-9a-zA-Z+\-*/(). _,\^]+$'
        if not re.match(allowed_pattern, expression):
            return False, "Выражение содержит недопустимые символы"

        return True, ""

    def _check_parentheses_balance(self, expression: str) -> bool:
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
        try:
            safe_dict = {}
            safe_dict.update(self.safe_functions)
            safe_dict.update(self.safe_constants)

            result = eval(expression, {"__builtins__": {}}, safe_dict)

            if isinstance(result, (int, float)):
                if abs(result) > self.max_result_value:
                    raise OverflowError("Результат слишком большой")

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
        if isinstance(result, complex):
            if result.imag == 0:
                result = result.real
            else:
                return f"{result.real:g} + {result.imag:g}i"

        if isinstance(result, float):
            if result.is_integer():
                result = int(result)
            else:
                if abs(result) < 1e-10:
                    result = 0
                elif abs(result) < 1:
                    result = round(result, 10)
                elif abs(result) < 1000:
                    result = round(result, 6)
                else:
                    result = round(result, 2)

                if isinstance(result, float) and result.is_integer():
                    result = int(result)

        if isinstance(result, int) and abs(result) >= 1000:
            return f"{result:,}".replace(',', ' ')
        else:
            return str(result)

    async def calculate(self, ctx: commands.Context, expression: str):
        if not expression:
            t = _(ctx=ctx)
            embed = Embed.error(
                title=t("api_math", "missing_params"),
                description=t("api_math", "specify_expression"),
            )
            await ctx.reply(embed=embed)
            return

        try:
            original_expression = expression

            expression = self.normalize_expression(expression)

            is_valid, error_message = self.validate_expression(expression)
            if not is_valid:
                await ctx.reply(embed=Embed.error(
                    title=t("api_math", "validation_error"),
                    description=error_message
                ))
                return

            result = self.safe_eval(expression)

            formatted_result = self.format_result(result)

            embed = Embed(
                title=t("api_math", "title"),
                color=Colors.PRIMARY
            )

            if original_expression.strip() != expression.strip():
                embed.add_field(
                    name=t("api_math", "original_expr"),
                    value=f"`{original_expression}`",
                    inline=False
                )
                embed.add_field(
                    name=t("api_math", "processed_expr"),
                    value=f"`{expression}`",
                    inline=False
                )
            else:
                embed.add_field(
                    name=t("api_math", "expression"),
                    value=f"`{expression}`",
                    inline=False
                )

            embed.add_field(
                name=t("api_math", "result"),
                value=f"```{formatted_result}```",
                inline=False
            )

            self._add_result_info(embed, result, t)

            await ctx.reply(embed=embed)

        except ValueError as e:
            await ctx.reply(embed=Embed.error(
                title=t("api_math", "calc_error"),
                description=str(e)
            ))
        except Exception as e:
            await ctx.reply(embed=Embed.error(
                title=t("api_math", "unexpected_error"),
                description=t("api_math", "unexpected_error_desc")
            ))

    def _add_result_info(self, embed: Embed, result: Union[float, int], t) -> None:
        info_parts = []

        if isinstance(result, (int, float)):
            if isinstance(result, int) and result > 1000000:
                scientific = f"{result:.2e}"
                info_parts.append(f"{t('api_math', 'scientific_notation')}: `{scientific}`")

                digit_count = len(str(abs(result)))
                info_parts.append(f"{t('api_math', 'digit_count')}: `{digit_count}`")

            elif isinstance(result, float) and not result.is_integer():
                if 0 < abs(result) < 1:
                    percentage = result * 100
                    info_parts.append(f"{t('api_math', 'percentage')}: `{percentage:.4f}%`")

        if info_parts:
            embed.add_field(
                name=t("api_math", "extra_info"),
                value="".join(info_parts),
                inline=False
            )

    async def calculate_math(self, ctx: commands.Context, expression: str):
        await self.calculate(ctx, expression)

math_calculator_api = MathCalculatorAPI()

