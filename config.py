from pathlib import Path
from datetime import date

# Основные пути
BASE_DIR = Path("C:/home/База Знаний/pc/Programming")
REVIEWS_FILE = BASE_DIR / "08. Повторение" / "reviews.json"

# Маркеры для парсинга вопросов
QUIZ_START = "<!-- QUIZ_START -->"
QUIZ_END = "<!-- QUIZ_END -->"

# Настройки SRS
DEFAULT_RANDOM_COUNT = 5  # Сколько случайных брать если нет запланированных
MAX_NOTES_PER_SESSION = None  # None = без лимита, int = лимит

# Текущая дата
TODAY = date.today()
 
