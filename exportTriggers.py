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
import re
import zenossAPI
import ConfigParser
import argparse
import sys

def main(args=None):
    import argparse
    parser = argparse.ArgumentParser(description='list Triggers')
    parser.add_argument('-s', dest='environ', action='store', default='test')
    options = parser.parse_args(args)


    zen_config = ConfigParser.ConfigParser()
    zen_config.read(['zenoss.conf'])
    zen_instance = zen_config.get(options.environ, 'ZENOSS_INSTANCE')
    zen_username = zen_config.get(options.environ, 'ZENOSS_USERNAME')
    zen_password = zen_config.get(options.environ, 'ZENOSS_PASSWORD')

    zen = zenossAPI.ZenossAPI(zen_instance, zen_username, zen_password)

    # result = zen.get_triggerList()['result']
    # data = result['data']
    # for trigger in data:
        # print(trigger)
        # test = zen.get_trigger(trigger['uuid'])
        # print(test)


    triggers_export = zen.export_triggers()['result']
    # print(config)
    # for k in config:
    #    print(k)

    # for r in result:
    #     print(r)

    zen2 = zen
    # result = zen2.import_triggers(config['triggers'])
    # print(result)

    notifs = triggers_export['notifications'][:5]

    for n in notifs:
        if n['name'] == 'RenditionQueue':
            n['subscriptions'] = []
            print(n)
            result = zen2.import_triggers(notifications=[n])['result']
            # print(result['success'])
            # Not working : {u'msg': u"'NotificationSubscriptionInfo' object has no attribute 'getPrimaryUrlPath'", u'type': u'error', u'success': False}
            # Issue with line 748 of /Products/Zuul/facades/triggersfacade.py: notification['uid'] = data['uid'] = obj.getPrimaryUrlPath()
            # To test: Add notification one by one: addNotification - updateNotification
            print(result)


    # result = zen2.import_triggers(notifications=config['notifications'])
    # print(result)


if __name__ == '__main__':
    rc = 1
    try:
        main()
        rc = 0
    except Exception as e:
        print('Error: {}'.format(e))
    sys.exit(rc)
