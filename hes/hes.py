import zeep
"""Home Energy Score connect to HES API and retrieves score and output values"""

# select between sandbox and production
CLIENT_URL = 'https://sandbox.hesapi.labworks.org/st_api/wsdl'  

def hes_helix(building_info):
    client = connect_client()
    address = make_api_call(client, 'retrieve_inputs', building_info)
    result = {k: address['about'][k] for k in ('address','city','state','zip_code','year_built','conditioned_floor_area')}
#    scores = make_api_call(client, 'retrieve_extended_results', building_info)
    scores = make_api_call(client, 'retrieve_label_results', building_info)
    result.update({k: scores[k] for k in ('qualified_assessor_id','assessment_type','base_score','hescore_version','assessment_date')})
    building_label = building_info
    building_info.update({'is_final': 'false', 'is_polling': 'false'})
    label = make_api_call(client, 'generate_label', building_label)
    result['message'] = label['message']
    result['pdf'] = label['file'][0]['url']
    return result
    
def connect_client(wsdl = CLIENT_URL):
    """Connects to Home Energy Score API using sandbox or production API

    For example:
       connect_client()
    """
    client = zeep.Client(wsdl)
    return client
     
def make_api_call(client, operation, params):
    """Retrieve Home Energy Score results

    For example:
       make_api_call(client, operation, params)
    """
    output = getattr(client.service, operation)(params)
    return output

def test_client(building_info):
    """Sample building info: building_info={'user_key':'ce4cdc28710349a1bbb4b7a047b65837','building_id':'142543'} """
    client = zeep.Client(wsdl ='https://sandbox.hesapi.labworks.org/st_api/wsdl')
    output= client.service.retrieve_inputs(building_info)
    return output
