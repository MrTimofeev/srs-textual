from textual.screen import Screen
from textual.widgets import (
    Header, Footer, Static, Label, Button, 
    ProgressBar, Checkbox, RadioButton, RadioSet
)
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.reactive import var
from textual import log

from data.models import Note, Question, SessionResult
from data.storage import Storage
from parser.question_parser import QuestionParser
from srs.algorithm import SRSAlgorithm
from utils.helpers import make_safe_id
import config


# ==================== DASHBOARD ====================

class DashboardScreen(Screen):
    """Главный экран: список заметок для повторения"""
    
    def __init__(self, storage: Storage):
        super().__init__()
        self.storage = storage
        self.parser = QuestionParser()
        self.selected_notes: list[Note] = []
        self.session_limit: int = 5  # Лимит заметок на сессию
    
    def compose(self):
        """Создание виджетов экрана"""
        yield Header()
        
        with Vertical(classes="container"):
            yield Label("📚 Интервальное повторение", classes="title")
            yield Label(f"📅 {config.TODAY}", classes="subtitle")
            
            # Статус
            yield Static("", id="status-info")
            
            # Список заметок
            with ScrollableContainer(id="notes-list"):
                # Динамически заполняется в on_mount
                pass
            
            # Настройки сессии (если заметок много)
            with Horizontal(id="session-controls", classes="actions"):
                yield Label("Заметок на сессию:")
                yield RadioButton("5", id="limit-5", value=True)
                yield RadioButton("10", id="limit-10")
                yield RadioButton("Все", id="limit-all")
                yield Button("▶ Начать", id="start-btn", variant="primary")
        
        yield Footer()
    
    def on_mount(self):
        """Заполнение списка заметок"""
        due_notes = self.storage.get_due_notes(config.TODAY)
        self.selected_notes = due_notes
        
        # Обновляем статус
        status_text = f"✅ Найдено: {len(due_notes)} заметок"
        if any(n.is_random for n in due_notes):
            status_text += " (включая случайные)"
        self.query_one("#status-info", Static).update(status_text)
        
        # Заполняем список
        notes_container = self.query_one("#notes-list", ScrollableContainer)
        
        if not due_notes:
            notes_container.mount(Label("🎉 Нет заметок для повторения!", classes="success"))
            self.query_one("#start-btn", Button).disabled = True
            return
        
        # Создаём карточки заметок
        for note in due_notes:
            safe_id = make_safe_id(note.file_name, prefix="note-")
            card = Static(
                f"[bold]{note.file_name}[/bold]\n"
                f"[dim]Повторений: {note.number_of_repetitions} | "
                f"След: {note.date_for_repeat}[/dim]",
                classes="note-card",
                id=safe_id
            )
            notes_container.mount(card)
    
    def on_radio_set_changed(self, event: RadioSet.Changed):
        """Обработка выбора лимита сессии"""
        if event.radio_set.id == "session-controls":
            if event.pressed.id == "limit-5":
                self.session_limit = 5
            elif event.pressed.id == "limit-10":
                self.session_limit = 10
            elif event.pressed.id == "limit-all":
                self.session_limit = None
    
    def on_button_pressed(self, event: Button.Pressed):
        """Обработка кнопок"""
        if event.button.id == "start-btn":
            # Применяем лимит
            notes_to_review = (
                self.selected_notes[:self.session_limit] 
                if self.session_limit
                else self.selected_notes
            )
            
            if not notes_to_review:
                self.notify("⚠️ Нет заметок для повторения", severity="warning")
                return
            
            # Запускаем сессию
            self.app.push_screen(
                QuizSessionScreen(self.storage, notes_to_review)
            )

# ==================== QUIZ SESSION ====================

