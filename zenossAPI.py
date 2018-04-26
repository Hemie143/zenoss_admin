# Zenoss-4.x JSON API Example (python)
#
# To quickly explore, execute 'python -i api_example.py'
#
# >>> z = ZenossAPIExample()
# >>> events = z.get_events()
# etc.

import json
import urllib
import urllib2
import ssl

# TODO: One module per router ?

ROUTERS = {'MessagingRouter': 'messaging',
           'EventsRouter': 'evconsle',
           'ProcessRouter': 'process',
           'ServiceRouter': 'service',
           'DeviceRouter': 'device',
           'NetworkRouter': 'network',
           'TemplateRouter': 'template',
           'DetailNavRouter': 'detailnav',
           'ReportRouter': 'report',
           'MibRouter': 'mib',
           'ZenPackRouter': 'zenpack',
           'TriggersRouter': 'triggers',
           }

class ZenossAPI():
    def __init__(self, url, username, password, debug=False):
        """
        Initialize the API connection, log in, and store authentication cookie
        """
        self.url = url
        
        # Use the HTTPCookieProcessor as urllib2 does not save cookies by default
        self.urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor())

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ssl._https_verify_certificates(enable=False)
        
        ctx2 = ssl._create_unverified_context()
        
        self.urlOpener.add_handler(urllib2.HTTPSHandler(context=ctx))
        if debug: self.urlOpener.add_handler(urllib2.HTTPSHandler(debuglevel=1))
        self.reqCount = 1

        # Contruct POST params and submit login.
        loginParams = urllib.urlencode(dict(
                        __ac_name = username,
                        __ac_password = password,
                        submitted = 'true',
                        came_from = url + '/zport/dmd'))
        self.urlOpener.open(url + '/zport/acl_users/cookieAuthHelper/login',
                            loginParams)

    def _router_request(self, router, method, data=[]):
        if router not in ROUTERS:
            raise Exception('Router "' + router + '" not available.')

        # Contruct a standard URL request for API calls
        req = urllib2.Request(self.url + '/zport/dmd/' +
                              ROUTERS[router] + '_router')

        # NOTE: Content-type MUST be set to 'application/json' for these requests
        req.add_header('Content-type', 'application/json; charset=utf-8')

        # Convert the request parameters into JSON
        reqData = json.dumps([dict(
                    action=router,
                    method=method,
                    data=data,
                    type='rpc',
                    tid=self.reqCount)])

        # Increment the request count ('tid'). More important if sending multiple
        # calls in a single request
        self.reqCount += 1

        # Submit the request and convert the returned JSON to objects
        return json.loads(self.urlOpener.open(req, reqData).read())


    def get_devices(self, deviceClass='/zport/dmd/Devices'):
        return self._router_request('DeviceRouter', 'getDevices',
                                    data=[{'uid': deviceClass,
                                           'params': {} }])['result']

    def get_events(self, device=None, component=None, eventClass=None):
        data = dict(start=0, limit=100, dir='DESC', sort='severity')
        data['params'] = dict(severity=[5,4,3,2], eventState=[0,1])

        if device: data['params']['device'] = device
        if component: data['params']['component'] = component
        if eventClass: data['params']['eventClass'] = eventClass

        return self._router_request('EventsRouter', 'query', [data])['result']

    def add_device(self, deviceName, deviceClass, collector):
        data = dict(deviceName=deviceName, deviceClass=deviceClass, collector=collector, productionState=str(500), model=True )
        return self._router_request('DeviceRouter', 'addDevice', [data])

    def create_event_on_device(self, device, severity, summary):
        if severity not in ('Critical', 'Error', 'Warning', 'Info', 'Debug', 'Clear'):
            raise Exception('Severity "' + severity +'" is not valid.')

        data = dict(device=device, summary=summary, severity=severity,
                    component='', evclasskey='', evclass='')
        return self._router_request('EventsRouter', 'add_event', [data])

    def get_device_uids(self, uid):
        return self._router_request('DeviceRouter', 'getDeviceUids', data=[{'uid': uid}])

    def remodel(self, device_uid):
        return self._router_request('DeviceRouter', 'remodel', data=[{'deviceUid': device_uid}])
        
    def add_datasource(self, templateUid, name, type):
        '''
        templateUid (string) - Unique ID of the template to add data source to
        name (string) - ID of the new data source
        type (string) - Type of the new data source. From getDataSourceTypes()
        '''
        data = dict(templateUid = templateUid, name = name, type = type )
        return self._router_request('TemplateRouter', 'addDataSource', [data])

    def get_datasourcetypes(self, query=None):
        data = dict(query = query)
        return self._router_request('TemplateRouter', 'getDataSourceTypes', [data])

    def get_datasources(self, uid):
        '''
        id (string) - Unique ID of a template
        '''
        data = dict(uid = uid)
        return self._router_request('TemplateRouter', 'getDataSources', [data])

    def add_datapoint(self, dataSourceUid, name):
        '''
        Add a new data point to a data source.
        Parameters:
        dataSourceUid (string) - Unique ID of the data source to add data point to
        name (string) - ID of the new data point
        Returns: DirectResponseSuccess message
        '''
        data = dict(dataSourceUid=dataSourceUid, name=name)
        return self._router_request('TemplateRouter', 'addDataPoint', [data])

    def add_threshold(self, data):
        '''
        Add a threshold.
        Parameters:
        uid (string) - Unique identifier of template to add threshold to
        thresholdType (string) - Type of the new threshold. From getThresholdTypes()
        thresholdId (string) - ID of the new threshold
        dataPoints ([string]) - List of data points to select for this threshold
        Returns: DirectResponseSuccess
        '''
        return self._router_request('TemplateRouter', 'addThreshold', [data])
        
    def add_graph(self, templateUid, graphDefinitionId):
        '''
        Add a new graph definition to a template.
        Parameters:
        templateUid (string) - Unique ID of the template to add graph definition to
        graphDefinitionId (string) - ID of the new graph definition
        Returns: DirectResponseSuccess messageDecorators:@require('Manage DMD')
        '''
        data = dict(templateUid=templateUid, graphDefinitionId=graphDefinitionId)
        return self._router_request('TemplateRouter', 'addGraphDefinition', [data])

    def add_datapointtograph(self, dataPointUid, graphUid, includeThresholds=False):
        '''
        Add a data point to a graph.
        Parameters:
        dataPointUid (string) - Unique ID of the data point to add to graph
        graphUid (string) - Unique ID of the graph to add data point to
        includeThresholds (boolean) - (optional) True to include related thresholds (default: False)
        Returns: DirectResponseSuccess
        '''
        data = dict(dataPointUid=dataPointUid, graphUid=graphUid, includeThresholds=includeThresholds)
        return self._router_request('TemplateRouter', 'addDataPointToGraph', [data])

    def get_graphpoints(self, uid):
        '''
        Get a list of graph points for a graph definition.
        Parameters:
        uid (string) - Unique ID of a graph definition
        Returns: DirectResponseProperties: 
        data: ([dictionary]) List of objects representing graph points 
        '''
        data = dict(uid = uid)
        return self._router_request('TemplateRouter', 'getGraphPoints', [data])

    def del_graphpoints(self, uid):
        '''
        Delete a graph point.
        Parameters:
        uid (string) - Unique ID of the graph point to delete
        Returns: DirectResponseSuccess
        '''
        data = dict(uid=uid)
        return self._router_request('TemplateRouter', 'deleteGraphPoint', [data])

        
    def set_info(self, data):
        '''
        Set attributes on an object. This method accepts any keyword argument for the property that you wish to set. The only required property is "uid".
        Parameters:
        uid (string) - Unique identifier of an object
        Returns: DirectResponseProperties: data: (dictionary) The modified object 
        '''
        return self._router_request('TemplateRouter', 'setInfo', [data])
        
    def get_info(self, uid):
        '''
        Get the properties of an object.
        Parameters:
        uid (string) - Unique identifier of an object
        Returns: DirectResponse
        Properties data: (dictionary) Object properties 
        form: (dictionary) Object representing an ExtJS form for the object 
        '''
        data = dict(uid=uid)
        return self._router_request('TemplateRouter', 'getInfo', [data])

    def add_template(self, id, targetUid):
        '''
        id (string) - Unique ID of the template to add
        targetUid (string) - Unique ID of the device class to add template to
        '''
        data = dict(id = id, targetUid = targetUid)
        return self._router_request('TemplateRouter', 'addTemplate', [data])
    
    def get_templates(self, id):
        '''
        id (string) - not used
        '''
        data = dict(id = id)
        return self._router_request('TemplateRouter', 'getTemplates', [data])
        
    def get_deviceclasstemplates(self, id):
        '''
        id (string) - not used
        '''
        data = dict(id = id)
        return self._router_request('TemplateRouter', 'getDeviceClassTemplates', [data])
        
    def make_localTemplate(self, uid, templateName):
        '''
        makeLocalRRDTemplate(self, uid, templateName) 
        Parameters:
        uid (string) - Identifer of the obj we wish to make the template local for
        templateName (string) - identifier of the template
        Decorators:@require('Manage DMD')
        '''
        data = dict(uid = uid, templateName=templateName)
        return self._router_request('TemplateRouter', 'makeLocalRRDTemplate', [data])

    def get_eventsConfig(self):
        '''
        '''
        return self._router_request('EventsRouter', 'getConfig')
        
    def network_getTree(self):
        return self._router_request('NetworkRouter', 'getTree')

    def network_getInfo(self, uid):
        data = dict(uid = uid)
        return self._router_request('NetworkRouter', 'getInfo', [data])
        
    def network_addNode(self, newSubnet, contextUid):
        data = dict(newSubnet=newSubnet, contextUid=contextUid)
        return self._router_request('NetworkRouter', 'addNode', [data])
        
    def get_triggerList(self):
        return self._router_request('TriggersRouter', 'getTriggerList', None)
        
    def get_trigger(self, uuid):
        data = dict(uuid = uuid)
        return self._router_request('TriggersRouter', 'getTrigger', [data])
        
    def export_triggers(self, triggerIds=None, notificationIds=None):
        data = dict(triggerIds = triggerIds, notificationIds = notificationIds)
        return self._router_request('TriggersRouter', 'exportConfiguration', [data])

    def import_triggers(self, triggers=None, notifications=None):
        data = dict(triggers = triggers, notifications = notifications)
        return self._router_request('TriggersRouter', 'importConfiguration', [data])
