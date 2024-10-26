from base64 import b64decode, b64encode
from collections import namedtuple
from datetime import date, datetime, timezone
from decimal import Decimal
from logging import getLogger
from math import ceil
from typing import Any, Callable, Dict, Mapping, Type, TypeVar, Union

from flask import request
from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    asc,
    desc,
    inspect,
    or_,
    text,
)
from sqlalchemy import (
    Enum as DbEnum,
)
from zoneinfo import ZoneInfo

from service.api_definition import BAD_VALUE, REQUIRED, Arg, Enum, boolean, natural0, natural1, symbol
from service.db import db_session
from service.error import NotFound, UnprocessableEntity

ASC = "asc"
DESC = "desc"


logger = getLogger("makeradmin")


def not_empty(key, value):
    if not value:
        raise UnprocessableEntity(f"'{key}' can not be empty.", fields=key, what=REQUIRED)


T = TypeVar("T")
U = TypeVar("U")


def to_model_wrap(value_converter: Callable[[T], U]) -> Callable[[str], Callable[[T], Union[U, None]]]:
    def error_handling_wrapper(key: str) -> Callable[[T], Union[U, None]]:
        def converter(value: T) -> Union[U, None]:
            if value is None:
                return None
            try:
                return value_converter(value)
            except Exception as e:
                raise UnprocessableEntity(
                    f"Failed to save value '{value}' as {key}: {str(e)}", fields=key, what=BAD_VALUE
                )

        return converter

    return error_handling_wrapper


def identity(value: T) -> T:
    return value


def base64decode(value):
    if value is None:
        return None
    return b64decode(value)


def base64encode(value):
    if value is None:
        return None
    return b64encode(value).decode()


def fromisoformat(value):
    if value[-1].lower() == "z":
        value = value[:-1]
    return datetime.fromisoformat(value)


to_model_converters: Dict[Type, Callable] = {
    Integer: to_model_wrap(int),
    Numeric: to_model_wrap(Decimal),
    String: to_model_wrap(str),
    Text: to_model_wrap(str),
    DateTime: to_model_wrap(fromisoformat),
    Date: to_model_wrap(date.fromisoformat),
    DbEnum: to_model_wrap(str),
    Boolean: to_model_wrap(bool),
    LargeBinary: to_model_wrap(base64decode),
    JSON: to_model_wrap(identity),
}


to_obj_converters: Dict[Type, Callable] = {
    Integer: identity,
    Numeric: str,
    String: identity,
    Text: identity,
    DateTime: lambda d: None if d is None else d.replace(tzinfo=ZoneInfo("UTC")).isoformat(),
    Date: lambda d: None if d is None else d.isoformat(),
    DbEnum: identity,
    Boolean: identity,
    LargeBinary: base64encode,
    JSON: identity,
}


GLOBAL_READ_ONLY = ("created_at", "updated_at", "deleted_at")


ExpandField = namedtuple("ExpandField", "relation,columns")


