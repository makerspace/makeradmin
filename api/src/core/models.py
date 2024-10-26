from service.db import db_session
from sqlalchemy import Column, DateTime, Integer, String, Text, func, text
from sqlalchemy.orm import configure_mappers, declarative_base

Base = declarative_base()


class AccessToken(Base):
    __tablename__ = "access_tokens"

    user_id = Column(Integer, index=True, nullable=False)
    access_token = Column(String(32), primary_key=True, nullable=False)
    browser = Column(String(255), nullable=False)
    ip = Column(String(255), nullable=False)
    expires = Column(DateTime, nullable=False)
    permissions = Column(Text)
    lifetime = Column(Integer, nullable=False, server_default=text("300"))

    def __repr__(self):
        return f"AccessToken(user_id={self.access_token}, access_token={self.access_token})"


class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    member_id = Column(Integer, index=True, nullable=False)
    token = Column(String(32), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"PasswordResetToken(member_id={self.member_id}, created_at={self.created_at})"


class Login:
    # login table does not have a possible primary key, so no sqlalchemy model possible.
    # +---------+--------------+------+-----+-------------------+-------------------+
    # | Field   | Type         | Null | Key | Default           | Extra             |
    # +---------+--------------+------+-----+-------------------+-------------------+
    # | success | tinyint(1)   | NO   |     | NULL              |                   |
    # | user_id | int(11)      | YES  |     | NULL              |                   |
    # | ip      | varchar(255) | NO   |     | NULL              |                   |
    # | date    | datetime     | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
    # +---------+--------------+------+-----+-------------------+-------------------+

    @staticmethod
    def register_login_failed(ip):
        db_session.execute(text("INSERT INTO login (success, ip) VALUES (0, :ip)"), {"ip": ip})

    @staticmethod
    def register_login_success(ip, user_id):
        db_session.execute(
            text("INSERT INTO login (success, user_id, ip) VALUES (1, :user_id, :ip)"), {"user_id": user_id, "ip": ip}
        )

    @staticmethod
    def get_failed_login_count(ip):
        (count,) = db_session.execute(
            text(
                "SELECT count(1) FROM login"
                "   WHERE ip = :ip AND NOT success AND date >= DATE_SUB(NOW(), INTERVAL 1 HOUR)"
            ),
            {"ip": ip},
        ).fetchone()
        return count


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
