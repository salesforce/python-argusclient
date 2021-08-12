#
# Copyright (c) 2016, salesforce.com, inc.
# All rights reserved.
# Licensed under the BSD 3-Clause license.
# For full license text, see LICENSE.txt file in the repo root  or https://opensource.org/licenses/BSD-3-Clause
#
# Use the package in this repo (argusclient directory)

from argusclient import *

"""
LOGGING IN!~
"""
username = "s.basu"
password = "TownsendStreet2SF!"
argus = ArgusServiceClient(user="s.basu",
                           password=password,
                           endpoint="http://shared1-argusws1-1-prd.eng.sfdc.net:8080/argusws/")
                           # endpoint = "https://argus-ws.data.sfdc.net/argusws/")
print ('logging in...')
argus.login()
print ('logged in!')
"""
Set endpoint and params
"""
argus.grouppermissions = GroupPermissionsServiceClient(argus, get_all_req_opts= dict(groupID="234-567-891-667-001",
                                                                                                permissionsID=[0,1,2]))



# argus.alerts = AlertsServiceClient(argus, get_all_req_opts={REQ_PARAMS: dict(shared=False,
#                                                                              alertNameContains='TestAlert',
#                                                                              limit=1),
#                                                             REQ_PATH: "allinfo"})
# permission_group_D = {
#     "id": 10,
#     "createdById": 6906380,
#     "createdDate": 1616098911000,
#     "modifiedById": 6906380,
#     "modifiedDate": 1616098911000,
#     "type": "group",
#     "groupId": "c8be7819-bf5e-40aa-8535-88694d34280f",
#     "username": '',
#     "permissionIds": [],
#     "entityId": 23590046
# }

GroupPermission_D = {
    "groupId": "24231-52321-43523-64353-23111",
    "permissionIds": [0,1,2]
}
groupID1 = "24231-52321-43523-64353-23111"
grouppermission = GroupPermission.from_dict(GroupPermission_D)
#groupPerm = argus.grouppermissions.get_permissions_for_group(groupID1)
#print("groupPerms are "+ str(groupPerm))
grouppermission = GroupPermission(GroupPermission_D.get("groupId"),[0,1,2])
groupPerm1 = argus.grouppermissions.add_permissions_for_group(grouppermission)
print("groupPerms are "+ str(groupPerm1))
gpermission = GroupPermission(groupID1,[2])
deletedPerm = argus.grouppermissions.delete_permissions_for_group(groupPerm1) #this is not working as adding group_permission returns a permission object instead of groupPermission object ?
print("removed groupPerms are "+ str(deletedPerm))

#argus.permissions = PermissionsServiceClient(argus)
#group_perm = Permission.from_dict(permission_group_D)
# delattr(group_perm, "id")
# deleted_perm = argus.permissions.delete(23590046, group_perm)
#
# print "updating perm"
# updated_perm = argus.permissions.add(23590046, group_perm)
# print "updated permission is "+ str(updated_perm)
#print ("making call to get perms for entities")
#all_perms = argus.permissions.get_permissions_for_entities([26947204])
#print (all_perms)
#print (type(group_perm))
#for id, val group_perm.items():
    #print (id)
   # print (type(val))
   # for perm in val:
      #  perm_type = perm.type
      #  if perm_type == 'group':
       ##     print (perm.groupId)
       # else:
       #     print (perm.username)
# argus.permissions = PermissionsServiceClient(argus, get_all_req_opts={REQ_PARAMS: dict(shared=False),
# #                                                                       REQ_PATH: "entityIds",
# #                                                                       REQ_METHOD: "post",
# #                                                                       REQ_BODY: [14796957, 14796958]})
# argus.dashboards = DashboardsServiceClient(argus, get_all_req_opts=dict(REQ_PARAMS=dict(username="j.ma", shared=False, limit=3))) # note - limit does not work
"""
Making the call
"""
if __name__ == '__main__':

    # print 'calling items()'
    # res = argus.alerts.items()
   # res = argus.permissions.items()
    # res = argus.dashboards.items()
    print ("calling groupPerms")
    res1 = groupPerm1

    print ('size of result: ', len(res))
    #res = argus.permissions.get(16348603)
    # Get notif
    # alert = res[0][1]
    # print 'notifs:', alert.notifications.items()
    # notifs = alert.notifications.items()
    # notif = notifs[0][1]
    # print '\nresult: ', res
