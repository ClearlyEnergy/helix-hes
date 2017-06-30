import zeep
"""Home Energy Score connect to HES API and retrieves score and output values"""

# select between sandbox and production
CLIENT_URL = 'https://sandbox.hesapi.labworks.org/st_api/wsdl'  

def hes_helix(building_info):
    client = connect_client()
    address = make_api_call(client, 'retrieve_inputs', building_info)
    result = {k: address['about'][k] for k in ('address','city','state','zip_code','year_built','conditioned_floor_area')}
    scores = make_api_call(client, 'retrieve_extended_results', building_info)
    result['base_score'] = scores['base_score']
    
    return result

    
def connect_client(wsdl = CLIENT_URL):
    """Connects to Home Energy Score API using sandbox or production API

    For example:
       connect_client()
    """
    try:
        client = zeep.Client(wsdl)
        return client
     
    except Exception as e:
        print(e.message)
        raise    
    
def make_api_call(client, operation, params):
    try:
        output = getattr(client.service, operation)(params) 
        return output

    except Exception as e:
        print(e.message)
        raise

def test_client(building_info):
    try:
        client = zeep.Client(wsdl ='https://sandbox.hesapi.labworks.org/st_api/wsdl')
        output= client.service.retrieve_inputs(building_info)        
        return output
     
    except Exception as e:
        print(e.message)
        raise
