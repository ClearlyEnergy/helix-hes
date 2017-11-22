import zeep
import json
"""Home Energy Score connect to HES API and retrieves score and output values"""

# select between sandbox and production
# URL is currently set to select the HES 2.0 beta
CLIENT_URL = 'https://sandbeta.hesapi.labworks.org/st_api/wsdl'
UNIT_DICT = {
    'utility_electric': 'kwh', 
    'utility_generated': 'kwh', 
    'utility_natural_gas':'therms', 
    'utility_fuel_oil': 'gallons', 
    'utility_lpg': 'gallons', 
    'utility_cord_wood': 'cords', 
    'utility_pellet_wood': 'pounds', 
    'utility_generated': 'kwh', 
    'source_energy_total_base': 'mmbtu'}


# An instance of this class is used to access building records in the HES
# database from the context of a HES user. Once initialized, this class
# retrieves a session token from the HES api and uses this token for all
# subsequent requests. When a particular instance of HesHelix is no longer
# needed end_session should be called so that the session  token is destroyed
class HesHelix:
    def __init__(self, wsdl, user_name, password, user_key):
        self.user_key = user_key
        self.user_name = user_name
        self.password = password
        self.client = zeep.Client(wsdl)
        self.token = self.__get_session_token()

    def __get_session_token(self):
        params = {'user_key': self.user_key,
                  'user_name': self.user_name,
                  'password': self.password}
        return self.__make_api_call('get_session_token', params)

    def __make_api_call(self, operation, params):
        """Retrieve Home Energy Score results

        For example:
           make_api_call(client, operation, params)
        """
        output = getattr(self.client.service, operation)(params)
        return output

    # Call this method to retreive hes data for a building id using the
    # authenitcation information provided when the class was instantiated
    def query_hes(self, building_id):
        building_info = {'building_id': building_id,
                         'user_key': self.user_key,
                         'session_token': self.token}
        address = self.__make_api_call('retrieve_inputs', building_info)

        result = {k: address['about'][k] for k in ('address', 'city', 'state', 'zip_code', 'year_built', 'conditioned_floor_area')}
        if address['systems']['generation']['solar_electric']['system_capacity'] > 0:
                result.update({
                    'CAP_electric_pv': json.dumps({'quantity': address['systems']['generation']['solar_electric']['system_capacity'], 'unit': 'kw', 'year': address['systems']['generation']['solar_electric']['year'], 'status': 'ESTIMATE'})})

        scores = self.__make_api_call('retrieve_label_results', building_info)
        result.update({k: scores[k] for k in ('qualified_assessor_id', 'assessment_type', 'base_score', 'hescore_version', 'assessment_date')})
        # deal with source energy_total_base & source_energy_asset_base later
        for k in ('utility_electric', 'utility_natural_gas', 'utility_fuel_oil', 'utility_lpg', 'utility_cord_wood', 'utility_pellet_wood'):
            if scores[k] > 0:
                key = k.replace('utility_', 'CONS_')
                result.update({key: json.dumps({'quantity': scores[k], 'unit': UNIT_DICT[k], 'status': 'ESTIMATE'})})
        if scores['utility_generated'] > 0:
            result.update({'PROD_electric_pv': json.dumps({'quantity': scores['utility_generated'], 'unit': UNIT_DICT['utility_generated'], 'status': 'ESTIMATE'})})
                            
        building_label = building_info
        building_info.update({'is_final': 'false', 'is_polling': 'false'})
        label = self.__make_api_call('generate_label', building_label)
        result['message'] = label['message']
        result['pdf'] = label['file'][0]['url']
        return result
        
    def query_hes_method(self, method_name, building_id):
        building_info = {'building_id': building_id,
                         'user_key': self.user_key,
                         'session_token': self.token}
        scores = self.__make_api_call(method_name, building_info)
        result = {}
        for k in ('utility_electric', 'utility_natural_gas', 'utility_fuel_oil', 'utility_lpg', 'utility_cord_wood', 'utility_pellet_wood'):
            if scores[k] > 0:
                key = k.replace('utility_', 'consumption_')
                result.update({key: (scores[k], UNIT_DICT[k])})
        
        return result        

    # destroy the session token associated with this client. This method should
    # be called when you are done using the client.
    def end_session(self):
        params = {'session_token': self.token,
                  'user_key': self.user_key}
        self.__make_api_call('destroy_session_token', params)
        self.token = None
