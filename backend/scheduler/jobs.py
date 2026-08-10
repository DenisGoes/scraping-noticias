from backend.services.clean_db import clean_dados
from apscheduler.schedulers.background import BlockingScheduler
import pytz


tz = pytz.timezone('America/Sao_Paulo')

scheduler = BlockingScheduler(timezone=tz)

def processa_clean():
    clean_dados()
    print("Limpeza do banco executada.")


job = scheduler.add_job(
    func=processa_clean,
    trigger='cron',
    hour=5,
    minute=0
)


print("Scheduler iniciado. Aguardando jobs...")
scheduler.start()
