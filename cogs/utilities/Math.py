import discord
from discord import app_commands
from discord.ext import commands
import math
import re
from Niludetsu.utils.embed import Embed
from Niludetsu.utils.emojis import EMOJIS

class Math(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y if y != 0 else float('inf'),
            '^': lambda x, y: x ** y,
            'sqrt': lambda x: math.sqrt(x),
            'sin': lambda x: math.sin(math.radians(x)),
            'cos': lambda x: math.cos(math.radians(x)),
            'tan': lambda x: math.tan(math.radians(x))
        }

    def evaluate_expression(self, expression: str) -> float:
        # Заменяем запятые на точки для корректной работы с десятичными числами
        expression = expression.replace(',', '.')
        # Убираем все пробелы
        expression = expression.replace(' ', '')
        
        # Обработка тригонометрических функций и корня
        trig_pattern = r'(sqrt|sin|cos|tan)\(([^)]+)\)'
        while re.search(trig_pattern, expression):
            match = re.search(trig_pattern, expression)
            func_name = match.group(1)
            arg = self.evaluate_expression(match.group(2))
            result = self.operators[func_name](arg)
            expression = expression[:match.start()] + str(result) + expression[match.end():]

        # Обработка скобок
        while '(' in expression:
            start = expression.rindex('(')
            end = expression.find(')', start)
            if end == -1:
                raise ValueError("Несогласованные скобки")
            result = self.evaluate_expression(expression[start + 1:end])
            expression = expression[:start] + str(result) + expression[end + 1:]

        # Разбиваем выражение на токены, сохраняя все операторы
        tokens = []
        current_number = ''
        
        for char in expression:
            if char in '+-*/^':
                if current_number:
                    tokens.append(current_number)
                    current_number = ''
                tokens.append(char)
            else:
                current_number += char
        if current_number:
            tokens.append(current_number)

        # Проверяем токены на корректность
        if not tokens:
            raise ValueError("Неверное выражение")
        
        try:
            tokens = [float(t) if t not in '+-*/^' else t for t in tokens]
        except ValueError:
            raise ValueError("Неверное число в выражении")

        # Обрабатываем степени (^)
        i = 0
        while i < len(tokens):
            if tokens[i] == '^':
                if i == 0 or i == len(tokens) - 1:
                    raise ValueError("Неверное использование оператора степени")
                base = float(tokens[i-1])
                exp = float(tokens[i+1])
                result = self.operators['^'](base, exp)
                tokens[i-1:i+2] = [result]
                i -= 1
            i += 1

        # Обрабатываем умножение и деление
        i = 0
        while i < len(tokens):
            if tokens[i] in ['*', '/']:
                if i == 0 or i == len(tokens) - 1:
                    raise ValueError("Неверное использование оператора")
                left = float(tokens[i-1])
                right = float(tokens[i+1])
                result = self.operators[tokens[i]](left, right)
                tokens[i-1:i+2] = [result]
                i -= 1
            i += 1

        # Обрабатываем сложение и вычитание
        result = float(tokens[0])
        i = 1
        while i < len(tokens):
            if tokens[i] in ['+', '-']:
                if i == len(tokens) - 1:
                    raise ValueError("Неверное использование оператора")
                right = float(tokens[i+1])
                result = self.operators[tokens[i]](result, right)
            i += 2

        return result

    @app_commands.command(name="math", description="Калькулятор с поддержкой сложных выражений")
    @app_commands.describe(expression="Математическое выражение для вычисления")
    async def math(self, interaction: discord.Interaction, expression: str):
        result = self.evaluate_expression(expression)
        
        # Форматируем результат
        if result.is_integer():
            formatted_result = str(int(result))
        else:
            formatted_result = f"{result:.2f}"

        embed=Embed(
            title="🔢 Калькулятор"
        )
        embed.add_field(
            name="Выражение:",
            value=f"```{expression}```",
            inline=False
        )
        embed.add_field(
            name="Результат:",
            value=f"```{formatted_result}```",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Math(bot)) 