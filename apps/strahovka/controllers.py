from py4web import action, request, Session,Field
from .models import db
from .common import *
from .classes import Updates, DatabaseAccess, DataModify
from py4web.utils.form import Form, FormStyleBulma
from pydal.validators import *

import smtplib
import pandas as pd
import os
import datetime
from py4web.core import wsgi


from py4web import redirect, URL

logger = logging.getLogger(__name__)

@authenticated()
def index():
    logger.info('Index page entered')
    # print(my_auth.get_user())
    user = my_auth.get_user()
    user_id = user['id']
    admin = db(db.site_user.auth_user == user_id).select().first().admin
    application = wsgi()
    print(application)
    try:
        rows = db(db.company).select()
    except:
        logger.warning('NO companies in database')
        rows = []
    # print(ll)
    # logging.error('Index failed')
    logger.info('Index page OK')
    return dict(rows=rows,admin=admin)

@authenticated.callback()
def accept_request(id):
    logger.info('Accept_request method started')
    confirm_request = db.request[id]
    logger.info('Accept request method completed successfully')
    confirm_request.update_record(confirm=True)

@authenticated.callback()
def update_company_user():
    logger.info('Update_company_user method started')
    db_obj = DatabaseAccess()
    logger.debug('Update_company_user class method is called')
    db_obj.update_company_user()
    logger.info('Update_company_user method completed successfully')

@authenticated.callback()
def accept_all_requests():
    logger.info('Accept_all_requests method started')
    rows = db(db.request).select()
    for row in rows:
        if row.confirm == False:
            row.update_record(confirm=True)
    logger.info('Accept_all_requests method completed successfully')



def check_requests():
    logger.info('Check_requests method started')
    flag=True
    rows = db(db.request).select()
    for row in rows:
        if row.confirm==False:
            flag=False
            break
    logger.info('Check_requests method completed successfully')
    return flag

@authenticated()
def admin_page():
    logger.info('Admin page entered')
    user = my_auth.get_user()
    user_id = user['id']
    admin = db(db.site_user.auth_user == user_id).select().first().admin
    rows = db(db.request).select()
    logger.info('Admin page OK')
    return dict(
        rows=rows,
        admin=admin,
        accept_request=accept_request,
        update_company_user=update_company_user,
        accept_all_requests=accept_all_requests,
        check_requests=check_requests)

@authenticated()
def license():
    logger.info('License page entered')
    user = my_auth.get_user()
    user_id = user['id']
    admin = db(db.site_user.auth_user == user_id).select().first().admin
    try:
        rows = db(db.company).select()
    except:
        logger.warning('NO companies for licenses in database')
        rows = []
    logger.info('License page OK')
    return dict(rows=rows,admin=admin)


def check_nonnegative_quantity(form):

    if form.vars['start']:
        try:
            datetime.datetime.strptime(form.vars['start'], '%d.%m.%Y')
        except ValueError:
            form.errors['start'] = T('Not correct date. Please enter date like this: 26.05.2001')

    if form.vars['end']:
        try:
            datetime.datetime.strptime(form.vars['end'], '%d.%m.%Y')
        except ValueError:
            form.errors['end'] = T('Not correct date. Please enter date like this: 26.05.2001')

    # if form.vars['days']:
    #     try:
    #         start = datetime.datetime.strptime(form.vars['start'], '%d.%m.%Y')
    #         end = datetime.datetime.strptime(form.vars['end'], '%d.%m.%Y')
    #         if int((end - start).days) != int(form.vars['days']):
    #             form.errors['days'] = T('Not correct days')
    #             print((end - start).days)
    #     except ValueError:
    #         form.errors['start'] = T('Not correct date')
    #         form.errors['end'] = T('Not correct date')


@authenticated()
def insurance():
    return dict()

@action("success", method="POST")
@action.uses("insurance.html", db)
def success():
    print(request.POST.get('none_days'))
    print('ok')
    return dict()

@action("access")
@action.uses(db)
def access():
    obj = DatabaseAccess()
    codes = obj.get_codes('0692')
    name = obj.get_full_name('20693867')
    adr = obj.get_address('20693867')
    di = obj.get_director('20693867')
    print(codes)
    print(name)
    print(adr)
    print(di)
    return 'OK'

