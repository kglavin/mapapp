#
#  validate the policy rules  and apps across a set of SCM instances. 
#  policy rules include 
#  inbound (NAT Rules)
#  outbound (Firewalling rules)
#  pathrules ( Path Selection, Traffic Steering)
#


def donothing(x,y):
    ''' a funtion that just returns its two inputs, needed for a map operation to joint the 
    elements of two lists '''
    return x,y

def validate_attribute(attr, items, validate_message=""):
    ret = []
    valid = []
    invalid = []
    names = ()
    if attr in items[0]['items'][0]: 
        flag = attr
    else:
        #ret.append((validate_message, False, names, 'attribute {attr} not present in items'))
        return
    
    for i in range(len(items)):
        for j in range(len(items[0]['items'])):          
            if i > 0:
                if items[i-1]['items'][j][flag] != items[i]['items'][j][flag]:
                    invalid.append(items[i]['items'][j][flag])
                else:
                    valid.append(items[i]['items'][j][flag])
            else:
                valid.append(items[i]['items'][j][flag])              
    names = (valid,invalid) 
    
    if len(invalid) != 0:
        ret.append((validate_message + attr, False, names, 'attribute not matching'))
        return ret
    else:
        ret.append((validate_message +attr, True, names, ''))
                   
    return ret   

def validate_rule_basic(rules=[]):
    ''' the input array is the inbound, outbound, or path rules that have been queried from a set of 
        SCM instances. 
        This basic validation checks the basic dimensions or attributes of the rules array that is provided. 
        The check that are undertaken are:
        a) does each of the SCM entries have the same number of rules provisioned
        b) are the names for the rules that are provisioned across all the SCM instances consitent.
        c) is the operaitonal state of each rule instance consitent across the SCM instances. 

        This function works with all three types of rule arrays. 

        inrules = []
        outrules = []
        pathrules = []
        for u,p in map(donothing, users,pws):
        r = scm.get('inbound_rules',realm,u,p)
        inrules.append(r.json())
        r = scm.get('outbound_rules',realm,u, p)
        outrules.append(r.json())
        r = scm.get('path_rules',realm,u, p)
        pathrules.append(r.json())

        validate_rule_basic(inrules)
        validate_rule_basic(outrules)
        validate_rule_basic(pathrules)

        '''
    ret = []
    
    #rule_len validation
    l = len(rules)
    if l < 1:
        ret.append(('rule_len validation', False,'no input rules',0))
        return ret
    else:
        #ret.append(('rule_len validation', True,'input rules provided',l))
        pass
        
    # across the rules array ensure that each element has the same number of rules
    num_rules = []
    old_l = 0 
    for i in range(len(rules)):
        l = len(rules[i]['items'])
        num_rules.append(l)
        # first rule array entry so nothing to compare agaist so just keep it to compare the others against
        if i == 0:
            old_l = l
        if i > 0:
            # other rule arrays, compare with the kept number of rules from the first array entry
            if old_l != l:
                # not same amount of rules 
                ret.append(('rule numbers consistent', False, 'rules have different number of items',num_rules))
                return ret
    ret.append(('rule numbers consistent', True, 'rules have same number of items',num_rules))
    
    #is the rule naming consistent
    valid_rule_names = []
    invalid_rule_names = []
    for i in range(len(rules)):
        for j in range(len(rules[0]['items'])):
            if i > 0:
                # for array entries that are not the first array entry compare with previous array entry
                if rules[i-1]['items'][j]['name'] != rules[i]['items'][j]['name']:
                    #rule name not same
                    invalid_rule_names.append(rules[i]['items'][j]['name'])
                else:
                    valid_rule_names.append(rules[i]['items'][j]['name'])
            else:
                # the [0] rule array entry is valid as there is nothing to compare against.
                valid_rule_names.append(rules[i]['items'][j]['name'])
                
    rule_names = (valid_rule_names,invalid_rule_names) 
    
    if len(invalid_rule_names) != 0:
        ret.append(('rule names consistent', False, rule_names))
    else:
        ret.append(('rule names consistent', True, rule_names))
        
    # are all the equivilent rules enabled
    valid_active_rules = []
    invalid_active_rules = []
    # use of active flag as inbound rules use 'inactive' flag but outbound and pathrules use 'active' flag
    if 'active' in rules[0]['items'][0]: 
        flag = 'active'
    if 'inactive' in rules[0]['items'][0]: 
        flag = 'inactive'
        
    for i in range(len(rules)):
        for j in range(len(rules[0]['items'])):       
            if i > 0:
                if rules[i-1]['items'][j][flag] != rules[i]['items'][j][flag]:
                    #rule activation not same
                    invalid_active_rules.append(rules[i]['items'][j]['name'])
                else:
                    valid_active_rules.append(rules[i]['items'][j]['name'])
            else:
                valid_active_rules.append(rules[i]['items'][j]['name'])
              
    rule_activity = (valid_active_rules,invalid_active_rules)    
    if len(invalid_active_rules) != 0:
        ret.append(('rule operational state consistent', False, rule_activity))
    else:
        ret.append(('rule operational state consistent', True, rule_activity))

    ret.extend(validate_attribute('apps', rules, 'outbound rules type match'))

    return ret




def validate_apps_basic(apps=[]):
    ret = []
    l = len(apps)
    if l < 1:
        ret.append(('apps_len validation', False,0,'no input apps'))
        return ret
    else:
        #ret.append(('apps_len validation', True, l,'input apps provided'))
        pass
    ###
    # number of apps consistent
    ###
    num_apps = []
    old_l = 0 
    for i in range(len(apps)):
        l = len(apps[i]['items'])
        num_apps.append(l)
        if i == 0:
            old_l = l
        if i > 0:
            if old_l != l:
                ret.append(('apps numbers consistent', False, num_apps, 'apps have different number of items'))
                return ret
    ret.append(('apps numbers consistent', True,num_apps, 'apps have same number of items'))   

    ret.extend(validate_attribute('name', apps, 'customapp type match - '))
    ret.extend(validate_attribute('type', apps, 'customapp type match - '))
    ret.extend(validate_attribute('device_proto', apps, 'customapp type match - '))
    ret.extend(validate_attribute('appgrps', apps, 'customapp type match - '))
    ret.extend(validate_attribute('device_ports', apps, 'customapp type match - '))
    return ret