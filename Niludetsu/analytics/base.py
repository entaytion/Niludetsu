import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Цветовая схема
COLORS = {
    'primary': '#ED4245',    # Основной красный цвет Discord
    'secondary': '#FF6B6B',  # Светло-красный
    'accent': '#FF4B4B',     # Акцентный красный
    'background': '#2F3136', # Тёмный фон
    'text': '#FFFFFF',       # Белый текст
    'grid': '#40444B'        # Цвет сетки
}

class BaseAnalytics:
    def __init__(self):
        # Добавляем кастомный шрифт
        plt.rcParams['font.family'] = 'sans-serif'
        self.custom_font = fm.FontProperties(fname='config/fonts/TTNormsPro-Bold.ttf')
        
        # Настройка стиля для всех графиков
        plt.style.use('dark_background')
        plt.rcParams['axes.facecolor'] = '#2F3136'
        plt.rcParams['figure.facecolor'] = '#2F3136'
        plt.rcParams['text.color'] = '#FFFFFF'
        plt.rcParams['axes.labelcolor'] = '#FFFFFF'
        plt.rcParams['xtick.color'] = '#FFFFFF'
        plt.rcParams['ytick.color'] = '#FFFFFF'
        plt.rcParams['grid.color'] = '#40444B'
        
    def style_plot(self, fig, ax):
        """Применяет единый стиль к графику"""
        fig.patch.set_facecolor(COLORS['background'])
        ax.set_facecolor(COLORS['background'])
        
        # Настройка сетки
        ax.grid(True, linestyle='--', alpha=0.2, color=COLORS['grid'])
        
        # Настройка шрифтов
        for text in ax.get_xticklabels() + ax.get_yticklabels():
            text.set_fontproperties(self.custom_font)
            text.set_color(COLORS['text'])
        
        # Настройка заголовков
        ax.title.set_fontproperties(self.custom_font)
        ax.xaxis.label.set_fontproperties(self.custom_font)
        ax.yaxis.label.set_fontproperties(self.custom_font)
        
        # Настройка цветов
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.spines['top'].set_color(COLORS['grid'])
        ax.spines['left'].set_color(COLORS['grid'])
        ax.spines['right'].set_color(COLORS['grid']) 