@authenticated()
def add_company():
    logger.info('Add company page entered')
    # db(db.company.id>0).delete()
    # db(db.license.id>0).delete()
    user_id = my_auth.get_user()['id']
    admin = db(db.site_user.auth_user == user_id).select().first().admin
    user = db(db.site_user.auth_user == user_id).select().first()
    if not user:
        db['site_user'].insert(auth_user=user_id)
        logger.debug('Add site_user for auth_user')
    last_company = db(db.company).select().last()
    last_data = last_company.update_date
    rows = db(db.company.update_date == last_data).select()
    auth_user = db(db.auth_user.id == user_id).select().first()
    site_user = db(db.site_user.auth_user == user_id).select().first()
    db.site_user.auth_user.writable = False
    db.site_user.admin.writable = False
    form1 = Form(db.auth_user, auth_user, deletable=False, formstyle=FormStyleBulma)
    form2 = Form(db.site_user, site_user, deletable=False, formstyle=FormStyleBulma)
    logger.info('Add company page OK')
    return dict(rows=rows, auth_user=auth_user, site_user=site_user, form1=form1, form2=form2,admin=admin)


@action("update_database", method="GET")
@action.uses(db)
def update_database():
    db_obj = DatabaseAccess()
    obj = Updates()
    modify_obj = DataModify()
    try:
        data = db_obj.get_update_data()
        now = datetime.datetime.now()
        if (now - data).days > 7:
            print(1)
            tuple_obj = obj.parser()
            rows = db(db.company.update_date == data).select(orderby=db.company.id)
            modify_obj.modify_company(tuple_obj[0])
            modify_obj.modify_license(tuple_obj[1])
            obj.compare(rows, tuple_obj[0])
            date = datetime.datetime.now()
            print(tuple_obj[0])
            print(db_obj.upload_companies(tuple_obj[0]) + '1')
            print(db_obj.upload_licenses(tuple_obj[1]) + "1")
            # for i in range(len(tuple_obj[0])):
            #     request = "INSERT INTO company (id,IAN_FULL_NAME,FIN_TYPE,IM_NUMIDENT,IAN_RO_SERIA," \
            #               "IAN_RO_CODE,IAN_RO_DT,DIC_NAME,F_ADR,IA_PHONE_CODE,IA_PHONE,IA_EMAIL," \
            #               "IND_OBL,K_NAME,abbreviation,position,update_date,changes) VALUES ({},'{}','{}',{},'{}',{},'{}','{}'," \
            #               "'{}','{}','{}','{}','{}','{}','{}','{}','{}','{}');".format(tuple_obj[0][i]['id'],
            #                                                                            tuple_obj[0][i]['IAN_FULL_NAME'],
            #                                                                            tuple_obj[0][i]['FIN_TYPE'],
            #                                                                            tuple_obj[0][i]['IM_NUMIDENT'],
            #                                                                            tuple_obj[0][i]['IAN_RO_SERIA'],
            #                                                                            tuple_obj[0][i]['IAN_RO_CODE'],
            #                                                                            tuple_obj[0][i]['IAN_RO_DT'],
            #                                                                            tuple_obj[0][i]['DIC_NAME'],
            #                                                                            tuple_obj[0][i]['F_ADR'],
            #                                                                            tuple_obj[0][i]['IA_PHONE_CODE'],
            #                                                                            tuple_obj[0][i]['IA_PHONE'],
            #                                                                            tuple_obj[0][i]['IA_EMAIL'],
            #                                                                            tuple_obj[0][i]['IND_OBL'],
            #                                                                            tuple_obj[0][i]['K_NAME'],
            #                                                                            tuple_obj[0][i]['abbreviation'],
            #                                                                            tuple_obj[0][i]['position'],
            #                                                                            str(now),
            #                                                                            tuple_obj[0][i]['changes'])
            #     db.executesql(request)


    except AttributeError:
        print(2)
        tuple_obj = obj.parser()
        modify_obj.modify_company(tuple_obj[0])
        modify_obj.modify_license(tuple_obj[1])
        print(db_obj.upload_companies(tuple_obj[0])+'2')
        print(db_obj.upload_licenses(tuple_obj[1])+"2")
        print(tuple_obj[0])
    return 'Hello'


