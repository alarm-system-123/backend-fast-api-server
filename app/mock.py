from app.mqtt import sensors_cache

MOCK_SYSTEM_STATES = {
    "00:70:07:24:26:D0": {  # Ваш основний тестовий хаб (Квартира)
        "gateway_status": "online",
        "mode": "disarmed",
        "device": "main_controller"
    }
}
MOCK_SENSORS = {
    "00:70:07:24:26:D0": [
        {
            "id": 1,
            "name": "Вхідні двері",
            "type": 1,        # 1 - Геркон
            "state": False,   # Зачинено
            "bat": 4.1,       # Майже повний заряд
            "online": True,
            "mac": "AC:EB:E6:4A:C7:40"
        },
        {
            "id": 2,
            "name": "Коридор (Рух)",
            "type": 0,        # 0 - Інфрачервоний
            "state": False,   # Немає руху
            "bat": 3.6,       # Середній заряд
            "online": True,
            "mac": "AC:EB:E6:4A:C7:41"
        }
    ]
}

def get_system_state_for_device(device_id: str) -> dict:
    """Отримує стан системи для конкретного хаба."""
    return MOCK_SYSTEM_STATES.get(device_id, {
        "gateway_status": "offline",
        "mode": "unknown",
        "device": "unknown"
    })

def get_sensors_for_device(device_id: str) -> list:
    """Отримує список РЕАЛЬНИХ датчиків для конкретного хаба з кешу."""

    # Якщо хаб уже надсилав дані, повертаємо їх
    if device_id in sensors_cache:
        return list(sensors_cache[device_id].values())

    # Якщо хаб ще нічого не надсилав (або вимкнений), повертаємо порожній список
    return []