from flask import g, request

from service.api_definition import QUIZ_EDIT, USER, GET, PUBLIC, POST
from quiz.entities import quiz_question_entity, quiz_question_option_entity
from quiz import service
from service.db import db_session
from quiz.models import QuizQuestion, QuizQuestionOption, QuizAnswer
from service.entity import OrmSingeRelation
from sqlalchemy import func, exists, distinct
from membership.models import Member
from dataclasses import dataclass

service.entity_routes(
    path="/question",
    entity=quiz_question_entity,
    permission_list=QUIZ_EDIT,
    permission_read=QUIZ_EDIT,
    permission_create=QUIZ_EDIT,
    permission_update=QUIZ_EDIT,
    permission_delete=QUIZ_EDIT,
)

service.entity_routes(
    path="/question_options",
    entity=quiz_question_option_entity,
    permission_list=QUIZ_EDIT,
    permission_read=QUIZ_EDIT,
    permission_create=QUIZ_EDIT,
    permission_update=QUIZ_EDIT,
    permission_delete=QUIZ_EDIT,
)

service.related_entity_routes(
    path="/question/<int:related_entity_id>/options",
    entity=quiz_question_option_entity,
    relation=OrmSingeRelation('options', 'question_id'),
    permission_list=QUIZ_EDIT,
)

@service.route("/question/<int:question_id>/answer", method=POST, permission=USER)
def answer_question(question_id):
    data = request.json
    option_id = int(data["option_id"])

    option = db_session \
        .query(QuizQuestionOption) \
        .join(QuizQuestionOption.question) \
        .filter((QuizQuestion.id == question_id) & (QuizQuestionOption.id == option_id) & (QuizQuestionOption.deleted_at == None)) \
        .one_or_none()
    if option == None:
        return (400, f"Option id {option_id} is not an option for question id {question_id}")

    db_session.add(QuizAnswer(question_id=question_id, option_id=option_id, member_id=g.user_id, correct=option.correct))
    db_session.flush()

    question = db_session.query(QuizQuestion).get(question_id)
    json = quiz_question_entity.to_obj(question)
    json["options"] = []
    for option in question.options:
        option = quiz_question_option_entity.to_obj(option)
        json["options"].append(option)

    return json


@service.route("/next_question", method=GET, permission=USER)
def next_question(include_correct=False):
    # Find all questions that the user has correctly answered
    correct_questions = db_session.query(QuizQuestion.id) \
        .join(QuizQuestion.answers) \
        .filter(QuizAnswer.member_id == g.user_id) \
        .filter((QuizAnswer.correct) & (QuizAnswer.deleted_at == None))

    # Find questions which the user has not yet answered correctly
    q = db_session.query(QuizQuestion) \
        .filter(QuizQuestion.id.notin_(correct_questions)) \
        .filter(QuizQuestion.deleted_at == None) \
        .order_by(func.random())

    # Pick the first one
    question = q.first()

    if question is None:
        return None

    json = quiz_question_entity.to_obj(question)
    json["options"] = []
    for option in question.options:
        option = quiz_question_option_entity.to_obj(option)
        del option["correct"]
        del option["answer_description"]
        json["options"].append(option)

    del json["answer_description"]

    return json


@service.route("/unfinished", method=GET, permission=PUBLIC)
def quiz_member_answer_stats_route():
    return quiz_member_answer_stats()

@dataclass(frozen=True)
class QuizMemberStat:
    member_id: int
    remaining_questions: int
    correctly_answered_questions: int

def quiz_member_answer_stats():
    ''' Returns all members which haven't completed the quiz'''

    # Calculates how many questions each member has answered correctly
    # Includes an entry for all members, even if it is zero
    correctly_answered_questions = db_session.query(Member.member_id, func.count(distinct(QuizAnswer.option_id)).label("count")) \
        .join(QuizAnswer, Member.member_id==QuizAnswer.member_id, isouter=True) \
        .join(QuizAnswer.question, isouter=True) \
        .filter((QuizAnswer.id == None) | ((QuizAnswer.correct) & (QuizAnswer.deleted_at == None) & (QuizQuestion.deleted_at == None))) \
        .group_by(Member.member_id) \
        .subquery()

    question_count = db_session.query(QuizQuestion).filter(QuizQuestion.deleted_at == None).count()

    members = db_session.query(Member.member_id, correctly_answered_questions.c.count) \
        .join(correctly_answered_questions, (correctly_answered_questions.c.member_id==Member.member_id)) \
        .filter(Member.deleted_at == None)

    return [
        QuizMemberStat(
            member_id=member[0],
            remaining_questions=question_count - member[1],
            correctly_answered_questions=member[1],
         ) for member in members.all()
    ]

