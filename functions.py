import sqlite3
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from classes import Building, Apartment, Meter, SensorData, Alert, User, Report


class DatabaseManager:
    """Менеджер бази даних"""
   
    def __init__(self, db_name: str = "gravity_park.db"):
        self.db_name = db_name
        self.create_tables()
   
    def get_connection(self):
        """Отримання з'єднання з БД"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
   
    def create_tables(self):
        """Створення таблиць бази даних"""
        conn = self.get_connection()
        cursor = conn.cursor()
       
        # Таблиця будинків
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                floors_count INTEGER NOT NULL,
                sections_count INTEGER NOT NULL,
                developer TEXT,
                city TEXT
            )
        """)
       
        # Таблиця квартир
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS apartments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                number TEXT NOT NULL,
                floor INTEGER NOT NULL,
                area_sqm REAL NOT NULL,
                tariff_plan TEXT,
                owner_name TEXT,
                FOREIGN KEY (building_id) REFERENCES buildings(id)
            )
        """)
       
        # Таблиця лічильників
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                apartment_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                serial_number TEXT UNIQUE NOT NULL,
                firmware_version TEXT,
                supports_remote_cutoff INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Active',
                FOREIGN KEY (apartment_id) REFERENCES apartments(id)
            )
        """)
       
        # Таблиця телеметрії
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                voltage REAL NOT NULL,
                current REAL NOT NULL,
                power REAL NOT NULL,
                frequency REAL NOT NULL,
                power_factor REAL NOT NULL,
                energy_consumed REAL NOT NULL,
                FOREIGN KEY (meter_id) REFERENCES meters(id)
            )
        """)
       
        # Таблиця аварій
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meter_id INTEGER,
                apartment_id INTEGER,
                type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                resolved INTEGER DEFAULT 0,
                acknowledged_by TEXT,
                action_taken TEXT,
                resolved_at TEXT,
                FOREIGN KEY (meter_id) REFERENCES meters(id),
                FOREIGN KEY (apartment_id) REFERENCES apartments(id)
            )
        """)
       
        # Таблиця користувачів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                login TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                apartment_id INTEGER,
                status TEXT DEFAULT 'Active',
                full_name TEXT,
                email TEXT,
                phone TEXT,
                FOREIGN KEY (apartment_id) REFERENCES apartments(id)
            )
        """)
       
        # Таблиця звітів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                scope TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                avg_power REAL NOT NULL,
                peak_power REAL NOT NULL,
                total_energy REAL NOT NULL,
                total_cost REAL NOT NULL,
                alerts_count INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id)
            )
        """)
       
        # Таблиця логів імітації
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                cycles_count INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (building_id) REFERENCES buildings(id)
            )
        """)
       
        conn.commit()
        conn.close()
   
    # Методи для роботи з будинками
    def add_building(self, building: Building) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO buildings (address, floors_count, sections_count, developer, city)
            VALUES (?, ?, ?, ?, ?)
        """, (building.address, building.floors_count, building.sections_count,
              building.developer, building.city))
        building_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return building_id
   
    def get_all_buildings(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buildings")
        buildings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return buildings
   
    def get_building_by_id(self, building_id: int) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buildings WHERE id = ?", (building_id,))
        building = dict(cursor.fetchone())
        conn.close()
        return building
   
    def delete_building(self, building_id: int):
        """Видалення будинку та всіх пов'язаних даних"""
        conn = self.get_connection()
        cursor = conn.cursor()
       
        # Отримуємо всі квартири будинку
        cursor.execute("SELECT id FROM apartments WHERE building_id = ?", (building_id,))
        apartment_ids = [row['id'] for row in cursor.fetchall()]
       
        # Видаляємо всі пов'язані дані
        for apt_id in apartment_ids:
            # Видаляємо дані лічильників
            cursor.execute("DELETE FROM sensor_data WHERE meter_id IN (SELECT id FROM meters WHERE apartment_id = ?)", (apt_id,))
            cursor.execute("DELETE FROM alerts WHERE apartment_id = ?", (apt_id,))
            cursor.execute("DELETE FROM meters WHERE apartment_id = ?", (apt_id,))
       
        # Видаляємо квартири
        cursor.execute("DELETE FROM apartments WHERE building_id = ?", (building_id,))
       
        # Видаляємо звіти
        cursor.execute("DELETE FROM reports WHERE building_id = ?", (building_id,))
        cursor.execute("DELETE FROM simulation_logs WHERE building_id = ?", (building_id,))
       
        # Видаляємо будинок
        cursor.execute("DELETE FROM buildings WHERE id = ?", (building_id,))
       
        conn.commit()
        conn.close()
   
    def get_building_stats(self, building_id: int) -> Dict:
        """Отримання статистики будинку"""
        conn = self.get_connection()
        cursor = conn.cursor()
       
        # Кількість квартир
        cursor.execute("SELECT COUNT(*) as count FROM apartments WHERE building_id = ?", (building_id,))
        apartments_count = cursor.fetchone()['count']
       
        # Активні лічильники
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM meters m
            JOIN apartments a ON m.apartment_id = a.id
            WHERE a.building_id = ? AND m.status = 'Active'
        """, (building_id,))
        active_meters = cursor.fetchone()['count']
       
        # Середнє споживання
        cursor.execute("""
            SELECT AVG(sd.power) as avg_power, MAX(sd.power) as peak_power
            FROM sensor_data sd
            JOIN meters m ON sd.meter_id = m.id
            JOIN apartments a ON m.apartment_id = a.id
            WHERE a.building_id = ?
                AND sd.timestamp > datetime('now', '-1 hour')
        """, (building_id,))
        result = cursor.fetchone()
        avg_power = result['avg_power'] if result['avg_power'] else 0
        peak_power = result['peak_power'] if result['peak_power'] else 0
       
        # Активні аварії
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM alerts al
            JOIN apartments a ON al.apartment_id = a.id
            WHERE a.building_id = ? AND al.resolved = 0
        """, (building_id,))
        active_alerts = cursor.fetchone()['count']
       
        conn.close()
       
        return {
            'apartments_count': apartments_count,
            'active_meters': active_meters,
            'avg_power': avg_power,
            'peak_power': peak_power,
            'active_alerts': active_alerts
        }
    
    def building_has_critical_alert(self, building_id: int) -> bool:
        """Перевіряє, чи є в будинку невирішена критична аварія"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM alerts al
            JOIN apartments a ON al.apartment_id = a.id
            WHERE a.building_id = ?
              AND al.severity = 'Critical'
              AND al.resolved = 0
        """, (building_id,))
        row = cursor.fetchone()
        conn.close()
        return (row['count'] if row else 0) > 0

    def resolve_building_critical_alerts(
        self,
        building_id: int,
        engineer: str = "System",
        action: str = "Автоматичне відновлення живлення"
    ) -> None:
        """Позначити всі критичні аварії будинку як вирішені"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts
            SET resolved = 1,
                acknowledged_by = ?,
                action_taken = ?,
                resolved_at = datetime('now')
            WHERE id IN (
                SELECT al.id
                FROM alerts al
                JOIN apartments a ON al.apartment_id = a.id
                WHERE a.building_id = ?
                  AND al.severity = 'Critical'
                  AND al.resolved = 0
            )
        """, (engineer, action, building_id))
        conn.commit()
        conn.close()

    
    def building_has_critical_alert(self, building_id: int) -> bool:
        """Чи є в будинку невирішена критична аварія"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM alerts al
            JOIN apartments a ON al.apartment_id = a.id
            WHERE a.building_id = ?
              AND al.severity = 'Critical'
              AND al.resolved = 0
        """, (building_id,))
        count = cursor.fetchone()['count']
        conn.close()
        return count > 0

    def get_building_meters(self, building_id: int) -> List[Dict]:
        """Отримання всіх лічильників будинку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, a.number as apartment_number, a.id as apartment_id
            FROM meters m
            JOIN apartments a ON m.apartment_id = a.id
            WHERE a.building_id = ?
        """, (building_id,))
        meters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return meters
   
    def resolve_alert(self, alert_id: int, engineer: str, action: str):
        """Позначити аварію як вирішену"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts
            SET resolved = 1,
                acknowledged_by = ?,
                action_taken = ?,
                resolved_at = datetime('now')
            WHERE id = ?
        """, (engineer, action, alert_id))
        conn.commit()
        conn.close()
   
    def get_building_detailed_stats(self, building_id: int) -> Dict:
        """Детальна статистика будинку для звіту"""
        conn = self.get_connection()
        cursor = conn.cursor()
       
        # Загальна статистика споживання
        cursor.execute("""
            SELECT
                AVG(sd.power) as avg_power,
                MAX(sd.power) as peak_power,
                SUM(sd.energy_consumed) as total_energy
            FROM sensor_data sd
            JOIN meters m ON sd.meter_id = m.id
            JOIN apartments a ON m.apartment_id = a.id
            WHERE a.building_id = ?
                AND sd.timestamp > datetime('now', '-24 hours')
        """, (building_id,))
        result = cursor.fetchone()
       
        avg_power = result['avg_power'] if result['avg_power'] else 0
        peak_power = result['peak_power'] if result['peak_power'] else 0
        total_energy = result['total_energy'] if result['total_energy'] else 0
       
        # Вартість (тариф 1.68 грн/кВт·год)
        total_cost = total_energy * 1.68
       
        # Статистика аварій
        cursor.execute("""
            SELECT
                COUNT(*) as total_alerts,
                SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved_alerts,
                SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as active_alerts
            FROM alerts al
            JOIN apartments a ON al.apartment_id = a.id
            WHERE a.building_id = ?
        """, (building_id,))
        alerts_result = cursor.fetchone()
       
        # Квартири з найбільшою кількістю аварій
        cursor.execute("""
            SELECT
                a.number,
                COUNT(*) as alerts_count
            FROM alerts al
            JOIN apartments a ON al.apartment_id = a.id
            WHERE a.building_id = ?
            GROUP BY a.id
            ORDER BY alerts_count DESC
            LIMIT 5
        """, (building_id,))
        problem_apartments = [dict(row) for row in cursor.fetchall()]
       
        conn.close()
       
        return {
            'avg_power': round(avg_power, 2),
            'peak_power': round(peak_power, 2),
            'total_energy': round(total_energy, 2),
            'total_cost': round(total_cost, 2),
            'alerts_count': alerts_result['total_alerts'],
            'resolved_alerts': alerts_result['resolved_alerts'],
            'active_alerts': alerts_result['active_alerts'],
            'problem_apartments': problem_apartments
        }
    
    def building_has_critical_alert(self, building_id: int) -> bool:
        """Перевіряє, чи є в будинку невирішена критична аварія"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) AS count
            FROM alerts al
            JOIN apartments a ON al.apartment_id = a.id
            WHERE a.building_id = ?
              AND al.severity = 'Critical'
              AND al.resolved = 0
        """, (building_id,))
        row = cursor.fetchone()
        conn.close()
        return (row['count'] if row else 0) > 0

    def resolve_building_critical_alerts(
        self,
        building_id: int,
        engineer: str = "System",
        action: str = "Автоматичне відновлення живлення"
    ) -> None:
        """Позначити всі критичні аварії будинку як вирішені"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE alerts
            SET resolved = 1,
                acknowledged_by = ?,
                action_taken = ?,
                resolved_at = datetime('now')
            WHERE id IN (
                SELECT al.id
                FROM alerts al
                JOIN apartments a ON al.apartment_id = a.id
                WHERE a.building_id = ?
                  AND al.severity = 'Critical'
                  AND al.resolved = 0
            )
        """, (engineer, action, building_id))
        conn.commit()
        conn.close()

   
    def add_report(self, building_id: int, report: Report) -> int:
        """Додавання звіту"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reports (building_id, scope, period_start, period_end,
                               avg_power, peak_power, total_energy, total_cost, alerts_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (building_id, report.scope, report.period_start, report.period_end,
              report.avg_power, report.peak_power, report.total_energy,
              report.total_cost, report.alerts_count))
        report_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return report_id
   
    def save_simulation_report(self, building_id: int, start_time: str,
                              end_time: str, cycles_count: int, duration_seconds: float):
        """Збереження звіту про імітацію"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO simulation_logs (building_id, start_time, end_time,
                                        cycles_count, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (building_id, start_time, end_time, cycles_count, duration_seconds))
        conn.commit()
        conn.close()
   
    def update_building(self, building_id: int, address: str, floors_count: int,
                       sections_count: int, developer: str, city: str):
        """Оновлення параметрів будинку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE buildings
            SET address = ?, floors_count = ?, sections_count = ?,
                developer = ?, city = ?
            WHERE id = ?
        """, (address, floors_count, sections_count, developer, city, building_id))
        conn.commit()
        conn.close()
   
    # Методи для роботи з квартирами
    def add_apartment(self, apartment: Apartment) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO apartments (building_id, number, floor, area_sqm, tariff_plan, owner_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (apartment.building_id, apartment.number, apartment.floor,
              apartment.area_sqm, apartment.tariff_plan, apartment.owner_name))
        apartment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return apartment_id
   
    def get_all_apartments(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apartments")
        apartments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return apartments
   
    def get_all_apartments_with_buildings(self) -> List[Dict]:
        """Отримання всіх квартир з інформацією про будинки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, b.address as building_address
            FROM apartments a
            JOIN buildings b ON a.building_id = b.id
            ORDER BY b.address, a.number
        """)
        apartments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return apartments
   
    def get_building_apartments_monitoring(self, building_id: int) -> List[Dict]:
        """Отримання даних моніторингу квартир будинку"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                a.number,
                a.floor,
                sd.voltage,
                sd.current,
                sd.power
            FROM apartments a
            LEFT JOIN meters m ON a.id = m.apartment_id
            LEFT JOIN (
                SELECT meter_id, voltage, current, power,
                       ROW_NUMBER() OVER (PARTITION BY meter_id ORDER BY timestamp DESC) as rn
                FROM sensor_data
            ) sd ON m.id = sd.meter_id AND sd.rn = 1
            WHERE a.building_id = ?
            ORDER BY a.number
        """, (building_id,))
        apartments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return apartments
   
    # Методи для роботи з лічильниками
    def add_meter(self, meter: Meter) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO meters (apartment_id, type, serial_number, firmware_version,
                              supports_remote_cutoff, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (meter.apartment_id, meter.meter_type, meter.serial_number,
              meter.firmware_version, meter.supports_remote_cutoff, meter.status))
        meter_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return meter_id
   
    def get_all_meters(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, a.number as apartment_number
            FROM meters m
            JOIN apartments a ON m.apartment_id = a.id
        """)
        meters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return meters
   
    def get_all_meters_with_buildings(self) -> List[Dict]:
        """Отримання всіх лічильників з інформацією про будинки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.*, a.number as apartment_number, b.address as building_address
            FROM meters m
            JOIN apartments a ON m.apartment_id = a.id
            JOIN buildings b ON a.building_id = b.id
            ORDER BY b.address, a.number
        """)
        meters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return meters
   
    # Методи для роботи з телеметрією
    def add_sensor_data(self, data: SensorData) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_data (meter_id, timestamp, voltage, current, power,
                                    frequency, power_factor, energy_consumed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (data.meter_id, data.timestamp, data.voltage, data.current,
              data.power, data.frequency, data.power_factor, data.energy_consumed))
        data_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return data_id
   
    def get_recent_sensor_data(self, limit: int = 100) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sd.*, a.number as apartment_number
            FROM sensor_data sd
            JOIN meters m ON sd.meter_id = m.id
            JOIN apartments a ON m.apartment_id = a.id
            ORDER BY sd.timestamp DESC
            LIMIT ?
        """, (limit,))
        data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return data
   
    # Методи для роботи з аваріями
    def add_alert(self, alert: Alert) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (meter_id, apartment_id, type, severity, message,
                              timestamp, resolved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (alert.meter_id, alert.apartment_id, alert.alert_type, alert.severity,
              alert.message, alert.timestamp, alert.resolved))
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert_id
   
    def get_all_alerts(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT al.*, a.number as apartment_number
            FROM alerts al
            LEFT JOIN apartments a ON al.apartment_id = a.id
            ORDER BY al.timestamp DESC
        """)
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return alerts
   
    def get_all_alerts_with_buildings(self) -> List[Dict]:
        """Отримання всіх аварій з інформацією про будинки"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT al.*, a.number as apartment_number, b.address as building_address
            FROM alerts al
            LEFT JOIN apartments a ON al.apartment_id = a.id
            LEFT JOIN buildings b ON a.building_id = b.id
            ORDER BY al.timestamp DESC
        """)
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return alerts
   
    def get_active_alerts(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT al.*, a.number as apartment_number
            FROM alerts al
            LEFT JOIN apartments a ON al.apartment_id = a.id
            WHERE al.resolved = 0
            ORDER BY al.timestamp DESC
        """)
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return alerts