class Entity:
    """Used to create a crud-able entity, subclass to provide additional functionality."""

    def __init__(
        self,
        model,
        hidden_columns=tuple(),
        read_only_columns=tuple(),
        validation=None,
        default_sort_column="created_at",
        default_sort_order=DESC,
        search_columns=tuple(),
        expand_fields=None,
    ):
        """
        :param model sqlalchemy orm model class
        :param hidden_columns columns that should be filtered on read
        :param read_only_columns columns that should be filtered on create and update (in addition to GLOBAL_READ_ONLY)
        :param validation map from column name to validation function run on create and update, None values will
                          not be validated, use not null in db
        :param default_sort_column column name
        :param default_sort_order asc/desc
        :param search_columns columns that should be used for text search (search param to list)
        :param expand_fields map of name to ExpandField for data from other models that can be added when listing entity
        """

        self.model = model
        self.name = model.__name__
        self.validation = validation or {}
        self.default_sort_column = default_sort_column
        self.default_sort_order = default_sort_order
        self.search_columns = search_columns
        self.expand_fields = expand_fields or {}

        model_inspect = inspect(self.model)

        assert len(model_inspect.primary_key) == 1, "this class only supports single column primary keys"

        self.pk = model_inspect.primary_key[0]

        self.columns = model_inspect.columns

        assert default_sort_column is None or default_sort_column in self.columns, "default_sort_column does not exist"

        assert default_sort_order in (None, ASC, DESC), "bad default sort order"

        self.cols_to_model = {
            k: to_model_converters[type(c.type)](k)
            for k, c in self.columns.items()
            if (not c.primary_key and k not in GLOBAL_READ_ONLY and k not in read_only_columns)
        }

        self.cols_to_obj = {
            k: to_obj_converters[type(c.type)] for k, c in self.columns.items() if k not in hidden_columns
        }

    def validate_present(self, obj):
        """Validate object for all items in object."""
        for k, v in obj.items():
            func = self.validation.get(k)
            if func:
                func(k, v)

    def validate_all(self, obj):
        """Validate object for all validation items."""
        for k, func in self.validation.items():
            v = obj.get(k)
            if v is not None:
                func(k, v)

    def to_model(self, obj):
        """Convert and filter json compatible object to model compatible dict, also filter fields that is not
        allowed to be edited."""
        if obj is None:
            raise UnprocessableEntity("expected data in request, was empty", what=BAD_VALUE)

        if not isinstance(obj, Mapping):
            raise UnprocessableEntity("expected data object in request", what=BAD_VALUE)

        return {k: self.cols_to_model[k](v) for k, v in obj.items() if k in self.cols_to_model}

    def to_obj(self, entity):
        """Convert model to json compatible object."""
        return {k: conv(getattr(entity, k, None)) for k, conv in self.cols_to_obj.items()}

    def list(
        self,
        sort_by=Arg(symbol, required=False),
        sort_order=Arg(Enum(DESC, ASC), required=False),
        search: str = Arg(str, required=False),
        page_size=Arg(natural0, required=False),
        page=Arg(natural1, required=False),
        expand=Arg(symbol, required=False),
        relation=None,
        related_entity_id=None,
        include_deleted=Arg(boolean, required=False),
    ):
        query = db_session.query(self.model)

        if include_deleted is None:
            include_deleted = False

        if not include_deleted and "deleted_at" in self.columns:
            query = query.filter(self.model.deleted_at.is_(None))

        if relation and related_entity_id:
            query = relation.filter(query, related_entity_id)

        if search:
            for term in search.split():
                expression = or_(*[self.columns[column_name].like(f"%{term}%") for column_name in self.search_columns])
                query = query.filter(expression)

        if expand:
            expand_field = self.expand_fields.get(expand)
            if not expand_field:
                raise UnprocessableEntity(f"Expand of {expand} not allowed.", fields="expand", what=BAD_VALUE)
            query = query.outerjoin(expand_field.relation).add_columns(*expand_field.columns)

            column_obj_converter = [to_obj_converters[type(c.type)] for c in expand_field.columns]

            for c in expand_field.columns:
                self.columns.add(c)

            # Use to_obj that can unpack result row.
            def to_obj(row):
                obj = self.to_obj(row[0])
                for value, column, converter in zip(row[1:], expand_field.columns, column_obj_converter):
                    obj[column.name] = converter(value)
                return obj

        else:
            # Use regular to_obj.
            to_obj = self.to_obj

        sort_column = sort_by or self.default_sort_column
        sort_order = sort_order or self.default_sort_order

        if sort_column:
            try:
                column = self.columns[sort_column]
            except KeyError:
                raise UnprocessableEntity(f"Can't sort on column {sort_column}.", fields="sort_column", what=BAD_VALUE)
            order = desc if sort_order == DESC else asc
            query = query.order_by(order(column))

        count = query.count()

        page_size = 25 if page_size is None else page_size
        page = page or 1

        if page_size:
            query = query.limit(page_size).offset((page - 1) * page_size)

        return dict(
            total=count,
            page=page,
            page_size=page_size,
            last_page=max(1, ceil(count / page_size)) if page_size else 1,
            data=[to_obj(entity) for entity in query],
        )

    def _create_internal(self, data, commit=True):
        """Internal create to make it easier for subclasses to manipulated data before create."""
        input_data = self.to_model(data)
        self.validate_all(input_data)
        if not input_data:
            raise UnprocessableEntity("Can not create using empty data.")
        entity = self.model(**input_data)
        db_session.add(entity)
        if commit:
            db_session.commit()
        else:
            db_session.flush()  # Flush to get id of created entity.

        return entity

    def create(self, data=None, commit=True):
        if data is None:
            data = request.json or {}
        return self.to_obj(self._create_internal(data, commit=commit))

    def read(self, entity_id):
        entity = db_session.query(self.model).get(entity_id)
        if not entity:
            raise NotFound("Could not find any entity with specified parameters.")
        obj = self.to_obj(entity)
        return obj

    def _update_internal(self, entity_id, data, commit=True):
        """Internal update to make it easier for subclasses to manipulated data before update."""
        input_data = self.to_model(data)
        self.validate_present(input_data)
        if not input_data:
            raise UnprocessableEntity("Can not update using empty data.")
        entity = db_session.query(self.model).get(entity_id)
        if not entity:
            raise NotFound("Could not find any entity with specified parameters.")

        for k, v in input_data.items():
            try:
                setattr(entity, k, v)
            except ValueError as e:
                raise UnprocessableEntity(f"Could not save value.", fields=k, what=BAD_VALUE) from e

        if commit:
            db_session.commit()

        return self.to_obj(entity)

    def update(self, entity_id: int, commit: bool = True) -> Any:
        return self._update_internal(entity_id, request.json, commit=commit)

    def delete(self, entity_id: int, commit: bool = True) -> None:
        entity = db_session.query(self.model).get(entity_id)
        if not entity:
            raise NotFound("Could not find any entity with specified parameters.")

        if not entity.deleted_at:
            entity.deleted_at = datetime.now(timezone.utc)

        if commit:
            db_session.commit()

    def _get_entity_id_list(self, name):
        ids = request.json.get(name)
        try:
            if ids is None or any(int(id) < 0 for id in ids):
                raise UnprocessableEntity(f"Unexpected post body, should be list of ids named {name}.", what=BAD_VALUE)
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
        Relation that is implemented through a foreign key in the orm.
        """

        self.name = name
        self.related_entity_id_column = related_entity_id_column

    def add(self, *args):
        raise NotFound("Not supported.", log="Add not supported by this class.")

    def remove(self, *args):
        raise NotFound("Not supported.", log="Remove not supported by this class.")

    def filter(self, query, related_entity_id):
        return query.filter_by(**{self.related_entity_id_column: related_entity_id})


class OrmSingleSingleRelation:
    def __init__(self, name=None, between_model=None, related_entity_id_column=None):
        """
        Relation that is implemented through a foreign key and then another foreigh key in the orm.
        """

        self.name = name
        self.between_model = between_model
        self.related_entity_id_column = related_entity_id_column

    def add(self, *args):
        raise NotFound("Not supported.", log="Add not supported by this class.")

    def remove(self, *args):
        raise NotFound("Not supported.", log="Remove not supported by this class.")

    def filter(self, query, related_entity_id):
        return query.join(self.between_model).filter_by(**{self.related_entity_id_column: related_entity_id})


class OrmManyRelation:
    def __init__(
        self,
        name=None,
        relation_property=None,
        relation_table=None,
        entity_id_column=None,
        related_entity_id_column=None,
    ):
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

        self.insert = text(
            f"REPLACE INTO {self.relation_table.name} "
            f" ({self.entity_id_column}, {self.related_entity_id_column}) "
            f" VALUES (:entity_id, :related_entity_id)"
        )

        self.delete = text(
            f"DELETE FROM {self.relation_table.name} "
            f" WHERE {self.entity_id_column} = :entity_id"
            f" AND {self.related_entity_id_column} = :related_entity_id"
        )

    def add(self, entity_ids, related_entity_id):
        for entity_id in entity_ids:
            db_session.execute(self.insert, {"entity_id": entity_id, "related_entity_id": related_entity_id})

    def remove(self, entity_ids, related_entity_id):
        for entity_id in entity_ids:
            db_session.execute(self.delete, {"entity_id": entity_id, "related_entity_id": related_entity_id})

    def filter(self, query, related_entity_id):
        return query.join(self.relation_property).filter_by(**{self.related_entity_id_column: related_entity_id})
