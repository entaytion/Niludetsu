from collections import defaultdict

class CogLoader:
    def __init__(self):
        self.loaded_cogs = defaultdict(lambda: {'success': [], 'failed': []})
        
    def add_loaded_cog(self, cog_path: str, success: bool = True, error: str = None):
        """Добавляет загруженный ког в соответствующую категорию
        
        Args:
            cog_path (str): Путь к когу
            success (bool): Успешно ли загружен ког
            error (str): Сообщение об ошибке, если есть
        """
        parts = cog_path.split('/')
        if len(parts) > 1:
            category = parts[0]
            cog_name = parts[-1]
            if error:
                cog_name = f"{cog_name} ({error})"
            status_list = 'success' if success else 'failed'
            self.loaded_cogs[category][status_list].append(cog_name)
        else:
            status_list = 'success' if success else 'failed'
            if error:
                cog_path = f"{cog_path} ({error})"
            self.loaded_cogs['other'][status_list].append(cog_path)
            
    def print_loaded_cogs(self):
        """Выводит информацию о загруженных когах в красивом формате"""
        print("\n=== Загруженные расширения ===")
        for category, status in self.loaded_cogs.items():
            if not status['success'] and not status['failed']:
                continue
                
            print(f"\n📁 {category.upper()}:")
            if status['success']:
                print(f"  ├─ ✅ {', '.join(sorted(status['success']))}")
            if status['failed']:
                print(f"  ├─ ❌ {', '.join(sorted(status['failed']))}")
        print("\n============================\n")

# Создаем глобальный экземпляр для использования
cog_loader = CogLoader() 