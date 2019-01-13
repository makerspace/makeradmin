from datetime import datetime, date
from math import ceil

from flask import request
from sqlalchemy import inspect, Integer, String, DateTime, Text, desc, asc, or_, text, Date, Enum as DbEnum

from service.api_definition import BAD_VALUE, REQUIRED, Arg, symbol, Enum, natural0, natural1
from service.db import db_session
from service.error import NotFound, UnprocessableEntity, InternalServerError

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
    Date: to_model_wrap(date.fromisoformat),
    DbEnum: to_model_wrap(str),
}


def identity(value):
    return value


to_obj_converters = {
    Integer: identity,
    String: identity,
    Text: identity,
    DateTime: lambda d: None if d is None else d.isoformat(),
    Date: lambda d: None if d is None else d.isoformat(),
    DbEnum: identity,
}


GLOBAl_READ_ONLY = ('created_at', 'updated_at', 'deleted_at')


# TODO BM Expand functionality is used for Key->member and Span->member, nothing else, add support for it.
# Or subclassing if it turns out it is rarly used.

# TODO BM Try to get guis running with both old and new version using same db for verification.

class Entity:
    """ Used to create a crud-able entity, subclass to provide additional functionality. """
    
    def __init__(self, model, hidden_columns=tuple(), read_only_columns=tuple(), validation=None,
                 default_sort_column=None, default_sort_order=None, search_columns=tuple(),
                 list_deleted=False):
        """
        :param model sqlalchemy orm model class
        :param hidden_columns columns that should be filtered on read
        :param read_only_columns columns that should be filtered on create and update (in addition to GLOBAl_READ_ONLY)
        :param validation map from column name to validation function run on create and update
        :param default_sort_column column name
        :param default_sort_order asc/desc
        :param search_columns columns that should be used for text search (search param to list)
        :param list_deleted whether deleted entities should be included in list or not
        # TODO BM Old implementation can search for "roos anders" check this.
        """
        
        self.model = model
        self.name = model.__name__
        self.validation = validation or {}
        self.default_sort_column = default_sort_column
        self.default_sort_order = default_sort_order
        self.search_columns = search_columns
        self.list_deleted = list_deleted
        
        model_inspect = inspect(self.model)
        
        assert len(model_inspect.primary_key) == 1, "this class only supports single column primary keys"
        
        self.pk = model_inspect.primary_key[0]
        
        self.columns = model_inspect.columns
        
        self.cols_to_model = {
            k: to_model_converters[type(c.type)](k)
            for k, c in self.columns.items()
            if (not c.primary_key
                and k not in GLOBAl_READ_ONLY
                and k not in read_only_columns)
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
    
    def list(self, sort_by=Arg(symbol, required=False), sort_order=Arg(Enum(DESC, ASC), required=False),
             search=Arg(str, required=False), page_size=Arg(natural0, required=False),
             page=Arg(natural1, required=False), relation=None, related_entity_id=None):

        query = db_session.query(self.model)\
        
        if not self.list_deleted:
            query = query.filter(self.model.deleted_at.is_(None))

        if relation and related_entity_id:
            query = relation.filter(query, related_entity_id)

        if search:
            expression = or_(*[self.columns[column_name].like(f"%{search}%") for column_name in self.search_columns])
            query = query.filter(expression)

        sort_column = sort_by or self.default_sort_column
        sort_order = sort_order or self.default_sort_order
        
        if sort_column:
            order = desc if sort_order == DESC else asc
            query = query.order_by(order(sort_column))

        count = query.count()

        page_size = 25 if page_size is None else page_size
        page = page or 1
        
        if page_size:
            query = query.limit(page_size).offset((page - 1) * page_size)

        return dict(
            total=count,
            page=page,
            per_page=page_size,
            last_page=ceil(count / page_size) if page_size else 1,
            data=[self.to_obj(entity) for entity in query]
        )
    
    def _create_internal(self, data):
        """ Internal create to make it easier for subclasses to manipulated data before create. """
        input_data = self.to_model(data)
        self.validate_all(input_data)
        if not input_data:
            raise UnprocessableEntity("Can not create using empty data.")
        entity = self.model(**input_data)
        db_session.add(entity)
        db_session.commit()
        return self.to_obj(entity)
    
    def create(self):
        return self._create_internal(request.json)
    
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

    def _get_entity_id_list(self, name):
        ids = request.json.get(name)
        try:
            if ids is None or any(int(id) < 0 for id in ids):
                raise UnprocessableEntity(f"Unexpected post body, should be list of ids named {name}.",
                                          what=BAD_VALUE)
        except ValueError:
            raise UnprocessableEntity(f"Expected list of integers.", what=BAD_VALUE)
        
        return ids
        
    def related_add(self, relation=None, related_entity_id=None):
        relation.add(self._get_entity_id_list(relation.name), related_entity_id)

    def related_remove(self, relation=None, related_entity_id=None):
        relation.remove(self._get_entity_id_list(relation.name), related_entity_id)
    
    
class OrmSingeRelation:
    def __init__(self, name=None, related_entity_id_column=None):
        """
        Relation that is implemented through a foreithn key in the orm.
        """
        
        self.name = name
        self.related_entity_id_column = related_entity_id_column
        
    def add(self, *args):
        raise NotFound("Not supported.", log="Add not supported by this class.")

    def remove(self, *args):
        raise NotFound("Not supported.", log="Add not supported by this class.")

    def filter(self, query, related_entity_id):
        return query.filter_by(**{self.related_entity_id_column: related_entity_id})
        

class OrmManyRelation:
    
    # TODO The use of sqlalchemy in this class could probably be improved/simplified.
    def __init__(self, name=None, relation_property=None, relation_table=None,
                 entity_id_column=None, related_entity_id_column=None):
        """
        Relation that is implemented through a many to many table in the orm.
        
        :param name the name of the entity id list in the post request, also used for the flask entity name
        :param relation_property the orm property of the relation to use
        :param relation_table the relation table
        :param entity_id_column the column name of the entity column name
        :param related_entity_id_column the column name of the related entity column name
        """
        self.name = name
        self.relation_property = relation_property
        self.relation_table = relation_table
        self.entity_id_column = entity_id_column
        self.related_entity_id_column = related_entity_id_column
        
        self.insert = text(f"REPLACE INTO {self.relation_table.name} "
                           f" ({self.entity_id_column}, {self.related_entity_id_column}) "
                           f" VALUES (:entity_id, :related_entity_id)")
    
        self.delete = text(f"DELETE FROM {self.relation_table.name} "
                           f" WHERE {self.entity_id_column} = :entity_id"
                           f" AND {self.related_entity_id_column} = :related_entity_id")
    
    def add(self, entity_ids, related_entity_id):
        for entity_id in entity_ids:
            db_session.execute(self.insert, {'entity_id': entity_id, 'related_entity_id': related_entity_id})

    def remove(self, entity_ids, related_entity_id):
        for entity_id in entity_ids:
            db_session.execute(self.delete, {'entity_id': entity_id, 'related_entity_id': related_entity_id})
    
    def filter(self, query, related_entity_id):
        return query.join(self.relation_property).filter_by(**{self.related_entity_id_column: related_entity_id})


# TODO BM Move this somewhere, belongs to membership.
class MemberEntity(Entity):
    """ Member member_number should be auto increment but mysql only supports one auto increment per table,
    can solve it with a trigger or like this using an explicit mysql lock. """
    
    def create(self):
        status, = db_session.execute("SELECT GET_LOCK('member_number', 20)").fetchone()
        if not status:
            raise InternalServerError("Failed to create member, try again later.",
                                      log="failed to aquire member_number lock")
        
        try:
            data = request.json
            if data.get('member_number') is None:
                sql = "SELECT COALESCE(MAX(member_number), 999) FROM membership_members"
                max_member_number, = db_session.execute(sql).fetchone()
                data['member_number'] = max_member_number + 1
            return self._create_internal(data)
        except Exception:
            # Rollback session if anything went wrong or we can't release the lock.
            db_session.rollback()
            raise
        finally:
            db_session.execute("DO RELEASE_LOCK('member_number')")
        
        