@action("static/add_company", method="POST")
@action.uses("add_company.html", db)
def add():
    logger.info('Add method started')
    db_obj = DatabaseAccess()
    last_company = db(db.company).select().last()
    last_data = last_company.update_date
    rows = db(db.company.update_date == last_data).select()
    choice_id = request.POST.get('choice_id')
    action = request.POST.get('action')
    current_company = db(db.company.id == choice_id).select().last()
    user_id = my_auth.get_user()['id']
    admin = db(db.site_user.auth_user == user_id).select().first().admin
    site_user = db_obj.get_user(user_id)
    auth_user = db_obj.get_auth_user(user_id)
    fromaddr = 'strahovka.work2020@gmail.com'
    toaddr = auth_user.email
    # toaddr = current_company.email

    username = 'strahovka.work2020@gmail.com'
    password = 'cdnblpUYBvdlH8'
    server = smtplib.SMTP('smtp.gmail.com:587')
    if action == 'add':
        db_obj.insert_request(site_user, choice_id, action)
        logger.debug('Action "add" is added to requests table')
        # server.starttls()
        # server.login(username, password)
        # msg1 = 'Потвердите что вашу компанию обслуживает ' + str(site_user.first_name)
        # msg2 = 'Confirm that you want to add this company' + str(current_company.IAN_FULL_NAME) + str(
        #     current_company.IM_NUMIDENT)
        # server.sendmail(fromaddr, toaddr, msg2.encode("utf8"))
        # server.quit()
    elif action == 'delete':
        db_obj.insert_request(site_user, choice_id, action)
        logger.debug('Action "delete" is added to requests table')
        # server.starttls()
        # msg3 = 'Confirm that you want to delete this company' + str(current_company.IAN_FULL_NAME) + str(
        #     current_company.IM_NUMIDENT)
        # server.login(username, password)
        # server.sendmail(fromaddr, toaddr, msg3.encode("utf8"))
        # server.quit()
    form1 = Form(db.auth_user, auth_user, deletable=False, formstyle=FormStyleBulma)
    form2 = Form(db.site_user, site_user, deletable=False, formstyle=FormStyleBulma)
    logger.info('Add method OK')
    return dict(rows=rows, auth_user=auth_user, site_user=site_user, session=session, form1=form1, form2=form2,admin=admin)


@action("company_users", method="GET")
@action.uses("company_users.html", db)
def add():
    rows = db(db.name).select()
    print(rows.fields)

    # date=datetime.datetime.now()
    for i in range(1234, 1851):
        db(db.company.id == i).delete()
    for i in range(14543, 15160):
        db(db.license.id == i).delete()
    for i in range(20,30):
        db(db.request.id == i).delete()
    # myDict={'id':18,'name':'Vll'}
    # qmarks = ', '.join('?' * len(myDict))
    # arr1=[]
    # qqq=''
    # qqq2=''
    # for i in myDict.keys():
    #     qqq2+=str(i)+","
    # for i in myDict.values():
    #     qqq+="'"+str(i)+"',"
    # qqq = qqq[0:len(qqq) - 1]
    # qqq2 = qqq2[0:len(qqq2) - 1]
    # qry = "Insert Into name (%s) Values (%s)" % (qqq2, qqq)
    # db.executesql(qry)
    return dict(rows=rows)


@authenticated()
def upload():
    logger.info('Upload to database as admin started (upload method)')
    user = my_auth.get_user()
    user_id = user['id']
    admin = db(db.site_user.auth_user == user_id).select().first().admin
    logger.info('Upload to database as admin OK (upload method)')
    return dict(message="", new_data_dict={}, session=session,admin=admin)


