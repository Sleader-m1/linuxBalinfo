import subprocess
import json
import time
import platform 
import requests
import os


from urllib.request import urlopen
import re as r
import cpuinfo

import socket,re,uuid,psutil,getpass

json_config = None
base_url = "http://81.200.152.218:3000"
config_path = __file__.replace("getPCInfo.py","config.json")

def autostart():
    service_name = os.path.basename(__file__).replace(".py", "")
    service_path = f"/etc/systemd/system/{service_name}.service"
    

    if not os.path.exists(service_path):
    # Создание файла сервиса
        with open(service_path, "w") as f:
            f.write(f'''[Unit]
                Description=Start {service_name}

                [Service]
                ExecStart=/bin/python3 ../../../root/linuxBalinfo/getPCInfo.py
                Restart=always
                RestartSec=3

                [Install]
                WantedBy=multi-user.target
            ''')
            os.system("systemctl daemon-reload")
    
        # Включение автозапуска сервиса
        os.system(f"systemctl enable {service_name}.service")
    else:
        print("Exists")

# def getPCInfo():
#     command = "sudo lshw -short"
#     process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
#     output, error = process.communicate()
#     if error:
#         return "Error"

#     result = json.dumps({
#         "PC info": str(output).replace('\\n', "\n").replace('\\t', '\t')
#     })
#     file = open("output.txt", "w")

#     file.write(result)
#     file.close()

start_time = time.time()

def get_serial_number():
    try:
        output = subprocess.check_output(["sudo", "dmidecode", "-s", "system-serial-number"])
        serial_number = output.decode().strip()
        return serial_number
    except subprocess.CalledProcessError:
        return None

def getMAC():
    return ':'.join(re.findall('..', '%012x' % uuid.getnode()))

def getOS():
    return platform.system()

def getOSType():
    return platform.version()

def getHostname():
    return socket.gethostname()

def getUsername():
    return getpass.getuser()

def getGlobalIP():
    d = str(urlopen('http://checkip.dyndns.com/').read())
    return r.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(d).group(1)
 
def getLocalIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    result = s.getsockname()[0]
    s.close()
    return result


def get_package_list():
    command = "dpkg -l"

    try:
        output = subprocess.check_output(command, shell=True)
        package_list = output.decode("utf-8").strip().split("\n")[7:]
        parsed_packages = [{"name":package.split()[1], "version" : package.split()[2]} for package in package_list]
        return parsed_packages

    except subprocess.CalledProcessError:
        return None

def getRAMSpace():
    return str(psutil.virtual_memory().total)

def getCPUName():
    return cpuinfo.get_cpu_info()['brand_raw']


def getARMInfo():
    command = "sudo lshw"

    try:
        output = subprocess.check_output(command, shell=True).decode("utf-8").strip().split("\n")[1:4]
        parsed_packages = [information.split()[1] for information in output]
        armType = parsed_packages[0].lower()
        if(armType == 'ноутбук'):
            parsed_packages[0] = "Laptop"
        else:
            parsed_packages[0] = "Desktop"
        return {
            "ARM_Type": parsed_packages[0],
            "ARM_Name" : parsed_packages[1],
            "Manufacturer": parsed_packages[2]
        }
    except subprocess.CalledProcessError:
        return None




def convert_bytes(size):
    
    return round(size / 8589934592, 1)

def getDisks():
    partitions = psutil.disk_partitions()
    disk_info = {}
    for partition in partitions:
        disk_name = partition.device
        disk_usage = psutil.disk_usage(partition.mountpoint)
        disk_info[disk_name] = {
            'space': f"{convert_bytes(disk_usage.total)}",
            'free': f"{convert_bytes(disk_usage.free)}"
        }

    result = []

    for disk, info in disk_info.items():
        result.append(info)
    
    return result

