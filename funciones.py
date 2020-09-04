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
    api_list = requests.post(URL + api_get, headers=headers, data=params, verify=bool(verify))  # verify=False
    return (api_list)
