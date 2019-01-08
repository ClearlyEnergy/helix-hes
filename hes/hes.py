import zeep
import json
import datetime
"""Home Energy Score connect to HES API and retrieves score and output values"""

# select between sandbox and production
# URL is currently set to select the HES 2.0 beta
#CLIENT_URL = 'https://sandbeta.hesapi.labworks.org/st_api/wsdl' #sandbeta
#CLIENT_URL = 'https://hesapi.labworks.org/st_api/wsdl' #production
#CLIENT_URL = 'https://sandbox.hesapi.labworks.org/st_api/wsdl' #sandbox
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
        """Retrieve Home Energy Score API session token

        For example:
           get_session_token(client)
        """
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

    def query_hes(self, building_id):
        """ Returns primary Home Energy Score parameters for a building ID. Use authentication information provided when the class is instantiated
        Parameters:
            building_id: Home Energy Score building id

        Returns:
            dictionary with street address, city, state, zip code, year built, conditioned floor area and home energy score
            consumption, production are returned along with the relevant fuel and unit as a dictionary
        For example:
           client.query_hes(123456)
        """
        building_info = {'building_id': building_id,
                         'user_key': self.user_key,
                         'session_token': self.token}
        try:                         
            address = self.__make_api_call('retrieve_inputs', building_info)
        except zeep.exceptions.Fault as f:
            return {'status': 'error', 'message': f.message}

        location_map = {
            'address': 'Address Line 1',
            'city': 'City',
            'zip_code': 'Postal Code',
            'year_built': 'Year Built',
            'conditioned_floor_area': 'Conditioned Floor Area' 
        }
        result = {location_map[k]: address['about'][k] for k in location_map.keys()}
        result['Green Assessment Name'] = 'Home Energy Score'
        result['Green Assessment Property Source'] = 'Department of Energy'
        if address['systems']['generation']['solar_electric']['system_capacity'] > 0:
                result['Measurement Capacity Quantity'] = address['systems']['generation']['solar_electric']['system_capacity']
                result['Measurement Capacity Year'] = address['systems']['generation']['solar_electric']['year']
                result['Measurement Capacity Unit'] = 'kw'
                result['Measurement Capacity Status'] = 'ESTIMATE'
                result['Measurement Capacity Measurement Type'] = 'CAP'
                result['Measurement Capacity Measurement Subtype'] = 'PV'
        try:
            scores = self.__make_api_call('retrieve_label_results', building_info)
        except zeep.exceptions.Fault as f:
            return {'status': 'error', 'message': f.message}
        
        name_map = {
            'qualified_assessor_id': 'Qualified Assessor Id', 
            'base_score': 'Green Assessment Property Metric',
            'assessment_type': 'Green Assessment Property Status', 
            'hescore_version': 'Green Assessment Property Version', 
            'assessment_date': 'Green Assessment Property Date'}
        result.update({name_map[k]: scores[k] for k in name_map.keys()})
            # deal with source energy_total_base & source_energy_asset_base later
        for k in ('utility_electric', 'utility_natural_gas', 'utility_fuel_oil', 'utility_lpg', 'utility_cord_wood', 'utility_pellet_wood'):
            if scores[k] > 0:
                key = k.replace('utility_', '')
                result['Measurement Consumption Quantity'] = scores[k]
                result['Measurement Consumption Unit'] = UNIT_DICT[k]
                result['Measurement Consumption Status'] = 'ESTIMATE'
                result['Measurement Consumption Measurement Type'] = 'CONS'
                result['Measurement Consumption Fuel'] = key
        if scores['utility_generated'] > 0:
            result['Measurement Production Quantity'] = scores['utility_generated']
            result['Measurement Production Unit'] = UNIT_DICT['utility_generated']            
            result['Measurement Production Status'] = 'ESTIMATE'
            result['Measurement Production Measurement Type'] = 'PROD'
            result['Measurement Production Measurement Subtype'] = 'PV'
                        
        building_label = building_info
        building_info.update({'is_final': 'false', 'is_polling': 'false'})
        try:
            label = self.__make_api_call('generate_label', building_label)
            result['Message'] = label['message']
            result['Green Assessment Property Url'] = label['file'][0]['url']
        except  zeep.exceptions.Fault as f:
            result['pdf'] = ''
        result['Building Id'] = building_id
        result['status'] = 'success'
        return result
        
    def query_by_partner(self, partner, start_date=None, end_date=None):
        """query_by_partner
        Parameters:
            partner: Home Energy Score partner id
            start_date: optional, retrieve only records created on or after start date, format 'yyyy-mm-dd'
            end_date: optional, retrieve only records created before end date, use only in conunction with start date

        Returns:
            list of ids
        For example:
           client.query_by_partner('Test')
        """
        if start_date is not None:
            date_range = start_date.strftime("%Y-%m-%d")+'_'
            if end_date is not None: 
                date_range = date_range+end_date.strftime("%Y-%m-%d")
            else:
                date_range = date_range+datetime.date.today().strftime("%Y-%m-%d") 
                
        page_number = 1
        building_list = []
        while True:
            partner_info = {'partner': partner,
                            'session_token': self.token,
                            'user_key': self.user_key,
                            'rows_per_page': 10,
                            'page_number': page_number,
                            'archive': 0,
                        }
                        
            if start_date is not None:
                partner_info['date_range'] = date_range
            
            try:
                buildings = self.__make_api_call('retrieve_buildings_by_partner', partner_info)
                if not buildings:
                    return buildling_list
                for build, b in enumerate(buildings):
                    if b['_value_1'][0]['assessment_type'] in ['initial', 'final', 'corrected']:
                        building_list += [b['_value_1'][0]['id']]
                if build+1 == partner_info['rows_per_page']:
                    page_number += 1
                else:
                    return {'status': 'success', 'building_ids': building_list}
            except zeep.exceptions.Fault as f:
                return {'status': 'error', 'message': f.message}
            except zeep.exceptions.TransportError as f:
                if f.message.startswith("Server returned HTTP status 500 (no content available)"):
                    return {'status': 'success', 'building_ids': building_list}
                else:
                    return {'status': 'error', 'message': f.message}
        return {'status': 'success', 'building_ids': building_list}

    def end_session(self):
        """Destroy the session token associated with this client. 

        For example:
           client.end_session()
        """
        params = {'session_token': self.token,
                  'user_key': self.user_key}
        self.__make_api_call('destroy_session_token', params)
        self.token = None
