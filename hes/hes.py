import zeep
#from zeep.cache import SqliteCache, InMemoryCache
from zeep.transports import Transport
import json
import datetime
import csv
import re
import urllib2

"""Home Energy Score connect to HES API and retrieves score and output values"""
    
# select between sandbox and production
# URL is currently set to select the HES 2.0 beta
#CLIENT_URL = 'https://sandbeta.hesapi.labworks.org/st_api/wsdl' #sandbeta
#CLIENT_URL = 'https://hesapi.labworks.org/st_api/wsdl' #production
#CLIENT_URL = 'https://sandbox.hesapi.labworks.org/st_api/wsdl' #sandbox
UNIT_DICT = {
    'cost': 'dollars',
    'system_capacity': 'kw',
    'utility_generated': 'kwh', 
    'utility_electric_base': 'kwh', 
    'utility_natural_gas_base':'therms', 
    'utility_fuel_oil_base': 'gallons', 
    'utility_lpg_base': 'gallons', 
    'utility_cord_wood_base': 'cords', 
    'utility_pellet_wood_base': 'pounds', 
    'source_energy_total_base': 'mmbtu'}
    
FUEL_DICT = {
    'lpg': 'Propane',
    'fueloil': 'Fuel Oil',
    'electric': 'Electric',
    'naturalgas': 'Natural Gas',
    'cordwood': 'Cord Wood',
    'pelletwood': 'Pellet Wood'
}


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
#        transport = Transport(cache=InMemoryCache())
#        self.client = zeep.Client(wsdl, transport=transport)
        self.client = zeep.Client(wsdl) #doesn't set global variable
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

    def query_inputs(self, building_id):
        building_info = {'building_id': building_id,
                         'user_key': self.user_key,
                         'session_token': self.token}
        inputs = self.__make_api_call('retrieve_inputs', building_info)
        return inputs

    def query_result(self, building_id):
        building_info = {'building_id': building_id,
                         'user_key': self.user_key,
                         'session_token': self.token}
        results = self.__make_api_call('retrieve_label_results', building_info)
        return results
        
    def query_partner_result(self, partner, start_date=None, end_date=None):  
        partner_info = {'partner': partner,
                        'session_token': self.token,
                        'user_key': self.user_key,
                        'is_async': 0
                    }
                    
        if start_date is not None:
            partner_info['start_date'] = start_date               
        if end_date is not None: 
            partner_info['end_date'] = end_date
            
        all_results = self.__make_api_call('export_partner_label_results', partner_info)
        results = []
        if all_results['status']:
            results = self.parse_file(all_results['url'], partner)
        return results
        

    def query_label(self, building_id):
        building_info = {'building_id': building_id,
                         'user_key': self.user_key,
                         'session_token': self.token}
        label = self.__make_api_call('generate_label', building_info)
        return label    
        
    def parse_file(self, url, partner):
        name_map = {
            'address': 'Address Line 1',
            'city': 'City', 
            'zip_code': 'Postal Code', 
            'year_built': 'Year Built',
            'state': 'State',
            'conditioned_floor_area': 'Conditioned Floor Area',
            'qualified_assessor_id': 'Qualified Assessor Id', 
            'base_score': 'Green Assessment Property Metric',
            'assessment_type': 'Green Assessment Property Status', 
#            'hescore_version': 'Green Assessment Property Version', 
            'assessment_date': 'Green Assessment Property Date',
            'assessment_type': 'Green Assessment Property Status',
            'label_url': 'Green Assessment Property Url',
            'building_id': 'Green Assessment Property Reference Id',
            'hvac.0.heating.fuel_primary': 'Heating Fuel',
            'domestic_hot_water.fuel_primary': 'Water Heater Fuel'}

        result = []
        existing_addresses = []