class QuizSessionScreen(Screen):
    """Экран прохождения сессии вопросов"""
    
    # Reactive переменные. При их изменении автоматически вызываются методы watch_*
    current_note_idx = var(0)
    current_question_idx = var(0)
    errors_count = var(0)
    
    def __init__(self, storage: Storage, notes: list[Note]):
        super().__init__()
        self.storage = storage
        self.notes = notes
        self.parser = QuestionParser()
        
        # Обычные переменные состояния
        self.current_questions: list[Question] = []
        self.results: list[SessionResult] = []
        
        # Загружаем вопросы первой заметки сразу
        self._load_current_note_data()

    def _load_current_note_data(self):
        """Загружает данные вопроса (не UI)"""
        if self.current_note_idx >= len(self.notes):
            return
        
        note = self.notes[self.current_note_idx]
        self.current_questions = self.parser.parse_file(note.relative_path)
        self.current_question_idx = 0
        self.errors_count = 0
        
        # Если вопросов нет, сразу завершаем заметку
        if not self.current_questions:
            self._complete_note(score=2)

    def compose(self):
        """Создание виджетов. Вызывается один раз."""
        yield Header()
        
        if not self.notes or self.current_note_idx >= len(self.notes):
            yield Label("Завершение сессии...", classes="title")
            yield Footer()
            return

        note = self.notes[self.current_note_idx]
        
        with Vertical(classes="container"):
            yield Label(f"📄 {note.file_name}", classes="title")
            
            # Прогресс бар (обновляется через watch или on_mount)
            yield ProgressBar(total=len(self.notes), id="note-progress")
            
            # Текстовые блоки (изначально пустые, заполняются в watch)
            yield Label("", classes="subtitle", id="question-label")
            yield Static("", id="question-text")
            
            # Контейнер для кнопок (кнопки создаются динамически внутри)
            with ScrollableContainer(id="options-scroll"):
                yield Vertical(id="options")
            
            # Блок завершения (скрыт по умолчанию)
            yield Label("✅ Все вопросы пройдены", id="done-label", classes="success")
            yield Button("Следующая заметка →", id="next-note-btn", variant="primary")
            
            yield Static("", id="status")
        
        yield Footer()

    async def on_mount(self) -> None:
        """Асинхронная инициализация после создания виджетов"""
        # Обновляем прогресс бар
        try:
            pb = self.query_one("#note-progress", ProgressBar)
            pb.update(value=self.current_note_idx + 1)
        except Exception:
            pass
        
        # Запускаем отрисовку первого вопроса через реактивность
        # Это триггерит метод watch_current_question_idx
        self._update_ui_for_question()

    def _update_ui_for_question(self):
        """Логика обновления UI в зависимости от состояния"""
        # Проверка на выход за границы
        if not self.current_questions or self.current_question_idx >= len(self.current_questions):
            self._show_completion_state()
            return

        self._show_question_state()

    def _show_question_state(self):
        """Отображает вопрос и варианты"""
        q = self.current_questions[self.current_question_idx]
        
        try:
            # Обновляем тексты
            self.query_one("#question-label", Label).update(
                f"Вопрос {self.current_question_idx + 1}/{len(self.current_questions)}"
            )
            self.query_one("#question-text", Static).update(q.text)
            self.query_one("#status", Static).update(f"Ошибок в заметке: {self.errors_count}")
            
            # Скрываем блок завершения
            self.query_one("#done-label", Label).display = False
            self.query_one("#next-note-btn", Button).display = False
            
            # Показываем контейнер вопроса
            self.query_one("#question-label", Label).display = True
            self.query_one("#question-text", Static).display = True
            self.query_one("#options-scroll", ScrollableContainer).display = True
            
            # ✅ ГЛАВНОЕ: Пересоздаем кнопки вариантов
            options_container = self.query_one("#options", Vertical)
            options_container.remove_children() # Очищаем старые
            
            for i, option_text in enumerate(q.options):
                btn = Button(f"{i + 1}. {option_text}", id=f"opt-{i}", variant="default")
                options_container.mount(btn) # Монтируем новые
            
            # Фокус на первую кнопку
            self.set_timer(0.1, self._focus_first_option) # Небольшая задержка для стабильности
            
        except Exception as e:
            log.error(f"Ошибка при отрисовке вопроса: {e}")

    def _show_completion_state(self):
        """Отображает состояние 'вопросы закончились'"""
        try:
            self.query_one("#question-label", Label).display = False
            self.query_one("#question-text", Static).display = False
            self.query_one("#options-scroll", ScrollableContainer).display = False
            
            self.query_one("#done-label", Label).display = True
            self.query_one("#next-note-btn", Button).display = True
            self.query_one("#status", Static).update(f"Итого ошибок: {self.errors_count}")
        except Exception:
            pass

    def _focus_first_option(self):
        """Ставит фокус на первую кнопку"""
        try:
            options_container = self.query_one("#options", Vertical)
            if options_container.children:
                first_btn = options_container.children[0]
                if isinstance(first_btn, Button):
                    first_btn.focus()
        except Exception:
            pass

    # === Реактивные наблюдатели (Watchers) ===
    # Вызываются автоматически при изменении соответствующих переменных
    
    def watch_current_question_idx(self, idx: int) -> None:
        """Срабатывает при переходе к новому вопросу"""
        # Если виджеты еще не созданы (до on_mount), ничего не делаем
        if not self.is_mounted:
            return
        self._update_ui_for_question()

    def watch_errors_count(self, count: int) -> None:
        """Срабатывает при изменении счета ошибок"""
        if self.is_mounted:
            try:
                self.query_one("#status", Static).update(f"Ошибок в заметке: {count}")
            except Exception:
                pass

    def watch_current_note_idx(self, idx: int) -> None:
        """Срабатывает при переходе к новой заметке"""
        if not self.is_mounted:
            return
        
        # Обновляем прогресс бар
        try:
            pb = self.query_one("#note-progress", ProgressBar)
            pb.update(value=idx + 1)
        except Exception:
            pass
        
        # Загружаем данные и обновляем UI
        self._load_current_note_data()
        # _load_current_note_data может вызвать _complete_note, который изменит idx снова.
        # Если мы все еще в той же заметке, рисуем вопрос.
        if self.current_note_idx == idx and self.current_questions:
            self._update_ui_for_question()

    # === Обработчики событий ===

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "next-note-btn":
            self._complete_note(score=2)
            return
        
        if btn_id.startswith("opt-"):
            selected_idx = int(btn_id.split("-")[1])
            
            if not self.current_questions or self.current_question_idx >= len(self.current_questions):
                return
            
            q = self.current_questions[self.current_question_idx]
            is_correct = q.is_correct(selected_idx)
            
            if is_correct:
                self.notify("✅ Верно!", severity="success", timeout=1)
                # Переход к следующему вопросу (триггерит watch_current_question_idx)
                self.current_question_idx += 1
            else:
                self.notify("❌ Ошибка!", severity="error", timeout=2)
                self.errors_count += 1 # Триггерит watch_errors_count
                self._highlight_correct_answer(q.correct_index)
                # При ошибке не переключаем вопрос, даем посмотреть

    def _highlight_correct_answer(self, correct_idx: int):
        """Подсвечивает правильный ответ"""
        try:
            options_container = self.query_one("#options", Vertical)
            for i, widget in enumerate(options_container.children):
                if isinstance(widget, Button):
                    if i == correct_idx:
                        widget.add_class("correct")
                    widget.disabled = True
        except Exception:
            pass

    def _complete_note(self, score: int):
        """Завершает заметку"""
        if self.current_note_idx >= len(self.notes):
            return
        
        note = self.notes[self.current_note_idx]
        self.results.append(SessionResult(note=note, score=score, errors_count=self.errors_count))
        
        next_date, new_reps = SRSAlgorithm.calculate_next_date(
            score=score,
            repetitions=note.number_of_repetitions,
            today=config.TODAY
        )
        self.storage.update_note(
            note.file_name,
            date_for_repeat=next_date,
            number_of_repetitions=new_reps
        )
        
        # Переход к следующей заметке (триггерит watch_current_note_idx)
        self.current_note_idx += 1
        
        if self.current_note_idx >= len(self.notes):
            self.app.push_screen(SummaryScreen(self.results))

        
