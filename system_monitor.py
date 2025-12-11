import time
try:
    import psutil  # type: ignore
except Exception:
    psutil = None

def get_system_status():
    tm = time.localtime()
    hour = tm.tm_hour
    cpu = 0
    if psutil:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
        except Exception:
            cpu = 0
    # 占位：活跃应用名称无法跨平台可靠获取，这里简单返回
    return {
        "time": f"{hour}点",
        "hour": hour,
        "active_app": "桌宠",
        "cpu_high": cpu >= 75,
    }

def get_user_activity():
    # 占位：简单认为最近有按键
    return {
        "last_keypress": "刚刚",
    }