#        file_name = 'HES_export_20181101_20181201_05152019_5cdc41.csv'
#        with open(file_name, mode='r') as csv_file:
        csv_file = urllib2.urlopen(url)
        csv_reader = csv.DictReader(csv_file)
            
        for row in csv_reader:
            if row['assessment_type'] not in ['Initial', 'Final', 'Corrected']:
                continue
            if partner == 'CT':
                if row['address'].endswith(','):
                    address_parts = row['address'].split(',')
                    new_address = address_parts[-2] + ' ' + ''.join(address_parts[:-2])
                    row['address'] = new_address.rstrip()
                elif re.search(r'\d+$', row['address']):
                    m = re.search(r'\d+$', row['address'])
                    address_parts = row['address'].split(m.group(0))
                    new_address = m.group(0) + ' ' + address_parts[0]
                    row['address'] = new_address.rstrip()
            new_address = row['address']+row['zip_code']
            if new_address in existing_addresses:
                currind = existing_addresses.index(new_address)
                currbldg = result[currind]['Green Assessment Property Reference Id']
                if currbldg < row['building_id']: #keep last iteration
                    del result[currind]
                    del existing_addresses[currind]
                    existing_addresses.append(new_address)
                elif currbldg > row['building_id']:
                    continue
            else:
                existing_addresses.append(new_address)

            rowdat = {'Green Assessment Name': 'Home Energy Score', 'Green Assessment Property Source': 'Department of Energy'}
            rowdat.update({name_map[k]: row[k] for k in name_map.keys()})
            rowdat['Measurement Cost Quantity'] = row['base_cost']
            rowdat['Measurement Cost Unit'] = UNIT_DICT['cost'] 
            rowdat['Measurement Cost Status'] = 'ESTIMATE'
            rowdat['Measurement Cost Measurement Type'] = 'Cost'
            if row['solar_electric.system_capacity'] and float(row['solar_electric.system_capacity']) > 0:
                rowdat['Measurement Capacity Quantity'] = row['solar_electric.system_capacity']
                rowdat['Measurement Capacity Year'] = row['solar_electric.year']
                rowdat['Measurement Capacity Unit'] = UNIT_DICT['system_capacity'] 
                rowdat['Measurement Capacity Status'] = 'ESTIMATE'
                rowdat['Measurement Capacity Measurement Type'] = 'Capacity'
                rowdat['Measurement Capacity Measurement Subtype'] = 'PV'
            if row['solar_electric.system_capacity'] and float(row['utility_generated_base']) > 0:
                rowdat['Measurement Production Quantity'] = row['utility_generated_base']
                rowdat['Measurement Production Unit'] = UNIT_DICT['utility_generated'] 
                rowdat['Measurement Production Status'] = 'ESTIMATE'
                rowdat['Measurement Production Measurement Type'] = 'Production'
                rowdat['Measurement Production Measurement Subtype'] = 'PV'                    
            for k in ('utility_electric_base', 'utility_natural_gas_base', 'utility_fuel_oil_base', 'utility_lpg_base', 'utility_cord_wood_base', 'utility_pellet_wood_base'):
                if row[k] and float(row[k]) > 0:
                    key = k.replace('utility_', '').replace('base','').replace('_','')
                    key = FUEL_DICT[key].title()
                    rowdat['Measurement Consumption Quantity ' + key] = row[k]
                    rowdat['Measurement Consumption Unit ' + key] = UNIT_DICT[k]
                    rowdat['Measurement Consumption Status ' + key] = 'ESTIMATE'
                    rowdat['Measurement Consumption Measurement Type ' + key] = 'Consumption'
                    rowdat['Measurement Consumption Fuel ' + key] = key
                
            result.append(rowdat)
        return result
    
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
                         
        result = {}
        result['Green Assessment Name'] = 'Home Energy Score'
        result['Green Assessment Property Source'] = 'Department of Energy'

#        try:                         
#            address = self.__make_api_call('retrieve_inputs', building_info)
#            if address['systems']['generation']['solar_electric']['system_capacity'] > 0:
#                    result['Measurement Capacity Quantity'] = address['systems']['generation']['solar_electric']['system_capacity']
#                    result['Measurement Capacity Year'] = address['systems']['generation']['solar_electric']['year']
#                    result['Measurement Capacity Unit'] = 'kw'
#                    result['Measurement Capacity Status'] = 'ESTIMATE'
#                    result['Measurement Capacity Measurement Type'] = 'Capacity'
#                    result['Measurement Capacity Measurement Subtype'] = 'PV'
#        except zeep.exceptions.Fault as f:
#            print(f.message);
#            return {'status': 'error', 'message': f.message}

        try:
            scores = self.__make_api_call('retrieve_label_results', building_info)
        except zeep.exceptions.Fault as f:
            return {'status': 'error', 'message': f.message}
        
        name_map = {
            'address': 'Address Line 1',
            'city': 'City', 
            'zip_code': 'Postal Code', 
            'year_built': 'Year Built',
            'conditioned_floor_area': 'Conditioned Floor Area',
            'qualified_assessor_id': 'Qualified Assessor Id', 
            'base_score': 'Green Assessment Property Metric',
            'assessment_type': 'Green Assessment Property Status', 
            'hescore_version': 'Green Assessment Property Version', 
            'assessment_date': 'Green Assessment Property Date'}
        result.update({name_map[k]: scores[k] for k in name_map.keys()})
            # deal with source energy_total_base & source_energy_asset_base later
        for k in ('utility_electric', 'utility_natural_gas', 'utility_fuel_oil', 'utility_lpg', 'utility_cord_wood', 'utility_pellet_wood'):
            if scores[k] > 0:
                key = k.replace('utility_', '').replace('_',' ').title()
                result['Measurement Consumption Quantity'] = scores[k]
                result['Measurement Consumption Unit'] = UNIT_DICT[k]
                result['Measurement Consumption Status'] = 'ESTIMATE'
                result['Measurement Consumption Measurement Type'] = 'Consumption'
                result['Measurement Consumption Fuel'] = key
        if scores['utility_generated'] > 0:
            result['Measurement Production Quantity'] = scores['utility_generated']
            result['Measurement Production Unit'] = UNIT_DICT['utility_generated']            
            result['Measurement Production Status'] = 'ESTIMATE'
            result['Measurement Production Measurement Type'] = 'Production'
            result['Measurement Production Measurement Subtype'] = 'PV'
                        
        building_label = building_info
        building_info.update({'is_final': 'false', 'is_polling': 'false'})
        try:
            label = self.__make_api_call('generate_label', building_label)
            result['Message'] = label['message']
            result['Green Assessment Property Url'] = label['file'][0]['url']
        except  zeep.exceptions.Fault as f:
            result['pdf'] = ''
        result['Building ID'] = building_id
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
        page_number = 1
        building_list = []
        while True:
            partner_info = {'partner': partner,
                            'session_token': self.token,
                            'user_key': self.user_key,
                            'rows_per_page': 100,
                            'page_number': page_number,
                            'archive': 0,
                        }
                        
            if start_date is not None:
                partner_info['min_date'] = start_date               
            if end_date is not None: 
                partner_info['max_date'] = end_date
            
            try:
                buildings = self.__make_api_call('retrieve_buildings_by_partner', partner_info)
                if not buildings:
                    return {'status': 'error', 'message': 'No buildings found'}
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
