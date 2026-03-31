import re
import hashlib

def make_safe_id(text: str, prefix: str = "") -> str:
    """
    Преобразует любую строку в безопасный ID для Textual.
    
    Правила:
    1. Только латинские буквы, цифры, подчеркивания и дефисы
    2. Не может начинаться с цифры
    3. Уникальность (на основе хеша)
    """
    # 1. Транслитерация или замена нелатинских символов на _
    # Простой вариант: заменяем всё не ASCII на подчеркивание
    safe_text = re.sub(r'[^a-zA-Z0-9_-]', '_', text)
    
    # 2. Убираем расширения и лишние точки
    safe_text = safe_text.replace('.', '_')
    
    # 3. Если начинается с цифры — добавляем префикс
    if safe_text and safe_text[0].isdigit():
        safe_text = f"n_{safe_text}"
    
    # 4. Обрезаем до разумной длины (ID не должны быть гигантскими)
    if len(safe_text) > 50:
        # Сохраняем начало и добавляем хеш для уникальности
        hash_part = hashlib.md5(text.encode()).hexdigest()[:8]
        safe_text = f"{safe_text[:40]}_{hash_part}"
    
    return f"{prefix}{safe_text}" if prefix else safe_text