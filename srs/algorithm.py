from datetime import date, timedelta
from typing import Tuple


class SRSAlgorithm:
    """Алгоритм интервального повторения (SM-2 стиль)"""
    
    @staticmethod
    def calculate_next_interval(
        score: int,
        repetitions: int,
        current_interval: int
    ) -> Tuple[int, int]:
        """
        Рассчитывает следующий интервал и количество повторений.
        
        Args:
            score: 0=не помню, 1=трудно, 2=легко
            repetitions: текущее количество успешных повторений
            current_interval: текущий интервал в днях
            
        Returns:
            (new_interval_days, new_repetitions)
        """
        if score == 0:  # Не помню — сброс
            return 1, 0
        
        elif score == 1:  # Трудно — минимальный интервал
            return 1, repetitions + 1
        
        elif score == 2:  # Легко — растущий интервал
            new_repetitions = repetitions + 1
            
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 6
            else:
                # Экспоненциальный рост (коэффициент 2.5)
                new_interval = int(current_interval * 2.5)
            
            return new_interval, new_repetitions
        
        # По умолчанию
        return 1, repetitions
    
    @staticmethod
    def calculate_next_date(
        score: int,
        repetitions: int,
        today: date
    ) -> Tuple[date, int]:
        """
        Рассчитывает следующую дату повторения.
        
        Returns:
            (next_date, new_repetitions)
        """
        interval_days, new_reps = SRSAlgorithm.calculate_next_interval(
            score=score,
            repetitions=repetitions,
            current_interval=repetitions  # Используем repetitions как proxy для интервала
        )
        
        next_date = today + timedelta(days=interval_days)
        return next_date, new_reps