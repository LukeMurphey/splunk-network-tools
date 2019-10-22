import time
import collections

# Python 2+3 basestring
try:
    basestring
except NameError:
    basestring = str

def is_list_of_lists(l):
    for item in l:
        if not isinstance(item, basestring) and isinstance(item, (list, tuple)):
            return True
        if isinstance(item, dict):
            return True
    
    return False

def flatten(item, dictionary=None, name=None, ignore_blanks=False):
    
    if dictionary is None:
        dictionary = collections.OrderedDict()
    
    if name is None:
        name = ""
    
    iterative_name = name
        
    if len(iterative_name) > 0:
        iterative_name = name + "."
    
    # Handle dictionaries
    if isinstance(item, dict):
        for key in item:
            flatten(item[key], dictionary,  iterative_name + key, ignore_blanks=ignore_blanks)
    
    # Handle blanks
    elif ignore_blanks and item in [None, '']:
        pass # Ignore this one
    
    # Handle arrays where the items in the arrays are individual items like strings and numbers (not more lists)
    elif not isinstance(item, basestring) and isinstance(item, (list, tuple)) and not is_list_of_lists(item):
        if len(item) == 0 and ignore_blanks:
            pass # Ignore empty arrays
        else:
            
            # We need to convert the values to strings because Intersplunk.py::outputResults() assumes the values are strings and tries to do string replacements on the values.
            converted_list = []
            
            for i in item:
                converted_list.append(str(i))
                
            # Store the stringifed list
            dictionary[name] = converted_list
        
    elif not isinstance(item, basestring) and isinstance(item, (list, tuple)):
        
        index = 0
        
        for a in item:
            flatten(a, dictionary, iterative_name + str(index), ignore_blanks=ignore_blanks)
            
            index = index + 1
            
    # Handle plain values
    elif item in [True, False, None]: 
        dictionary[name] = item
        
    # Handle date
    elif item.__class__.__name__ == "struct_time":
        dictionary[name] = time.strftime('%Y-%m-%dT%H:%M:%SZ', item)
        
    # Handle string values
    else:
        dictionary[name] = str(item)
        
    return dictionary

def dict_to_table(dictionary, attribute_column_name="attribute", value_column_name="value"):
    results_table = []
    
    for k, v in dictionary.items():
        d = collections.OrderedDict()
        
        d[attribute_column_name] = k
        d[value_column_name] = v
        
        results_table.append(d)
        
    return results_table 

def flatten_to_table(item, attribute_column_name="attribute", value_column_name="value", dictionary=None, name=None, ignore_blanks=False):
    
    results = flatten(item, dictionary=dictionary, name=name, ignore_blanks=ignore_blanks)
    return dict_to_table(results, attribute_column_name=attribute_column_name, value_column_name=value_column_name)
