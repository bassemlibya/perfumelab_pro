# core/managers/currency_manager.py
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from core.database.connection import DatabaseManager

class CurrencyManager:
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
        self._default_currency = None
        self._rates_cache = {}

    def get_default_currency(self) -> Dict:
        if not self._default_currency:
            result = self.db.execute_one(
                "SELECT * FROM currencies WHERE is_default = 1 LIMIT 1"
            )
            if result:
                self._default_currency = result
        return self._default_currency or {'code': 'USD', 'symbol': '$', 'name_ar': 'الدولار'}

    def get_active_currencies(self) -> List[Dict]:
        return self.db.execute(
            "SELECT * FROM currencies WHERE is_active = 1 ORDER BY is_default DESC, code"
        )

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return 1.0

        cache_key = f"{from_currency}_{to_currency}"
        if cache_key not in self._rates_cache:
            result = self.db.execute_one(
                "SELECT rate FROM exchange_rates WHERE from_currency = ? AND to_currency = ? AND is_active = 1 ORDER BY effective_date DESC LIMIT 1",
                (from_currency, to_currency)
            )
            rate = result['rate'] if result else 1.0
            self._rates_cache[cache_key] = rate

        return self._rates_cache[cache_key]

    def convert(self, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return amount
        rate = self.get_exchange_rate(from_currency, to_currency)
        return round(amount * rate, 6)

    def convert_to_base(self, amount: float, from_currency: str) -> float:
        base = self.get_default_currency()['code']
        return self.convert(amount, from_currency, base)

    def convert_from_base(self, amount: float, to_currency: str) -> float:
        base = self.get_default_currency()['code']
        return self.convert(amount, base, to_currency)

    def update_rate(self, from_currency: str, to_currency: str, rate: float):
        inv_rate = 1/rate if rate else 1
        self.db.execute_insert(
            "INSERT INTO exchange_rates (from_currency, to_currency, rate, inverse_rate, effective_date) VALUES (?, ?, ?, ?, ?)",
            (from_currency, to_currency, rate, inv_rate, datetime.now())
        )
        self._rates_cache[f"{from_currency}_{to_currency}"] = rate
        self._rates_cache[f"{to_currency}_{from_currency}"] = inv_rate

    def format_amount(self, amount: float, currency_code: str, use_arabic: bool = True) -> str:
        result = self.db.execute_one(
            "SELECT symbol, symbol_ar, decimal_places, position FROM currencies WHERE code = ?",
            (currency_code,)
        )
        if not result:
            return f"{amount:,.2f}"

        symbol = result['symbol_ar'] or result['symbol'] if use_arabic else result['symbol']
        decimals = result['decimal_places'] or 2
        position = result['position'] or 'after'

        formatted = f"{amount:,.{decimals}f}"

        if use_arabic:
            arabic_numerals = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
            formatted = formatted.translate(arabic_numerals)

        if position == 'before':
            return f"{symbol} {formatted}"
        return f"{formatted} {symbol}"

    def add_currency(self, code: str, name_ar: str, name_en: str, symbol: str, 
                     symbol_ar: str = None, decimal_places: int = 2):
        return self.db.execute_insert(
            "INSERT INTO currencies (code, name_ar, name_en, symbol, symbol_ar, decimal_places) VALUES (?, ?, ?, ?, ?, ?)",
            (code, name_ar, name_en, symbol, symbol_ar, decimal_places)
        )

    def set_default_currency(self, code: str):
        self.db.execute_update("UPDATE currencies SET is_default = 0")
        self.db.execute_update("UPDATE currencies SET is_default = 1 WHERE code = ?", (code,))
        self._default_currency = None
