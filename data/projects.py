import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import orm


class Project(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'projects'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    title = sqlalchemy.Column(sqlalchemy.String)
    github_link = sqlalchemy.Column(sqlalchemy.String)
    duration_per_dates = sqlalchemy.Column(sqlalchemy.String, default='{}')
    tasks = orm.relationship('Task', backref="project_to_tasks")
    user = orm.relation('User')
