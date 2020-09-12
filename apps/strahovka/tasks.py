"""
To use celery tasks:
1a) pip install -U "celery[redis]"
    pip install gevent
1b) Download Redis for Windows
2) In settings.py: 
   USE_CELERY = True
   CELERY_BROKER = "redis://localhost:6379"
3) Start redis-server.exe
4) Start "celery -A apps.strahovka.tasks beat -l INFO --max-interval=360000"
5) Start "celery -A apps.strahovka.tasks worker -l info -f apps/strahovka/celerylog.txt -P gevent" for each worker

"""

from celery import Celery
from .common import *
from celery.utils.log import get_task_logger

from .classes import DatabaseAccess,Updates,DataModify
import datetime
scheduler = Celery('apps.strahovka.tasks', broker='redis://localhost:6379')
logging = get_task_logger(__name__)

@scheduler.task()
def my_task():
    logging.info('Apptask started')
    db._adapter.reconnect()
    db_obj = DatabaseAccess()
    obj = Updates()
    modify_obj = DataModify()
    data = db_obj.get_update_data()
    now = datetime.datetime.now()
    if (now - data).days > 7:
        tuple_obj = obj.parser()
        rows = db(db.company.update_date == data).select(orderby=db.company.id)
        modify_obj.modify_company(tuple_obj[0])
        modify_obj.modify_license(tuple_obj[1])
        obj.compare(rows, tuple_obj[0])
        for i in range(len(tuple_obj[0])):
            str_company1=''
            str_company2=''
            for j,k in zip(tuple_obj[0][i].keys(),tuple_obj[0][i].values()):
                 str_company2+=str(j)+","
                 str_company1 += "'" + str(k) + "',"
            str_company1 = str_company1[0:len(str_company1) - 1]
            str_company2 = str_company2[0:len(str_company2) - 1]
            sql = "INSERT INTO company (%s) VALUES (%s)" % (str_company2, str_company1)
            db.executesql(sql)

        for i in range(len(tuple_obj[1])):
            str_license1=''
            str_license2=''
            for j,k in zip(tuple_obj[1][i].keys(),tuple_obj[1][i].values()):
                 str_license2+=str(j)+","
                 str_license1 += "'" + str(k) + "',"
            str_license1 = str_license1[0:len(str_license1) - 1]
            str_license2 = str_license2[0:len(str_license2) - 1]
            sql = "INSERT INTO license (%s) VALUES (%s)" % (str_license2, str_license1)
            db.executesql(sql)

        db.commit()


scheduler.conf.beat_schedule = {
    'my_first_task': {
        'task': 'apps.strahovka.tasks.my_task',
        'schedule': 360.0,
        },
    }
