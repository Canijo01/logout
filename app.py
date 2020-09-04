import configparser
import datetime
import json
import os
import time
from funciones import *

### Inicio del programa
config = configparser.ConfigParser()
leer_parametros = config.read("config.ini")

### Acceso a la API
if "TOKEN" in os.environ:
    token = os.environ['TOKEN']
    # print ("Token:%s"%token)

### Convierte todas las tuples de cada sección de config.ini en variables
### la prioridad es primero la variable de ambiente y despues la definida en config.ini
### Las variables que se utilizan son:
###URL : dominio donde esta el appliance ej. https://awingu.edgecapital.tech/
### domain: tenant que se est utilizando ej. EDGEOS
###n VERIFY para verificar si la conexion es segura. false si hay problema con el certificado
### Numero de dias hacia atras para solicitar la información de las sesiones
### DAYS : Numero de dias anteriores para cargar los registros ej. 5
### IDLE #Seconds without open RDP apps before Awingu assumes session is idle
### DELAY ## Seconds between interactions ej. 60
for secciones in config.sections():
    for variable in config.items(secciones):
        if variable[0] in os.environ:
            variable[1] = os.environ[variable[0]]
        exec("%s=\"%s\"" % (variable[0], variable[1]))
        print("%s=\"%s\"" % (variable[0], variable[1]))

### Headers para los restful API
headers = {
    'Accept': 'application/json',
    'Authorization': "Token %s" % (token)
}
api_get = url + "api/v2/domains/"
params = {
    'name': "%s" % (domain.upper())
}
### Obtener el uri del dominio
domain_get = requests.get(api_get, headers=headers, params=params)
# print(domain_get)
if domain_get.status_code == requests.codes.ok:
    print("Conexion inicial al API Ok", )
    # print(json.dumps(json.loads(domain_get.text),indent=4,sort_keys=True))
    domains_info = json.loads(domain_get.text)
    if domains_info["count"] > 0:
        for domains in domains_info["results"]:
            domain_uri = domains["uri"]
# loop principal
# solicita las sesiones que estan activas
# verifica si la sesion no sobrepasado el lapso en idle
# verifica si hay sesiones aplicativas  activas en ese caso no hay nada que hacer.
# Si no hay sesiones aplicativas activas verifica si ya transcurrio un lapso mayor
# a idle de las sesiones aplicativascerradas
# Si no hay sesiones aplicativas  y las sesiones aplicativas cerradas sobrepasan el lapso de idle entonces
# cierra la sesion de usuario
while True:
    now = datetime.datetime.now(datetime.timezone.utc)
    before = now - datetime.timedelta(days=int(days))

    # Obtener informacion de las sessiones activas
    sessions_list = usersessionslist(headers, url, domain, "", "", bool(verify))

    if sessions_list.status_code == requests.codes.ok:
        # print(json.dumps(json.loads(sessions_list.text),indent=4,sort_keys=True))
        sessions_text = json.loads(sessions_list.text)
        if sessions_text["count"] > 0:
            print("Sesiones de Usuario:%s" % sessions_text["count"])
            for session in sessions_text["results"]:
                app_sessions_list = getappsessions(
                    headers,
                    url,
                    domain_uri,
                    session["session_id"],
                    before,
                    now,
                    bool(verify))
                # print(json.dumps(json.loads(app_sessions_list.text), indent=4, sort_keys=True))
                app_sessions_text = json.loads(app_sessions_list.text)
                app_sessions = app_sessions_text
                idle_session = True
                enddate = session["start"]
                closed = (now - datetime.datetime.strptime(enddate + "Z", "%Y-%m-%dT%H:%M:%S.%f%z"))
                # print( "Now %s - enddate %s"%(now,enddate))
                print("\t Sesion: %s iniciada hace %s segundos" % (session["session_id"], closed.total_seconds()))
                if closed.total_seconds() <= int(idle):
                    idle_session = False
                    print("\t Sesion %s no sobrepaso el limite quedan: %s"
                          % (session["session_id"], int(idle) - closed.total_seconds())
                          )
                else:
                    for app in app_sessions:
                        if "appsession_end" not in app:
                            # If app session is still open then user session is not idle
                            idle_session = False
                        print("\t Sesión: %s tiene aplicaciones activas" % session["session_id"])
                        break
                    else:
                        # Check how many seconds ago the session was closed
                        enddate = datetime.datetime.strptime(app["appsession_end"], "%Y-%m-%dT%H:%M:%S.%f%z")
                        closed = (now - enddate).total_seconds()
                        # If app session was closed less then $idle seconds then it is still active
                        if (closed <= int(idle)):
                            idle_session = False
                            print("\t Sessión: %s tiene una session aplicativa cerrada hace %s segundos" % (
                                session["session_id"], closed))
                            break
            if idle_session == True:
                closesession(headers, url, session["session_id"])
                print("\t Cerrando sesion: %s" % (session["session_id"]))
    else:
        print("Error: %s en conexion al API. Fecha %s" % (sessions_list.status_code, now))
    time.sleep(int(delay))
