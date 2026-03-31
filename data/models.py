from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class Question:
    """Модель вопроса"""
    text: str
    options: List[str]
    correct_index: int # Индекс правильного ответа (0-based)
    
    def is_correct(self, selected_index: int) -> bool:
        """Проверяем правильность ответа"""
        return selected_index == self.correct_index
    

@dataclass
class Note:
    """Модель заметки для повторения"""
    file_name: str
    relative_path: str
    date_for_repeat: date
    number_of_repetitions: int
    is_random: bool = False
    questions: List[Question] = field(default_factory=list)
    
    def is_due(self, today: date) -> bool:
        """Проверяет, пора ли повторять"""
        return self.date_for_repeat <= today
    
    def to_dict(self) -> dict:
        """Сериализация в dict для JSON"""
        return {
            "file_name": self.file_name,
            "relative_path": self.relative_path,
            "date_for_repeat": str(self.date_for_repeat),
            "number_of_repetitions": self.number_of_repetitions,
            "is_random": self.is_random
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        """Десериализация из dict"""
        return cls(
            file_name=data["file_name"],
            relative_path=data["relative_path"],
            date_for_repeat=date.fromisoformat(data["date_for_repeat"]),
            number_of_repetitions=data["number_of_repetitions"],
            is_random=data.get("is_random", False)
        )
    
@dataclass
class SessionResult:
    """Результат сессии повтория"""
    note: Note
    score: int # 0=не помню, 1=трудно, 2=легко
    errors_count: int = 0
    
