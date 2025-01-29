from ..utils.logging import BaseLogger
from ..utils.emojis import EMOJIS
import discord
from typing import Optional, List, Dict, Any

class PollLogger(BaseLogger):
    """Логгер для опросов Discord."""
    
    async def log_poll_create(self, message: discord.Message, question: str, options: List[str]):
        """Логирование создания опроса"""
        options_text = "\n".join([f"{i+1}. {option}" for i, option in enumerate(options)])
        
        fields = [
            {"name": f"{EMOJIS['DOT']} Автор", "value": message.author.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Ссылка", "value": f"[Перейти]({message.jump_url})", "inline": True},
            {"name": f"{EMOJIS['DOT']} Вопрос", "value": question, "inline": False},
            {"name": f"{EMOJIS['DOT']} Варианты ответов", "value": options_text, "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Создан новый опрос",
            description=f"В канале {message.channel.mention} создан новый опрос",
            color='GREEN',
            fields=fields
        )
        
    async def log_poll_delete(self, message: discord.Message, question: str):
        """Логирование удаления опроса"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Автор", "value": message.author.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Вопрос", "value": question, "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Опрос удален",
            description=f"В канале {message.channel.mention} удален опрос",
            color='RED',
            fields=fields
        )
        
    async def log_poll_finalize(self, message: discord.Message, question: str, results: Dict[str, int], total_votes: int):
        """Логирование завершения опроса"""
        results_text = []
        for option, votes in results.items():
            percentage = (votes / total_votes * 100) if total_votes > 0 else 0
            results_text.append(f"{option}: {votes} голосов ({percentage:.1f}%)")
            
        fields = [
            {"name": f"{EMOJIS['DOT']} Автор", "value": message.author.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Всего голосов", "value": str(total_votes), "inline": True},
            {"name": f"{EMOJIS['DOT']} Вопрос", "value": question, "inline": False},
            {"name": f"{EMOJIS['DOT']} Результаты", "value": "\n".join(results_text), "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['INFO']} Опрос завершен",
            description=f"В канале {message.channel.mention} завершен опрос",
            color='BLUE',
            fields=fields
        )
        
    async def log_poll_vote_add(self, message: discord.Message, user: discord.Member, option: str):
        """Логирование добавления голоса"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": user.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Выбранный вариант", "value": option, "inline": True},
            {"name": f"{EMOJIS['DOT']} Ссылка на опрос", "value": f"[Перейти]({message.jump_url})", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['SUCCESS']} Добавлен голос в опрос",
            description=f"Пользователь проголосовал в опросе",
            color='GREEN',
            fields=fields
        )
        
    async def log_poll_vote_remove(self, message: discord.Message, user: discord.Member, option: str):
        """Логирование удаления голоса"""
        fields = [
            {"name": f"{EMOJIS['DOT']} Пользователь", "value": user.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Канал", "value": message.channel.mention, "inline": True},
            {"name": f"{EMOJIS['DOT']} Отмененный вариант", "value": option, "inline": True},
            {"name": f"{EMOJIS['DOT']} Ссылка на опрос", "value": f"[Перейти]({message.jump_url})", "inline": False}
        ]
        
        await self.log_event(
            title=f"{EMOJIS['ERROR']} Удален голос из опроса",
            description=f"Пользователь отменил свой голос в опросе",
            color='RED',
            fields=fields
        ) 