@action("static/upload", method="POST")
@action.uses("confirm.html", db)
def upload_post():
    f = request.files["neededFile"]
    table_num = request.POST['table']
    quarter = request.POST['quarter']
    table = tables[table_num]

    f.save('apps/strahovka/xls_files/' + f'{f.filename}')
    message = 'Файл успешно загружен'
    # pandas and excel
    if table == 'payout':
        data_xls = pd.read_excel('apps/strahovka/xls_files/' + f'{f.filename}', index_col=None, skiprows=1, dtype=str)
        new_data_dict = data_xls.to_dict(orient='records')
        print(new_data_dict)
    elif table == 'type':
        data_xls = pd.read_excel('apps/strahovka/xls_files/' + f'{f.filename}', index_col=1, dtype=str)
        data_xls = data_xls.T
        print(data_xls)
        data_dict = data_xls.to_dict(orient='index')
        print(data_dict)

        new_data_dict = []
        for key, values_dict in data_dict.items():
            if key == 'Назва' or key == 'Всього:':
                continue
            new_dict = {}
            new_dict['Назва'] = key
            for key2, value2 in values_dict.items():
                for key1, value1 in names[table].items():
                    if key2 == value1:
                        new_dict[key2] = value2
            new_data_dict.append(new_dict)
        print(new_data_dict)
    else:
        data_xls = pd.read_excel('apps/strahovka/xls_files/' + f'{f.filename}')
    rows = db(db.company_user.user == globals().get('session').get('user').get('id')).select()
    message = 'Error'
    for row in rows:
        if str(row.company_id) == new_data_dict[0]['Номер компанії']:
            message = 'Thank you'
            break
    if message != 'Error':
        data = {'message': 'Файл успешно загружен', 'new_data_dict': new_data_dict, 'table': table,
                'filename': f.filename, 'quarter': quarter, 'session': session}
    else:
        data = {'message': 'Error', 'session': session}
    return data


@action("static/confirm", method="POST")
@action.uses("confirm_success.html", db)
def confirm_post():
    table = request.POST['tabl_name']
    file_name = request.POST['file_name']
    quarter = request.POST['quarter']
    print(file_name)
    if table == 'payout':
        data_xls = pd.read_excel('apps/strahovka/xls_files/' + f'{file_name}', index_col=None, skiprows=1, dtype=str)
        data_dict = data_xls.to_dict(orient='records')
        new_data_dict = []
        for i in range(len(data_dict)):
            new_dict = {}
            for key2, value2 in data_dict[i].items():
                for key1, value1 in names['payout'].items():
                    if key2 == value1 or key2 in value1:
                        new_dict[key1] = value2
            new_data_dict.append(new_dict)
        for i in range(len(new_data_dict)):
            db['payout'].insert(**new_data_dict[i])
        print(new_data_dict)
    elif table == 'type':
        data_xls = pd.read_excel('apps/strahovka/xls_files/' + f'{file_name}', index_col=1, dtype=str)
        data_xls = data_xls.T
        print(data_xls)
        data_dict = data_xls.to_dict(orient='index')
        print(data_dict)

        new_data_dict = []
        for key, values_dict in data_dict.items():
            if key == 'Назва' or key == 'Всього:':
                continue
            new_dict = {}
            new_dict['name'] = key
            for key2, value2 in values_dict.items():
                for key1, value1 in names['type'].items():
                    if key2 == value1:
                        new_dict[key1] = value2
            new_data_dict.append(new_dict)
        for i in range(len(new_data_dict)):
            db['type'].insert(**new_data_dict[i])
        print(new_data_dict)
    today_data = str(datetime.datetime.now())
    company_id = new_data_dict[0]['company_id']
    user_name = globals().get('session').get('user').get('id')
    db['download'].insert(name=table, data=today_data, quarter_num=quarter, user=user_name, company_id=company_id)
    os.remove('apps/strahovka/xls_files/' + f'{file_name}')
    data = {'message': 'Thank you', 'session': session}

    fromaddr = 'testvlada222@gmail.com'
    toaddr = db(db.auth_user.id == user_name).select().first().email
    msg = 'Hello'
    # Gmail Login

    username = 'testvlada222@gmail.com'
    password = 'pydal4weBB'

    # Sending the mail

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(username, password)
    server.sendmail(fromaddr, toaddr, msg)
    server.quit()
    return data