# ==================== SUMMARY ====================

class SummaryScreen(Screen):
    """Экран итогов сессии"""
    
    def __init__(self, results: list[SessionResult]):
        super().__init__()
        self.results = results
    
    def compose(self):
        yield Header()
        
        with Vertical(classes="container"):
            yield Label("🎉 Сессия завершена!", classes="title")
            
            # Статистика
            total = len(self.results)
            perfect = sum(1 for r in self.results if r.score == 2 and r.errors_count == 0)
            errors = sum(r.errors_count for r in self.results)
            
            yield Static(
                f"📊 Пройдено: {total}\n"
                f"✅ Без ошибок: {perfect}\n"
                f"❌ Всего ошибок: {errors}",
                id="stats"
            )
            
            # Детали по заметкам
            yield Label("📋 Результаты:", classes="subtitle")
            with ScrollableContainer():
                for r in self.results:
                    status = "✅" if r.score == 2 else ("⚠️" if r.score == 1 else "❌")
                    yield Static(
                        f"{status} {r.note.file_name}\n"
                        f"   [dim]Ошибок: {r.errors_count} | "
                        f"След: {r.note.date_for_repeat}[/dim]"
                    )
            
            # Кнопки
            with Horizontal(classes="actions"):
                yield Button("🔄 Повторить", id="retry-btn")
                yield Button("🏠 В меню", id="home-btn", variant="primary")
        
        yield Footer()
    
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "home-btn":
            self.app.pop_screen()  # Возврат к Dashboard
        elif event.button.id == "retry-btn":
            # Запуск новой сессии со случайными заметками
            from data.storage import Storage
            storage = Storage()
            due_notes = storage.get_due_notes(config.TODAY)
            if due_notes:
                self.app.push_screen(QuizSessionScreen(storage, due_notes[:5]))
            else:
                self.notify("🎉 Нет заметок для повторения!", severity="success")
        
        
            
        