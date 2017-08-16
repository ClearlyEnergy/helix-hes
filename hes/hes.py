import zeep
"""Home Energy Score connect to HES API and retrieves score and output values"""

# select between sandbox and production
# URL is currently set to select the HES 2.0 beta
CLIENT_URL = 'https://sandbeta.hesapi.labworks.org/st_api/wsdl'


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

    def query_hes(self, building_id):
        building_info = {'building_id': building_id,
                         'user_key': self.user_key,
                         'session_token': self.token}
        address = self.__make_api_call('retrieve_inputs', building_info)
        result = {k: address['about'][k] for k in ('address', 'city', 'state', 'zip_code', 'year_built', 'conditioned_floor_area')}
        scores = self.__make_api_call('retrieve_label_results', building_info)
        result.update({k: scores[k] for k in ('qualified_assessor_id', 'assessment_type', 'base_score', 'hescore_version', 'assessment_date')})
        building_label = building_info
        building_info.update({'is_final': 'false', 'is_polling': 'false'})
        label = self.__make_api_call('generate_label', building_label)
        result['message'] = label['message']
        result['pdf'] = label['file'][0]['url']
        return result

    def end_session(self):
        params = {'session_token': self.token,
                  'user_key': self.user_key}
        self.__make_api_call('destroy_session_token', params)
