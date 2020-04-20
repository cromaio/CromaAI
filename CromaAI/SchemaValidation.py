from schema import Schema, And, Use, Optional, Or
import enum
import sys

def set_options(schema_dict, key, val_schema, required=False, validate_length=False, min_value=None, max_value=None):
    if validate_length:
        val_schema = And(val_schema, len) 
    if min_value is not None and max_value is not None:
            val_schema = And(val_schema, lambda n: min_value <= n <= max_value)
    if required:
        schema_dict[key] = val_schema
    else:
        schema_dict[Optional(key)] = Or(val_schema, None)
        
class EnumFiled():
    def __init__(self, enum_list, required=False):
        self.required = required
        self.types_list = None
        if type(enum_list) == enum.EnumMeta:
            self.types_list = [t for t in enum_list]
            self.enum_list = [t.value for t in enum_list]
        elif type(enum_list) == list:
            self.enum_list = enum_list
        else:
            print('Error: must be a list or enum.EnumMeta')
        
    def get_schema(self, schema_dict, key):  
        if self.types_list is not None:
            val_schema = Or(lambda s: s in self.enum_list, lambda s: s in self.types_list)
        else:
            val_schema = lambda s: s in self.enum_list
        set_options(schema_dict, key, val_schema, self.required)

class DictField():
    def __init__(self, dict_class, required=False):
        self.required = required
        self.dict_class = dict_class
        
    def get_schema(self, schema_dict, key):  
        val_schema = self.dict_class
        set_options(schema_dict, key, val_schema, self.required)
        
class ListField():
    def __init__(self, list_class, required=False, validate_length=True):
        self.required = required
        self.validate_length = validate_length
        self.list_class = list_class
    
    def get_schema(self, schema_dict, key):
        val_schema = [self.list_class]    
        set_options(schema_dict, key, val_schema, self.required, self.validate_length)

class StringField():
    def __init__(self, required=False, validate_length=False):
        self.validate_length = validate_length
        self.required = required
        
    def get_schema(self, schema_dict, key): 
        val_schema = str
        set_options(schema_dict, key, val_schema, self.required, self.validate_length)

class IntField():
    def __init__(self, required=False, min_value=None, max_value=None, convert_to_int=False):
        self.min_value = min_value
        self.max_value = max_value
        self.required = required
        self.convert_to_int = convert_to_int
    
    def get_schema(self, schema_dict, key):
        val_schema = int
        if self.convert_to_int:
            val_schema = Use(int)
        
        set_options(schema_dict, key, val_schema, self.required, min_value=self.min_value, max_value=self.max_value)
            
class FloatField():
    def __init__(self, required=False, min_value=None, max_value=None, convert_to_float=False):
        self.required = required
        self.min_value = min_value
        self.max_value = max_value
        self.convert_to_float = convert_to_float
    
    def get_schema(self, schema_dict, key):
        val_schema = float
        if self.convert_to_float:
            val_schema = Use(float)
       
        set_options(schema_dict, key, val_schema, self.required, min_value=self.min_value, max_value=self.max_value)

class Validation():
    def __init__(self, **kwargs):
        schema_dict = {}
        for k, v in self.__class__.__dict__.items():
            # if not k.startswith('__'):
            # All the Field class are defined in the same module as Validation
            if v.__class__.__module__ == __name__:
                v.get_schema(schema_dict, k)
        self.schema = Schema(schema_dict)
        self.__dict__.update(kwargs)
    
    def __repr__(self):
        data = self.__dict__.copy()
        del data['schema']
        return str(data)
    
    def to_JSON(self, validate=True):
        data = self.__dict__.copy()
        del data['schema']
        if validate:
            self.schema.validate(data)
        
        # Validate items in lists and dictFields
        for k, v in data.items():
            if type(v.__class__) == enum.EnumMeta:
                data[k] = v.value
            if Validation in v.__class__.__bases__:
                data[k] = v.to_JSON(validate=True)
            elif type(v) == list:
                list_data = []
                for l in v:
                    if Validation in l.__class__.__bases__:
                        list_data.append(l.to_JSON(validate=True))
                if len(list_data) > 0:
                    data[k] = list_data
        
        return data
    
    
    def validate(self):
        data = self.to_JSON()
        self.schema.validate(data)