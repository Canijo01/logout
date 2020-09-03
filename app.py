import configparser
import datetime
import json
import os
import requests
import time

config = configparser.ConfigParser()
a = config.read("config.ini")

### Acceso a la API
if "TOKEN" in os.environ:
    token = os.environ['TOKEN']
    print ("Token:%s"%token)

### Appliance de Awingu al que conectarse
if "URL" in os.environ:
    URL = os.environ['URL']
    print("URL:OK" )
else:
   URL = config.get("ACCESS", "URL")
   print("URL:%s"%URL)

### dominio a utilizar
if "domain" in os.environ:
    domain = os.environ['domain']
    print("domain:OK" )
else:
    domain = config.get("ACCESS", "domain")
    print("URL:%s" %domain)

### Si se va verificar la comunicación al API de Awingu
if "VERIFY" in os.environ:
    VERIFY=bool(os.environ['VERIFY'])
    print("VERIFY:OK")
else:
    VERIFY = bool(config.get("ACCESS", "VERIFY"))
    print("URL:%s" % VERIFY)

### Numero de dias hacia atras para solicitar la información de las sesiones
if "DAYS" in os.environ:
    days = int(os.environ['DAYS'])
    print("DAYS:OK")
else:
    days = int(config.get("ACCESS", "DAYS"))
    print("DAYS:%s"%days)

# seconds without open RDP apps before Awingu assumes session is idle
if "IDLE" in os.environ:
    idle = int(os.environ['IDLE'])
    print("IDLE:OK")
else:
    idle = int(config.get("ACCESS", "IDLE"))
    print("idle:%s" % idle)

## Seconds between interactions
if "DELAY" in os.environ:
    delay = int(os.environ['DELAY'])
    print("DELAY:OK")
else:
    delay = int(config.get("ACCESS", "DELAY"))
    print("delay:%s" % delay)



def usersessionslist(headers,URL,domain_name,TS_from,TS_to):
    params = {
        'limit': "%s" % (""),
        'offset': "%s" % (""),
       'status': "%s" % ("ACTIVE"),  #ACTIVE DISCONNECTED or CLOSED
        'start': "%s" % (TS_from),
        'end': "%s" % (TS_to),
        'domain': "%s" % (""),
        'domain_name': "%s" % (domain_name)
    }
    api_get = 'api/v2/user-sessions/'
    api_list = requests.get(URL + api_get, headers=headers, params=params,verify=VERIFY)  # verify=False
    return (api_list)

def closesession(headers,URL,session):
    data = {
           "status" : "CLOSED"
           }
    api_get = 'api/v2/user-sessions/'
    api_list = requests.patch(URL + api_get+ session +"/", headers=headers,data=data)
    return (api_list)

def getappsessions(headers, URL, domain_uri, session_id,TS_from,TS_to):
    params={
        "domain" : "%s" %(domain_uri),
        "query_name": "application_sessions",
        "query_filter" : "%s" %(session_id),
        "timestamp_from" : "%s" %(TS_from),
        "timestamp_to" : "%s" %(TS_to)
        }
    #print ("parametros %s"%(params))
    api_get = 'api/v2/indexer/'
    api_list = requests.post(URL + api_get, headers=headers, data=params)  # verify=False
    return (api_list)

### Inicio del programa

### Headers para los restful API
headers = {
        'Accept': 'application/json',
        'Authorization': "Token %s"%(token)
}
api_get = URL + "api/v2/domains/"
params = {
    'name' : "%s"%(domain.upper())
}
### Obtener el uri del dominio
domain_get =  requests.get(api_get, headers=headers,params=params)
#print(domain_get)
if domain_get.status_code == requests.codes.ok:
    #print(json.dumps(json.loads(domain_get.text),indent=4,sort_keys=True))
    domains_info=json.loads(domain_get.text)
    if domains_info["count"] > 0:
        for domains in domains_info["results"]:
            domain_uri=domains["uri"]
#loop principal
while True:
    now = datetime.datetime.now(datetime.timezone.utc)
    before = now - datetime.timedelta(days=days)
    print (now,"-", before)
    #Obtener informacion de las sessiones abiertas
    sessions_list = usersessionslist(headers,URL, domain,"","")
    print(sessions_list.status_code)
    if sessions_list.status_code == requests.codes.ok:
        #print(json.dumps(json.loads(sessions_list.text),indent=4,sort_keys=True))
        sessions_text=json.loads(sessions_list.text)
        if sessions_text["count"] > 0:
            print ("Sesiones de Usuario:%s" %sessions_text["count"])
            for session in sessions_text["results"]:
                #
                #print (session)
                app_sessions_list = getappsessions(headers, URL,domain_uri, session["session_id"],before,now)
                #print(json.dumps(json.loads(app_sessions_list.text), indent=4, sort_keys=True))
                app_sessions_text = json.loads(app_sessions_list.text)
                app_sessions = app_sessions_text
                idle_session = True
                enddate = session["start"]
                closed =   (now - datetime.datetime.strptime(enddate+"Z","%Y-%m-%dT%H:%M:%S.%f%z"))
                #print( "Now %s - enddate %s"%(now,enddate))
                print ("\t Sesion: %s iniciada hace %s segundos"%(session["session_id"],closed.total_seconds()))
                if  closed.total_seconds() <= idle:
                    idle_session = False
                    print ( "\t Sesion %s no sobrepaso el limite quedan: %s"%(session["session_id"],idle - closed.total_seconds()))
                else:
                    for app in app_sessions:
                        if "appsession_end" not in app:
                        # If app session is still open then user session is not idle
                            idle_session = False
                            print ("\t Sesión %s tiene aplicaciones activas" % session["session_id"])
                            break
                        else:
                            # Check how many seconds ago the session was closed
                            #now = datetime.datetime.now(datetime.timezone.utc)
                            enddate = datetime.datetime.strptime(app["appsession_end"],"%Y-%m-%dT%H:%M:%S.%f%z")
                            #print( "now %s - enddate %s"%(now,enddate))
                            closed = (now - enddate).total_seconds()
                            print ("closed = %s"%(closed))
                            # If app session was closed less then $idle seconds then it is still active
                            if (closed <= idle):
                                idle_session = False
                                break
                                #print ("\t La sesion %s no hay sesiones activas quedan %s segundos"%(session["session_id"],idle-closed))

                #print ("\t Sesion: %s status:%s "%(session["session_id"],idle_session))
                if idle_session == True :
                    closesession(headers,URL,session["session_id"])
                    print ("\t Cerrando sesion: %s"%(session["session_id"]))
    time.sleep(delay)
