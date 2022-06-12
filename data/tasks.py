import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import orm


class Task(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'tasks'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    project_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('projects.id'))
    title = sqlalchemy.Column(sqlalchemy.String)
    duration = sqlalchemy.Column(sqlalchemy.Integer)
    start_time = sqlalchemy.Column(sqlalchemy.DateTime)
    project = orm.relation('Project', viewonly=True)
