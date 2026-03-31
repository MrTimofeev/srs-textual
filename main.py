#!/usr/bin/env python3
"""
SRS Textual App — Интервальное повторение в терминале
"""

from textual.app import App
from textual import log

from ui.screens import DashboardScreen
from data.storage import Storage
import config


class SRSApp(App):
    """Основное приложение"""
    
    CSS_PATH = "styles.css"  # Выносим стили в отдельный файл
    
    def on_mount(self) -> None:
        """Инициализация при запуске"""
        log.info("🚀 Приложение запущено")
        
        # Инициализируем хранилище
        storage = Storage()
        new_notes = storage.scan_for_new_notes()
        
        if new_notes:
            self.notify(f"🆕 Найдено новых заметок: {new_notes}", timeout=3)
        
        # Запускаем главный экран
        self.push_screen(DashboardScreen(storage))


def main():
    app = SRSApp()
    app.run()


if __name__ == "__main__":
    main()
