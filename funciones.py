import json
import requests


##########################################################################
#    Funciones requeridas para obtener la info del appliance de Awingu
#    Desarrollado en python 3.7
#    Se utilizó de base un script en powershell provisto por awingu
##########################################################################

def usersessionslist(headers, URL, domain_name, TS_from, TS_to, verify):
    params = {
        'limit': "%s" % (""),
        'offset': "%s" % (""),
        'status': "%s" % ("ACTIVE"),  # ACTIVE DISCONNECTED or CLOSED
        'start': "%s" % (TS_from),
        'end': "%s" % (TS_to),
        'domain': "%s" % (""),
        'domain_name': "%s" % (domain_name)
    }
    api_get = 'api/v2/user-sessions/'
    api_list = requests.get(URL + api_get, headers=headers, params=params, verify=verify)  # verify=False
    return (api_list)


def closesession(headers, URL, session):
    data = {
        "status": "CLOSED"
    }
    api_get = 'api/v2/user-sessions/'
    api_list = requests.patch(URL + api_get + session + "/", headers=headers, data=data)
    return (api_list)


def getappsessions(headers, URL, domain_uri, session_id, TS_from, TS_to, verify):
    params = {
        "domain": "%s" % (domain_uri),
        "query_name": "application_sessions",
        "query_filter": "%s" % (session_id),
        "timestamp_from": "%s" % (TS_from),
        "timestamp_to": "%s" % (TS_to)
    }
    # print ("parametros %s"%(params))
    api_get = 'api/v2/indexer/'
    api_list = requests.post(URL + api_get, headers=headers, data=params, verify=verify)  # verify=False
    return (api_list)

def getdomainuri (headers, URL,domain):
    domain_uri = ""
    api_get =  "api/v2/domains/"
    params = {
        'name': "%s" % (domain.upper())
    }
    domain_get = requests.get(URL + api_get, headers=headers, params=params)
    # print(domain_get)
    if domain_get.status_code == requests.codes.ok:
        print("Conexion inicial al API Ok", )
        # print(json.dumps(json.loads(domain_get.text),indent=4,sort_keys=True))
        domains_info = json.loads(domain_get.text)
        if domains_info["count"] > 0:
            for domains in domains_info["results"]:
                domain_uri = domains["uri"]
    return domain_uri