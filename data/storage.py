import json
from pathlib import Path
from typing import List, Optional
from .models import Note
import config



class Storage:
    """Работа с хранилицем данных (JSON)"""
    
    def __init__(self):
        self.reviews_file = Path(config.REVIEWS_FILE)
        self.notes: List[Note] = []
        self._load()
        
    def _load(self):
        """Загружает заметки из JSON"""
        if not self.reviews_file.exists():
            self.reviews_file.parent.mkdir(parents=True, exist_ok=True)
            self.notes = []

        try: 
            with open(self.reviews_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.notes = [Note.from_dict(item) for item in data]
        except Exception as e:
            print(f"Ошибка загрузки {self.reviews_file}: {e}")
            self.notes = []
    
    def save(self):
        """Сохраняет значение в JSON"""
        self.reviews_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.reviews_file, "w", encoding="utf-8") as f:
            json.dump(
                [note.to_dict() for note in self.notes],
                f,
                ensure_ascii=False,
                indent=2
            )
    
    def add_note(self, note: Note):
        """Добавляет новую заметку"""
        # Проверяет дубликат
        if not any(n.file_name == note.file_name for n in self.notes):
            self.notes.append(note)
            self.save()
            return True
        return False
    
    def update_note(self, file_name: str, **kwargs):
        """Обновляет поля заметки"""
        for note in self.notes:
            if note.file_name == file_name:
                for key, value  in kwargs.items():
                    if hasattr(note, key):
                        setattr(note, key, value)
                    self.save()
                    return True
        return False
    
    def get_due_notes(self, today) -> List[Note]:
        """Возвращает заметки, котоыре нужно повторить сегодня"""
        if today is None:
            today = config.TODAY
            
        due = [note for note in self.notes if note.is_due(today)]
        future = [note for note in self.notes if not note.is_due(today)]
        
        # Если нет запланированных берем случайные
        if not due and future:
            import random
            random.shuffle(future)
            due = future[:config.DEFAULT_RANDOM_COUNT]
            for note in due:
                note.is_random = True
        
        return due
    
    def scan_for_new_notes(self) -> int:
        """Сканирует бзау на нове заметки с тегом #Повторить"""
        existing_files = {note.file_name for note in self.notes}
        new_count = 0
        
        for md_file in config.BASE_DIR.rglob("*.md"):
            # Пропускаем служеные папки
            if "08. Повторение" in str(md_file):
                continue
                
            if md_file.name in existing_files:
                continue
        
            try:
                content = md_file.read_text(encoding="utf-8")
                if "#test" in content:
                    relative_path = md_file.relative_to(config.BASE_DIR)
                    note = Note(
                        file_name=md_file.name,
                        relative_path=str(relative_path),
                        date_for_repeat=config.TODAY,
                        number_of_repetitions=0
                    )
                    self.add_note(note)
                    new_count += 1
                    print(f" Найдена новая заметка: {md_file.name}")
            except Exception as e:
                print(f"Ошибка чтения {md_file}: {e}")
        return new_count
