from utils.helpers import make_safe_id

test_cases = [
    "32 и 64 битная система.md",
    "Test note anki.md",
    "123开始.md",
    "Normal_File-Name.txt",
    "Очень длинное название заметки которое точно превысит лимит в пятьдесят символов.md"
]

print("Тестирование make_safe_id:\n")
for case in test_cases:
    safe = make_safe_id(case, prefix="note-")
    print(f"❌ {case}")
    print(f"✅ {safe}\n")