def getFullInformation():
    arm = ''
    serial_number = ''
    osType = ''
    osName = ''
    hostName = ''
    userName = ''
    localIP = ''
    globalIP = ''
    macAddress = ''
    cpuName = ''
    ramSpace = ''
    applications = []
    disks = []
    global json_config 
    Error_messages = []
    
    try:
        arm = getARMInfo()
    except:
        Error_messages.append({"message": 'Error while collecting ARM info!'})

    try:
        serial_number = get_serial_number()
    except:
        Error_messages.append({"message": 'Error while collecting serisl number!'})

    try:
        osType = getOS()
    except:
        Error_messages.append({"message": 'Error while collecting OS type!'})

    try:
        osName = getOSType()
    except:
        Error_messages.append({"message": 'Error while collecting OS name!'})

    try:
        hostName = getHostname()
    except:
        Error_messages.append({"message": 'Error while collecting host name!'})

    try:
        userName = getUsername()
    except:
        Error_messages.append({"message": 'Error while collecting user name!'})

    try:
        localIP = getLocalIP()
    except:
        Error_messages.append({"message": 'Error while collecting local IP!'})

    try:
        globalIP = getGlobalIP()
    except:
        Error_messages.append({"message": 'Error while collecting global IP!'})

    try:
        macAddress = getMAC()
    except:
        Error_messages.append({"message": 'Error while collecting MAC address!'})

    try:
        cpuName = getCPUName()
    except:
        Error_messages.append({"message": 'Error while collecting CPU name!'})

    try:
        ramSpace = getRAMSpace()
    except:
        Error_messages.append({"message": 'Error while collecting RAM space!'})

    try:
        applications = get_package_list()
    except:
        Error_messages.append({"message": 'Error while collecting applications!'})

    try:
        disks = getDisks()
    except Exception as e:
        Error_messages.append({"message": f"Error while collecting disks! {e}"})

    
    print(disks)
    result = {
        "Uptime" : f"{int(time.time() - start_time)}",
        "Access_Token": json_config["token"],
        "Serial_Number" : serial_number,
        "Manufacturer": arm["Manufacturer"],
        "ARM_Name": arm["ARM_Name"],
        "ARM_Type": arm["ARM_Type"],
        "OS_Type": osType,
        "OS_Name": osName,
        "Host_Name": hostName,
        "User_Name": userName,
        "Local_IP": localIP, 
        "Global_IP": globalIP,
        "MAC_Address": macAddress,
        "Agent_Version": json_config["version"],
        "CPU_Name": cpuName,
        "RAM_Space": ramSpace,
        "Applications": applications,
        "Local_Network":[],
        "Disks":disks,
        "Error_Messages" : Error_messages
    }
    return json.dumps(result)


def primaryPOSTRequest():
    url = base_url+'/api/Devices/primary'
    myobj = getFullInformation()

    #use the 'headers' parameter to set the HTTP headers:
    x = requests.post(url, data = myobj, headers = {"Content-Type": "application/json", "User-Agent" : "PostmanRuntime/7.32.3"})

    return json.loads(x.text)["message"] == "OK"

def cicleRequest():
    global json_config  
    error_messages = []

    disks = []
    applications = []

    try:
        applications = get_package_list()
    except:
        error_messages.append({"message":'Error while collecting applications!'})

    try:
        disks = getDisks()
    except:
        error_messages.append({"message":'Error while collecting disks!'})

    result = {
        "Uptime" : f"{int(time.time() - start_time)}",
        "Access_Token": json_config["token"],
        "Applications": applications,
        "Disks":disks,
        "Error_Messages":error_messages
    }


    url = base_url+'/api/Devices/repeated'

    #use the 'headers' parameter to set the HTTP headers:
    x = requests.post(url, data = json.dumps(result), headers = {"Content-Type": "application/json", "User-Agent" : "PostmanRuntime/7.32.3"})

    return json.loads(x.text)["message"] == "OK"

def updateToken(token):
    global json_config
    json_config["token"] = token
    with open(config_path, "w") as config_file:
        json.dump(json_config, config_file)

def checkToken(token):
    url = base_url+"/api/Devices/registration"
    result = {
        "token": token
    }
    x = requests.post(url, data = json.dumps(result), headers = {"Content-Type": "application/json", "User-Agent" : "PostmanRuntime/7.32.3"})
    if x.status_code == 200:
        return True
    return False

def authorize():
    # if not os.path.exists(config_path):
    #     config = open(config_path, "w")
    #     config.write("""
    # {
    #     "version":null,
    #     "token": null,
    #     "inventory_num": null
    # }
    #                  """)
    #     config.close()


    config = open(config_path)    
    global json_config
    json_config = json.load(config)
    if json_config['token'] is None:
        print("Введите токен:")
        new_token = input()
        while(not checkToken(new_token)):
            print("Введен некорректный токен, попробуйте еще раз: ")
            new_token = input()
        updateToken(new_token)




def main():
    authorize()
    autostart()
    while not primaryPOSTRequest():
        time.sleep(180000)
    print('Primary is ok!')
    interval = 1
    while True:
        time.sleep(interval)
        if not cicleRequest():
            interval = 60*5
        else:
            interval = 5#60*30
            print('Cicle is ok!')

main()
