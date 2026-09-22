import time
import logging
import threading
import psutil

from core.context import Context

log = logging.getLogger(__name__)

def _monitoring_loop(ctx: Context, asr):
    """
    Background loop that monitors system resources and triggers proactive notifications.
    """
    last_ram_warning = 0.0
    last_cpu_warning = 0.0
    
    # Check every 10 seconds
    while True:
        try:
            # CPU check (blocks for 1 second to get a valid reading)
            cpu_percent = psutil.cpu_percent(interval=1)
            # Memory check
            mem = psutil.virtual_memory()
            
            now = time.monotonic()
            
            # If RAM > 90% and we haven't warned in the last 5 minutes (300s)
            if mem.percent > 90 and (now - last_ram_warning > 300):
                # Wait for user to finish speaking if they are talking
                while asr.is_user_speaking():
                    time.sleep(1)
                ctx.say(f"Sir, system memory is critically high at {int(mem.percent)} percent. Should I attempt to close some background processes?")
                last_ram_warning = time.monotonic()
                
            # If CPU > 95% and we haven't warned in the last 5 minutes
            elif cpu_percent > 95 and (now - last_cpu_warning > 300):
                while asr.is_user_speaking():
                    time.sleep(1)
                ctx.say(f"Sir, CPU usage has spiked to {int(cpu_percent)} percent.")
                last_cpu_warning = time.monotonic()
                
        except Exception as e:
            log.error(f"Error in proactive monitoring: {e}")
            
        time.sleep(9) # total loop is ~10s since cpu_percent takes 1s

def start_proactive_monitoring(ctx: Context, asr):
    """Starts the background thread for system monitoring."""
    t = threading.Thread(target=_monitoring_loop, args=(ctx, asr), daemon=True)
    t.start()
    log.info("Proactive system monitoring started.")
