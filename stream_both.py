import sys
import time
import paramiko

sys.stdout.reconfigure(encoding="utf-8")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("192.168.0.183", username="ariyan", password="2009Ariyan@")

PYTHON = "/home/ariyan/.venvs/ai-trash-sorter/bin/python"
BASE = "/home/ariyan/ai-trash-sorter-test"

stream_both_code = """
import time
from sensors.ultrasonic import LgpioUltrasonicSensor

u1 = LgpioUltrasonicSensor(trigger_gpio=4, echo_gpio=5, timeout_seconds=0.04)
u3 = LgpioUltrasonicSensor(trigger_gpio=27, echo_gpio=13, timeout_seconds=0.04)
u1.start()
u3.start()

print("Sample | U1 (GPIO4/5)        | U3 (GPIO27/13)")
print("-------------------------------------------------")
for i in range(10):
    d1 = u1.read_distance_cm()
    time.sleep(0.02)
    d3 = u3.read_distance_cm()
    
    d1_s = f"{d1:>5.1f} cm" if d1 is not None else "  CLEAR"
    d3_s = f"{d3:>5.1f} cm" if d3 is not None else "  CLEAR"
    print(f" {i+1:02d}    | {d1_s:<18} | {d3_s:<18}")
    time.sleep(0.2)

u1.close()
u3.close()
"""

stdin, stdout, stderr = client.exec_command(f"PYTHONPATH={BASE}/app {PYTHON} -c '{stream_both_code}'")
print(stdout.read().decode("utf-8", errors="replace"))

client.close()
