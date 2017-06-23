import zeep
"""Performs xyz"""

def test():
    """Entry point for the application script"""
    return("Call your main application code here")    
    

def test_client(building_info):
    try:
        client = zeep.Client(wsdl ='https://sandbox.hesapi.labworks.org/st_api/wsdl')
        output= client.service.retrieve_inputs(building_info)
        
        return output
     
    except Exception as e:
        print(e.message)
        raise
