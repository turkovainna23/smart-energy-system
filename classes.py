from datetime import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class Building:
    """Клас для представлення будинку"""
    address: str
    floors_count: int
    sections_count: int
    developer: str
    city: str
    id: Optional[int] = None
   
    def __post_init__(self):
        if self.floors_count <= 0:
            raise ValueError("Кількість поверхів повинна бути більше 0")
        if self.sections_count <= 0:
            raise ValueError("Кількість секцій повинна бути більше 0")


@dataclass
class Apartment:
    """Клас для представлення квартири"""
    building_id: int
    number: str
    floor: int
    area_sqm: float
    tariff_plan: str
    owner_name: str
    id: Optional[int] = None
   
    def __post_init__(self):
        if self.floor <= 0:
            raise ValueError("Поверх повинен бути більше 0")
        if self.area_sqm <= 0:
            raise ValueError("Площа повинна бути більше 0")
   
    def calculate_monthly_limit(self) -> float:
        """Розрахунок місячного ліміту споживання (кВт·год)"""
        # Базовий розрахунок: 50 кВт·год на кв.м на рік / 12 місяців
        return (self.area_sqm * 50) / 12


@dataclass
class Meter:
    """Клас для представлення лічильника"""
    apartment_id: int
    meter_type: str  # Smart, Analog
    serial_number: str
    firmware_version: str
    supports_remote_cutoff: bool = True
    status: str = "Active"  # Active, Offline, Maintenance
    id: Optional[int] = None
   
    def self_test(self) -> bool:
        """Самодіагностика лічильника"""
        # Імітація тесту
        return self.status == "Active"


@dataclass
class SensorData:
    """Клас для телеметричних даних"""
    meter_id: int
    voltage: float  # Напруга, В
    current: float  # Струм, А
    power: float  # Потужність, кВт
    frequency: float  # Частота, Гц
    power_factor: float  # Коефіцієнт потужності
    energy_consumed: float  # Накопичене споживання, кВт·год
    timestamp: str = None
    id: Optional[int] = None
   
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   
    def calculate_power(self) -> float:
        """Розрахунок потужності за формулою P = U * I * cos(φ)"""
        return self.voltage * self.current * self.power_factor / 1000  # переведення в кВт
   
    def is_voltage_normal(self) -> bool:
        """Перевірка чи напруга в нормі (220-240 В)"""
        return 220 <= self.voltage <= 240
   
    def is_frequency_normal(self) -> bool:
        """Перевірка чи частота в нормі (49.8-50.2 Гц)"""
        return 49.8 <= self.frequency <= 50.2
   
    def detect_overload(self, max_power: float = 10.0) -> bool:
        """Виявлення перевантаження"""
        return self.power > max_power
   
    def detect_voltage_drop(self) -> bool:
        """Виявлення падіння напруги"""
        return self.voltage < 200
   
    def detect_phase_loss(self) -> bool:
        """Виявлення втрати фази (імітація)"""
        return self.voltage < 180


@dataclass
class Alert:
    """Клас для аварійних подій"""
    alert_type: str  # Overload, VoltageDrop, PhaseLoss, ShortCircuit, Tamper
    severity: str  # Low, Medium, High, Critical
    message: str
    meter_id: Optional[int] = None
    apartment_id: Optional[int] = None
    timestamp: str = None
    resolved: bool = False
    acknowledged_by: Optional[str] = None
    action_taken: Optional[str] = None
    resolved_at: Optional[str] = None
    id: Optional[int] = None
   
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   
    def mark_resolved(self, engineer: str, action: str):
        """Позначити аварію як вирішену"""
        self.resolved = True
        self.acknowledged_by = engineer
        self.action_taken = action
        self.resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
   
    def get_severity_color(self) -> str:
        """Отримати колір залежно від критичності"""
        colors = {
            "Low": "#4CAF50",
            "Medium": "#FFC107",
            "High": "#FF9800",
            "Critical": "#F44336"
        }
        return colors.get(self.severity, "#9E9E9E")


@dataclass
class User:
    """Клас для користувача системи"""
    role: str  # Resident, Engineer, Admin
    login: str
    password_hash: str
    apartment_id: Optional[int] = None
    status: str = "Active"  # Active, Blocked
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    id: Optional[int] = None
   
    def has_permission(self, permission: str) -> bool:
        """Перевірка дозволів користувача"""
        permissions = {
            "Resident": ["view_own_data", "view_consumption"],
            "Engineer": ["view_all_data", "acknowledge_alerts", "remote_control"],
            "Admin": ["view_all_data", "manage_users", "manage_buildings", "manage_alerts"]
        }
        return permission in permissions.get(self.role, [])


@dataclass
class Report:
    """Клас для звітів"""
    scope: str  # Apartment, Building, Section
    period_start: str
    period_end: str
    avg_power: float
    peak_power: float
    total_energy: float
    total_cost: float
    alerts_count: int
    id: Optional[int] = None
   
    def generate_summary(self) -> str:
        """Генерація короткого опису звіту"""
        return f"""
Звіт за період {self.period_start} - {self.period_end}
Середня потужність: {self.avg_power:.2f} кВт
Пікова потужність: {self.peak_power:.2f} кВт
Загальне споживання: {self.total_energy:.2f} кВт·год
Вартість: {self.total_cost:.2f} грн
Кількість аварій: {self.alerts_count}
"""


class AutonomousSystem:
    """Клас для імітації автономної роботи при аварійних відключеннях"""
   
    def __init__(self, building_id: int):
        self.building_id = building_id
        self.backup_power_available = True
        self.backup_capacity = 100.0  # кВт·год
        self.current_load = 0.0
        self.priority_apartments = []  # Пріоритетні квартири (медичне обладнання)
   
    def calculate_backup_duration(self, total_consumption: float) -> float:
        """Розрахунок часу автономної роботи (години)"""
        if total_consumption <= 0:
            return 0
        return self.backup_capacity / total_consumption
   
    def optimize_load_distribution(self, apartments_load: dict) -> dict:
        """Оптимізація розподілу навантаження при автономній роботі"""
        # Сортуємо квартири за пріоритетом
        sorted_apartments = sorted(
            apartments_load.items(),
            key=lambda x: x[0] in self.priority_apartments,
            reverse=True
        )
       
        optimized = {}
        remaining_capacity = self.backup_capacity
       
        for apt_id, load in sorted_apartments:
            if remaining_capacity >= load:
                optimized[apt_id] = load
                remaining_capacity -= load
            else:
                # Обмежуємо навантаження
                optimized[apt_id] = remaining_capacity * 0.5
                remaining_capacity *= 0.5
       
        return optimized
   
    def calculate_phase_imbalance(self, phase_currents: list) -> float:
        """Розрахунок несиметрії фаз (%)"""
        if len(phase_currents) != 3:
            return 0
       
        avg_current = sum(phase_currents) / 3
        if avg_current == 0:
            return 0
       
        max_deviation = max(abs(i - avg_current) for i in phase_currents)
        imbalance = (max_deviation / avg_current) * 100
       
        return imbalance
   
    def estimate_battery_health(self, cycles: int, age_years: float) -> float:
        """Оцінка стану акумуляторів (%)"""
        # Спрощена модель деградації
        cycle_degradation = cycles * 0.01  # 1% на 100 циклів
        age_degradation = age_years * 5  # 5% на рік
       
        health = 100 - cycle_degradation - age_degradation
        return max(0, min(100, health))