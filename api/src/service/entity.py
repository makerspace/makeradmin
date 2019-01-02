from datetime import datetime

from flask import request
from sqlalchemy import inspect, Integer, String, DateTime, Text

from service.api_definition import BAD_VALUE
from service.db import db_session
from service.error import NotFound, UnprocessableEntity
from service.logging import logger


def to_model_wrap(value_converter):
    def error_handling_wrapper(key):
        def converter(value):
            if value is None:
                return None
            try:
                return value_converter(value)
            except Exception as e:
                raise UnprocessableEntity(f"Failed to save value '{value}' as {key}: {str(e)}",
                                          fields=key, what=BAD_VALUE)
        return converter
    return error_handling_wrapper


to_model_converters = {
    Integer: to_model_wrap(int),
    String: to_model_wrap(str),
    Text: to_model_wrap(str),
    DateTime: to_model_wrap(datetime.fromisoformat),
}


def identity(value):
    return value


to_obj_converters = {
    Integer: identity,
    String: identity,
    Text: identity,
    DateTime: lambda d: None if d is None else d.isoformat(),
}


GLOBAl_READ_ONLY_COLUMNS = ('created_at', 'updated_at', 'deleted_at')


class Entity:
    """ Used to create a crud-able entity, subclass to provide additional functionality. """
    
    def __init__(self, model, hidden_columns=tuple(), read_only_columns=tuple()):
        self.model = model
        
        model_inspect = inspect(self.model)
        
        assert len(model_inspect.primary_key) == 1, "this class only supports single column primary keys"
        
        self.pk = model_inspect.primary_key[0]
        
        self.cols_to_model = {
            k: to_model_converters[type(c.type)](k)
            for k, c in model_inspect.columns.items()
            if (not c.primary_key
                and k not in GLOBAl_READ_ONLY_COLUMNS
                and k not in read_only_columns
                and k not in hidden_columns)
        }
        
        self.cols_to_obj = {
            k: to_obj_converters[type(c.type)]
            for k, c in model_inspect.columns.items()
            if k not in hidden_columns
        }
    
    def to_model(self, obj):
        """ Convert and filter json compatible obejct to model compatible dict, also filter fields that is not
        allowed to be edited. """
        return {k: self.cols_to_model[k](v) for k, v in obj.items() if k in self.cols_to_model}
    
    def to_obj(self, entity):
        """ Convert model to json compatible object. """
        return {k: conv(getattr(entity, k, None)) for k, conv in self.cols_to_obj.items()}
    
    def list(self):
        # TODO Implement pagination.
        # TODO Implement filters.
        # TODO Sort.
        return [self.to_obj(entity) for entity in db_session.query(self.model).filter(self.model.deleted_at.is_(None))]
    
    def create(self):
        input_data = self.to_model(request.json)
        if not input_data:
            raise UnprocessableEntity("Can not create using empty data.")
        entity = self.model(**input_data)
        db_session.add(entity)
        db_session.commit()
        return entity.json()
    
    def read(self, entity_id):
        entity = db_session.query(self.model).get(entity_id)
        if not entity:
            raise NotFound("Could not find any entity with specified parameters.")
        obj = self.to_obj(entity)
        logger.info(obj)
        return obj
    
    def update(self, entity_id):
        input_data = self.to_model(request.json)
        if not input_data:
            raise UnprocessableEntity("Can not update using empty data.")
        db_session.query(self.model).filter(self.pk == entity_id).update(input_data)
        return self.read(entity_id)
    
    def delete(self, entity_id):
        count = db_session.query(self.model).filter(self.pk == entity_id).update(dict(deleted_at=datetime.utcnow()))
        
        assert count <= 1, "More than one entity matching primary key, this is a bug."
        
        if not count:
            raise NotFound("Could not find any entity with specified parameters.")
