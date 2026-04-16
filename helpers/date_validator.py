from datetime import datetime, date
from typing import Optional


class DateValidator:
    @staticmethod
    def validate(date_str: str) -> Optional[date]:
        parsed = DateValidator.parse(date_str)
        return parsed
    
    @staticmethod
    def parse(date_str: str) -> date:
        formats = [
            "%d.%m.%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    @staticmethod
    def is_valid_format(date_str: str) -> bool:
        try:
            DateValidator.parse(date_str)
            return True
        except ValueError:
            return False