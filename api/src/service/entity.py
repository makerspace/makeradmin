from datetime import datetime
from math import ceil

from flask import request
from sqlalchemy import inspect, Integer, String, DateTime, Text, desc, asc, or_

from service.api_definition import BAD_VALUE, REQUIRED, Arg
from service.db import db_session
from service.error import NotFound, UnprocessableEntity


ASC = 'asc'
DESC = 'desc'


def not_empty(key, value):
    if not value:
        raise UnprocessableEntity(f"'{key}' can not be empty.", fields=key, what=REQUIRED)


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


GLOBAl_READ_ONLY = ('created_at', 'updated_at', 'deleted_at')


class Entity:
    """ Used to create a crud-able entity, subclass to provide additional functionality. """
    
    def __init__(self, model, hidden_columns=tuple(), read_only_columns=tuple(), validation=None,
                 default_sort_column=None, default_sort_order=None, search_columns=tuple()):
        """
        :param model sqlalchemy orm model class
        :param hidden_columns columns that should be filtered in all operations
        :param read_only_columns columns that should be filtered on create and update (in addition to GLOBAl_READ_ONLY)
        :param validation map from column name to validation function run on create and update
        :param default_sort_column column name
        :param default_sort_order asc/desc
        :param search_columns columns that should be used for text search (search param to list)
        """
        
        self.model = model
        self.name = model.__name__
        self.validation = validation or {}
        self.default_sort_column = default_sort_column
        self.default_sort_order = default_sort_order
        self.search_columns = search_columns
        
        model_inspect = inspect(self.model)
        
        assert len(model_inspect.primary_key) == 1, "this class only supports single column primary keys"
        
        self.pk = model_inspect.primary_key[0]
        
        self.columns = model_inspect.columns
        
        self.cols_to_model = {
            k: to_model_converters[type(c.type)](k)
            for k, c in self.columns.items()
            if (not c.primary_key
                and k not in GLOBAl_READ_ONLY
                and k not in read_only_columns
                and k not in hidden_columns)
        }
        
        self.cols_to_obj = {
            k: to_obj_converters[type(c.type)]
            for k, c in self.columns.items()
            if k not in hidden_columns
        }
    
    def validate_present(self, obj):
        for k, v in obj.items():
            func = self.validation.get(k)
            if func:
                func(k, v)

    def validate_all(self, obj):
        for k, func in self.validation.items():
            # TODO Use model default here?
            v = obj.get(k)
            func(k, v)
    
    def to_model(self, obj):
        """ Convert and filter json compatible obejct to model compatible dict, also filter fields that is not
        allowed to be edited. """
        return {k: self.cols_to_model[k](v) for k, v in obj.items() if k in self.cols_to_model}
    
    def to_obj(self, entity):
        """ Convert model to json compatible object. """
        return {k: conv(getattr(entity, k, None)) for k, conv in self.cols_to_obj.items()}
    
    def list(self, sort_by=Arg(str, required=False), sort_order=Arg(str, required=False),
             search=Arg(str, required=False), page_size=Arg(int, required=False), page=Arg(int, required=False)):
        # TODO Test sort that does not exist.
        # TODO Implement pagination.
        # TODO Implement search.
        # TODO Sort.
        # TODO Safety of sort_by?
        query = db_session.query(self.model).filter(self.model.deleted_at.is_(None))

        if search:
            expression = or_(*[self.columns[column_name].like(f"%{search}%") for column_name in self.search_columns])
            # TODO Add a test case where like query matches integer column.
            query = query.filter(expression)

        sort_column = sort_by or self.default_sort_column
        sort_order = sort_order or self.default_sort_order
        
        if sort_column:
            order = desc if sort_order == DESC else asc
            query = query.order_by(order(sort_column))

        count = query.count()

        page_size = page_size or 25
        page = page or 1
        
        if page_size:
            query = query.limit(page_size).offset((page - 1) * page_size)
            
        return dict(
            total=count,
            per_page=page_size,
            last_page=ceil(count / page_size),
            data=[self.to_obj(entity) for entity in query]
        )
    
    def create(self):
        input_data = self.to_model(request.json)
        self.validate_all(input_data)
        if not input_data:
            raise UnprocessableEntity("Can not create using empty data.")
        entity = self.model(**input_data)
        db_session.add(entity)
        db_session.commit()
        return self.to_obj(entity)
    
    def read(self, entity_id):
        entity = db_session.query(self.model).get(entity_id)
        if not entity:
            raise NotFound("Could not find any entity with specified parameters.")
        obj = self.to_obj(entity)
        return obj
    
    def update(self, entity_id):
        input_data = self.to_model(request.json)
        self.validate_present(input_data)
        if not input_data:
            raise UnprocessableEntity("Can not update using empty data.")
        db_session.query(self.model).filter(self.pk == entity_id).update(input_data)
        return self.read(entity_id)
    
    def delete(self, entity_id):
        count = db_session.query(self.model).filter(self.pk == entity_id).update(dict(deleted_at=datetime.utcnow()))
        
        assert count <= 1, "More than one entity matching primary key, this is a bug."
        
        if not count:
            raise NotFound("Could not find any entity with specified parameters.")


class EntityWithPassword(Entity):
    # TODO Class or additional parameter. Also hidden_columns is that something that is needed in many places?

    def to_obj(self, entity):
        obj = super().to_obj(entity)
        obj.pop('password', None)
        return obj
    