class AnalyticsEngine:
    """Модуль аналітики та прогнозування"""
   
    def __init__(self, db: DatabaseManager):
        self.db = db
   
    def get_system_statistics(self) -> Dict:
        """Отримання загальної статистики системи"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
       
        # Загальна кількість квартир
        cursor.execute("SELECT COUNT(*) as count FROM apartments")
        total_apartments = cursor.fetchone()['count']
       
        # Активні лічильники
        cursor.execute("SELECT COUNT(*) as count FROM meters WHERE status='Active'")
        active_meters = cursor.fetchone()['count']
       
        # Активні аварії
        cursor.execute("SELECT COUNT(*) as count FROM alerts WHERE resolved=0")
        active_alerts = cursor.fetchone()['count']
       
        # Середнє споживання
        cursor.execute("""
            SELECT AVG(power) as avg_power
            FROM sensor_data
            WHERE timestamp > datetime('now', '-1 hour')
        """)
        result = cursor.fetchone()
        avg_power = result['avg_power'] if result['avg_power'] else 0
       
        conn.close()
       
        return {
            'total_apartments': total_apartments,
            'active_meters': active_meters,
            'active_alerts': active_alerts,
            'avg_power': avg_power
        }
   
    def generate_sensor_data(self, meter_id: int) -> SensorData:
        """Генерація реалістичних даних сенсора"""
        # Базові значення з невеликими випадковими відхиленнями
        base_voltage = 230  # В
        base_current = random.uniform(2.0, 8.0)  # А
        base_frequency = 50  # Гц
        base_pf = 0.95
       
        # Додаємо випадкові відхилення
        voltage = base_voltage + random.gauss(0, 5)
        current = base_current + random.gauss(0, 0.5)
        frequency = base_frequency + random.gauss(0, 0.1)
        power_factor = base_pf + random.gauss(0, 0.02)
       
        # Розрахунок потужності
        power = (voltage * current * power_factor) / 1000
       
        # Випадково імітуємо аномалії (5% ймовірність)
        if random.random() < 0.05:
            anomaly_type = random.choice(['voltage_drop', 'overload', 'phase_loss'])
            if anomaly_type == 'voltage_drop':
                voltage = random.uniform(180, 200)
            elif anomaly_type == 'overload':
                current = random.uniform(15, 20)
                power = (voltage * current * power_factor) / 1000
            elif anomaly_type == 'phase_loss':
                voltage = random.uniform(150, 180)
       
        energy_consumed = power * 0.001  # Приблизне споживання за цикл
       
        return SensorData(
            meter_id=meter_id,
            voltage=round(voltage, 2),
            current=round(current, 2),
            power=round(power, 2),
            frequency=round(frequency, 2),
            power_factor=round(power_factor, 3),
            energy_consumed=round(energy_consumed, 4)
        )
   
    def check_for_anomalies(self, data: SensorData) -> Optional[Alert]:
        """Перевірка даних на аномалії"""
        # Перевірка перевантаження
        if data.detect_overload(max_power=10.0):
            return Alert(
                alert_type="Overload",
                severity="High",
                message=f"Перевантаження лінії: {data.power:.2f} кВт перевищує ліміт 10 кВт"
            )
       
        # Перевірка падіння напруги
        if data.detect_voltage_drop():
            return Alert(
                alert_type="VoltageDrop",
                severity="Medium",
                message=f"Падіння напруги: {data.voltage:.1f} В нижче норми"
            )
       
        # Перевірка втрати фази
        if data.detect_phase_loss():
            return Alert(
                alert_type="PhaseLoss",
                severity="Critical",
                message=f"Можлива втрата фази: напруга {data.voltage:.1f} В критично низька"
            )
       
        # Перевірка частоти
        if not data.is_frequency_normal():
            return Alert(
                alert_type="FrequencyAnomaly",
                severity="Low",
                message=f"Відхилення частоти: {data.frequency:.2f} Гц"
            )
       
        return None
   
    def calculate_monthly_consumption(self, apartment_id: int, month: int, year: int) -> Dict:
        """Розрахунок місячного споживання"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
       
        cursor.execute("""
            SELECT
                SUM(sd.energy_consumed) as total_energy,
                AVG(sd.power) as avg_power,
                MAX(sd.power) as peak_power,
                COUNT(*) as measurements
            FROM sensor_data sd
            JOIN meters m ON sd.meter_id = m.id
            WHERE m.apartment_id = ?
                AND strftime('%m', sd.timestamp) = ?
                AND strftime('%Y', sd.timestamp) = ?
        """, (apartment_id, f"{month:02d}", str(year)))
       
        result = dict(cursor.fetchone())
        conn.close()
       
        # Розрахунок вартості (приклад: 1.68 грн за кВт·год)
        tariff = 1.68
        total_energy = result['total_energy'] if result['total_energy'] else 0
        total_cost = total_energy * tariff
       
        return {
            'total_energy': round(total_energy, 2),
            'avg_power': round(result['avg_power'], 2) if result['avg_power'] else 0,
            'peak_power': round(result['peak_power'], 2) if result['peak_power'] else 0,
            'total_cost': round(total_cost, 2),
            'measurements': result['measurements']
        }
   
    def predict_consumption(self, apartment_id: int, days_ahead: int = 30) -> float:
        """Прогнозування споживання (проста лінійна модель)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
       
        # Отримуємо дані за останні 30 днів
        cursor.execute("""
            SELECT AVG(sd.power) as avg_power
            FROM sensor_data sd
            JOIN meters m ON sd.meter_id = m.id
            WHERE m.apartment_id = ?
                AND sd.timestamp > datetime('now', '-30 days')
        """, (apartment_id,))
       
        result = cursor.fetchone()
        conn.close()
       
        avg_power = result['avg_power'] if result['avg_power'] else 0
       
        # Прогноз: середня потужність * години * дні
        predicted_kwh = avg_power * 24 * days_ahead
       
        return round(predicted_kwh, 2)




class NotificationService:
    """Сервіс сповіщень"""
   
    def send_notification(self, alert: Alert):
        """Відправка сповіщення"""
        # В реальній системі тут був би код для відправки email/SMS/push
        print(f"[{alert.timestamp}] {alert.severity}: {alert.message}")
       
        # Логування
        self.log_notification(alert)
   
    def log_notification(self, alert: Alert):
        """Логування сповіщення"""
        with open("notifications.log", "a", encoding="utf-8") as f:
            f.write(f"{alert.timestamp} | {alert.alert_type} | {alert.severity} | {alert.message}\n")
   
    def send_batch_notifications(self, alerts: List[Alert]):
        """Масова відправка сповіщень"""
        for alert in alerts:
            self.send_notification(alert)




def calculate_power_loss(distance: float, current: float, cable_resistance: float = 0.02) -> float:
    """
    Розрахунок втрат потужності в кабелі
    P_loss = I² * R * L
   
    Args:
        distance: відстань в метрах
        current: струм в амперах
        cable_resistance: опір кабелю (Ом/м)
    """
    power_loss = (current ** 2) * cable_resistance * distance
    return round(power_loss, 4)




def calculate_voltage_drop(distance: float, current: float, cable_resistance: float = 0.02) -> float:
    """
    Розрахунок падіння напруги
    ΔU = I * R * L
    """
    voltage_drop = current * cable_resistance * distance
    return round(voltage_drop, 2)




def calculate_cos_phi(active_power: float, apparent_power: float) -> float:
    """
    Розрахунок коефіцієнта потужності
    cos(φ) = P / S
    """
    if apparent_power == 0:
        return 0
    cos_phi = active_power / apparent_power
    return round(min(1.0, max(0.0, cos_phi)), 3)




def calculate_three_phase_power(voltages: List[float], currents: List[float],
                                power_factors: List[float]) -> float:
    """
    Розрахунок потужності трифазної системи
    P = √3 * U * I * cos(φ)
    """
    if len(voltages) != 3 or len(currents) != 3 or len(power_factors) != 3:
        return 0
   
    # Середні значення
    avg_voltage = sum(voltages) / 3
    avg_current = sum(currents) / 3
    avg_pf = sum(power_factors) / 3
   
    power = math.sqrt(3) * avg_voltage * avg_current * avg_pf / 1000
    return round(power, 2)