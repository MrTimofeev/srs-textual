from pathlib import Path
from typing import List, Optional
from data.models import Question
import config


class QuestionParser:
    """Парсит вопросы из Markdown файлов"""
    
    def __init__(self):
        self.quiz_start = config.QUIZ_START
        self.quiz_end = config.QUIZ_END
    
    def parse_file(self, relative_path: str) -> List[Question]:
        """Извлекает вопросы из файла заметки"""
        file_path = Path(config.BASE_DIR) / relative_path
        questions: List[Question] = []
        
        if not file_path.exists():
            print(f"⚠️ Файл не найден: {file_path}")
            return questions
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠️ Ошибка чтения файла {file_path}: {e}")
            return questions
        
        # Ищем блок с вопросами
        if self.quiz_start not in content or self.quiz_end not in content:
            return questions
        
        # Вырезаем блок вопросов
        try:
            block = content.split(self.quiz_start)[1].split(self.quiz_end)[0]
        except IndexError:
            return questions
        
        lines = block.strip().split("\n")
        current_question = None
        
        for line in lines:
            line = line.strip()
            
            # Начало нового вопроса
            if line.startswith("Q:"):
                # ✅ ВАЖНО: Сохраняем предыдущий вопрос как объект Question
                if current_question and current_question["options"]:
                    questions.append(Question(
                        text=current_question["text"],
                        options=current_question["options"],
                        correct_index=current_question["correct_index"]
                    ))
                
                # Создаём новый вопрос (пока как dict для удобства парсинга)
                current_question = {
                    "text": line[2:].strip(),
                    "options": [],
                    "correct_index": -1
                }
            
            # Вариант ответа
            elif line.startswith("- [") and current_question:
                is_correct = "x" in line
                # Извлекаем текст после ]
                text = line.split("]", 1)[1].strip() if "]" in line else line
                current_question["options"].append(text)
                
                if is_correct:
                    current_question["correct_index"] = len(current_question["options"]) - 1
        
        # ✅ ВАЖНО: Добавляем ПОСЛЕДНИЙ вопрос как объект Question
        if current_question and current_question["options"]:
            questions.append(Question(
                text=current_question["text"],
                options=current_question["options"],
                correct_index=current_question["correct_index"]
            ))
        
        return questions
    
    def has_questions(self, relative_path: str) -> bool:
        """Проверяет, есть ли вопросы в файле"""
        return len(self.parse_file(relative_path)) > 0