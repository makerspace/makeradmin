from datetime import datetime
from decimal import Decimal
from typing import Optional

from membership.models import Base, Member
from sqlalchemy import ForeignKey, Text, func
from sqlalchemy.orm import Mapped, configure_mappers, declarative_base, mapped_column, relationship


class Quiz(Base):
    __tablename__ = "quiz_quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    # Optional required pass rate (0.0 to 1.0). If set, a member fails the quiz if they have
    # more than (1 - required_pass_rate) * total_questions incorrect answers.
    required_pass_rate: Mapped[float]
    # Whether to send help notifications to members when they complete this quiz
    send_help_notifications: Mapped[bool] = mapped_column(default=True)
    # Whether this quiz is visible to members (False hides it from member portal)
    visible: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    def __repr__(self) -> str:
        return f"Quiz(id={self.id}, name={self.name})"


class QuizAttempt(Base):
    """Tracks when a member starts or restarts a quiz attempt."""

    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey(Member.member_id))
    quiz_id: Mapped[int] = mapped_column(ForeignKey(Quiz.id))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    quiz = relationship(Quiz, backref="attempts", cascade_backrefs=False)

    def __repr__(self) -> str:
        return f"QuizAttempt(id={self.id}, member_id={self.member_id}, quiz_id={self.quiz_id})"


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey(Quiz.id))
    question: Mapped[str] = mapped_column(Text)
    answer_description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    def __repr__(self) -> str:
        return f"QuizQuestion(id={self.id}, question={self.question}, quiz={self.quiz_id})"


class QuizQuestionOption(Base):
    __tablename__ = "quiz_question_options"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey(QuizQuestion.id))
    description: Mapped[str] = mapped_column(Text)
    answer_description: Mapped[str] = mapped_column(Text)
    correct: Mapped[bool]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    question = relationship(QuizQuestion, backref="options", cascade_backrefs=False)

    def __repr__(self) -> str:
        return f"QuizQuestionOption(id={self.id}, description={self.description})"


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey(Member.member_id))
    question_id: Mapped[int] = mapped_column(ForeignKey(QuizQuestion.id))
    option_id: Mapped[int] = mapped_column(ForeignKey(QuizQuestionOption.id))
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id"))
    correct: Mapped[bool]

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(default=None)

    question = relationship(QuizQuestion, backref="answers", cascade_backrefs=False)
    attempt = relationship(QuizAttempt, backref="answers", cascade_backrefs=False)

    def __repr__(self) -> str:
        return f"QuizAnswer(id={self.id})"


# https://stackoverflow.com/questions/67149505/how-do-i-make-sqlalchemy-backref-work-without-creating-an-orm-object
configure_mappers()
