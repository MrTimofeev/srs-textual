from data.storage import Storage
from parser.question_parser import QuestionParser

def test():
    print("🔍 Тестирование системы...\n")
    
    # 1. Тест хранилища
    storage = Storage()
    new_count = storage.scan_for_new_notes()
    print(f"✅ Найдено новых заметок: {new_count}")
    print(f"📊 Всего заметок в базе: {len(storage.notes)}\n")
    
    # 2. Тест парсера
    parser = QuestionParser()
    
    if storage.notes:
        test_note = storage.notes[0]
        print(f"📄 Тестируем заметку: {test_note.file_name}")
        
        questions = parser.parse_file(test_note.relative_path)
        print(f"❓ Найдено вопросов: {len(questions)}\n")
        
        for i, q in enumerate(questions, 1):
            print(f"Вопрос #{i}: {q.text}")
            for j, opt in enumerate(q.options):
                mark = "✅" if j == q.correct_index else "  "
                print(f"  {mark} {opt}")
            print()
    else:
        print("⚠️ Нет заметок для тестирования. Добавьте файл с тегом #повторить")
    
    print("🎉 Тест завершён!")

if __name__ == "__main__":
    test()