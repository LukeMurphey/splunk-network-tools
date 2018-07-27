"""
This module contains functionality in order to translate the keys of a dictionary to a different
key.

Let's give an example.

Consider the following dictionary:

        dictionary = {
            'objects.LINOD.contact.0.name' : 'John Doe',
            'objects.NETWK.contact.1.name' : 'Jane Doe',
            'objects.LINOD.contact.0.address' : '123 Neverland'
        }

Let's say you want to convert the dictionary such that the field names are shortened:

        dictionary = {
            'contact.name' : ['John Doe', 'Jane Doe'],
            'contact.address' : '123 Neverland'
        }

You do this by calling translate() with some rules, like this:

        translation_rules = [
            ('objects.*.contact.*.name', 'contact.name'),
            ('objects.*.contact.*.address', 'contact.address'),
        ]

        translated_dict = translate(dictionary, translation_rules)

Here are some notes on the behavior:
 1) This function will provide values in an array if the translated key is found more than once.
 2) The translation rules work on wildcards, not on full regular expressions.
"""
import re

def prepare_translation_rules(translation_rules=None):
    """
    Prepare the translation rules by:
      1) Escaping the regexs so they can be modified into wildcards
      2) Converting the wildcards to actual regexs
    """
    escaped_translation_rules = []
    for rule in translation_rules:
        
        # Escape the regex
         escaped_translation_rule = (re.escape(rule[0]), rule[1])

         # Now convert the wildcards to regexs
         escaped_translation_rule = (escaped_translation_rule[0].replace("\\*", ".*"), escaped_translation_rule[1])

         # Add the rule to the list
         escaped_translation_rules.append(escaped_translation_rule)

    # Return the escaped rules
    return escaped_translation_rules

def is_array(value):
    """
    Indicate if the given item is an array but not a string.
    """

    if isinstance(value, list) and not isinstance(value, (str, unicode)):
        return True
    else:
        return False

def merge_values(first_value, second_value):
    """
    Merge the two provided values and creating an array as necessary to hold both values.
    """

    # Case 1: if one of the values are none, then just return the other one
    if first_value is None:
        return second_value

    if second_value is None:
        return first_value

    # Case 2: if the value already exists as an array and the new value is an array, then extend the existing array
    if is_array(first_value) and is_array(second_value):
        new_value = []
        new_value.extend(first_value)
        new_value.extend(second_value)
        return new_value

    # Case 3: if the value already exists as an array and the new value is not an array, then append it
    elif is_array(first_value) and not is_array(second_value):
        new_value = []
        new_value.extend(first_value)
        new_value.append(second_value)
        return new_value

    # Case 3: if the value already exists but not as an array and the new value is an array, then extend the existing array and add it
    elif not is_array(first_value) and is_array(second_value):
        new_value = []
        new_value.append(first_value)
        new_value.extend(second_value)
        return new_value

    # Case 4: if the value already exists but not as an array and the new value is not an array, then create an array with both values
    elif not is_array(first_value) and not is_array(second_value):
        return [first_value, second_value]

    return [first_value, second_value]

def translate_key(existing_key, re_rules):
    """
    Take the existing key and change it according to the given set of rules.
    """

    for rule in re_rules:
        if re.match(rule[0], existing_key):
            return rule[1]

    return None

def translate(dictionary=None, translation_rules=None):
    """
    Take the provided dictionary and translate it according to the provided rules.
    """

    # Prepare the translation rules so that they are now wild-cards
    escaped_translation_rules = prepare_translation_rules(translation_rules)

    # Use the rules to do the conversions
    translated_results = {}

    for key, value in dictionary.items():
        
        # Translate the key
        translated_key = translate_key(key, escaped_translation_rules)

        # We now need to add the value.
        translated_results[translated_key] = merge_values(value, translated_results.get(translated_key, None)) 

    return translated_results
