import subprocess
import json
import time
import platform 
import requests
import os


from urllib.request import urlopen
import re as r
import cpuinfo

import socket,re,uuid,psutil,logging,getpass

json_config = None
config_path = __file__.replace("getPCInfo.py","config.json")

def autostart():
    service_name = os.path.basename(__file__).replace(".py", "")
    service_path = f"/etc/systemd/system/{service_name}.service"
    

    print(__file__)

    if not os.path.exists(service_path):
    # Создание файла сервиса
        print("Not exists")
        with open(service_path, "w") as f:
            f.write(f'''[Unit]
                Description=Start {service_name}

                [Service]
                ExecStart=/bin/python3 {__file__}
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
    return platform.version().split()[0]

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
        if(float(info['space']) > 1):
            result.append(info)
    
    return result

def getFullInformation():
    arm = getARMInfo()
    global json_config 
    result = {
        "Uptime" : f"{round(time.time() - start_time, 1)}",
        "Access_Token": json_config["token"],
        "Serial_Number" : get_serial_number(),
        "Manufacturer": arm["Manufacturer"],
        "ARM_Name": arm["ARM_Name"],
        "ARM_Type": arm["ARM_Type"],
        "OS_Type": getOS(),
        "OS_Name": getOSType(),
        "Host_Name": getHostname(),
        "User_Name": getUsername(),
        "Local_IP": getLocalIP(), 
        "Global_IP": getGlobalIP(),
        "MAC_Address": getMAC(),
        "Agent_Version": json_config["version"],
        "CPU_Name": getCPUName(),
        "RAM_Space": getRAMSpace(),
        "Applications": get_package_list(),
        "Local_Network":[],
        "Disks":getDisks()
    }
    return json.dumps(result)


def primaryPOSTRequest():
    url = 'http://81.200.152.218:3000/api/Devices/primary'
    myobj = getFullInformation()

    #use the 'headers' parameter to set the HTTP headers:
    x = requests.post(url, data = myobj, headers = {"Content-Type": "application/json", "User-Agent" : "PostmanRuntime/7.32.3"})

    return json.loads(x.text)["message"] == "OK"

def cicleRequest():
    global json_config  
    result = {
        "Uptime" : f"{round(time.time() - start_time, 1)}",
        "Access_Token": json_config["token"],
        "Applications": get_package_list(),
        "Disks":getDisks(),
        "Error_Messages":[]
    }

    url = 'http://81.200.152.218:3000/api/Devices/repeated'

    #use the 'headers' parameter to set the HTTP headers:
    x = requests.post(url, data = json.dumps(result), headers = {"Content-Type": "application/json", "User-Agent" : "PostmanRuntime/7.32.3"})

    return json.loads(x.text)["message"] == "OK"

def updateToken(token):
    global json_config
    json_config["token"] = token
    with open(config_path, "w") as config_file:
        json.dump(json_config, config_file)

def checkToken(token):
    url = "http://81.200.152.218:3000/api/Devices/registration"
    result = {
        "token": token
    }
    x = requests.post(url, data = json.dumps(result), headers = {"Content-Type": "application/json", "User-Agent" : "PostmanRuntime/7.32.3"})
    if x.status_code == 200:
        return True
    return False

def authorize():
    if not os.path.exists(config_path):
        config = open(config_path, "w")
        config.write("""
    {
        "version":null,
        "token": null,
        "inventory_num": null
    }
                     """)
        config.close()


    config = open(config_path)    
    global json_config
    json_config = json.load(config)
    print("done")
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
    interval = 1
    while True:
        time.sleep(interval)
        if not cicleRequest():
            interval = 300000
        else:
            interval = 1800000

main()