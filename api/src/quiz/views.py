import time
from dataclasses import dataclass
from datetime import timedelta
from logging import getLogger
from typing import Any, List, Optional

from dataclasses_json import DataClassJsonMixin
from flask import g, request
from membership.models import Member
from redis_cache import redis_connection
from service.api_definition import GET, MEMBER_VIEW, POST, PUBLIC, QUIZ_EDIT, USER
from service.db import db_session
from service.entity import OrmSingeRelation
from sqlalchemy import distinct, exists, func, select, text

from quiz import service
from quiz.entities import quiz_entity, quiz_question_entity, quiz_question_option_entity
from quiz.models import Quiz, QuizAnswer, QuizAttempt, QuizQuestion, QuizQuestionOption

logger = getLogger("quiz")

service.entity_routes(
    path="/quiz",
    entity=quiz_entity,
    permission_list=PUBLIC,
    permission_read=PUBLIC,
    permission_create=QUIZ_EDIT,
    permission_update=QUIZ_EDIT,
    permission_delete=QUIZ_EDIT,
)

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
    relation=OrmSingeRelation("options", "question_id"),
    permission_list=QUIZ_EDIT,
)

service.related_entity_routes(
    path="/quiz/<int:related_entity_id>/questions",
    entity=quiz_question_entity,
    relation=OrmSingeRelation("questions", "quiz_id"),
    permission_list=PUBLIC,
)


def _find_current_attempt(member_id: int, quiz_id: int) -> Optional[QuizAttempt]:
    """Find the current (most recent) attempt for a member on a quiz."""
    return (
        db_session.query(QuizAttempt)
        .filter(
            QuizAttempt.member_id == member_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.deleted_at == None,
        )
        .order_by(QuizAttempt.created_at.desc())
        .first()
    )


def get_or_create_current_attempt(member_id: int, quiz_id: int) -> QuizAttempt:
    """Get the current (most recent) attempt for a member on a quiz, or create one if none exists."""
    attempt = _find_current_attempt(member_id, quiz_id)

    if attempt is None:
        attempt = QuizAttempt(member_id=member_id, quiz_id=quiz_id)
        db_session.add(attempt)
        db_session.flush()

    return attempt


def check_attempt_failed(attempt_id: int, quiz: Quiz) -> tuple[bool, int, int]:
    """
    Check if an attempt has failed based on the quiz's required_pass_rate.

    Returns (failed, incorrect_count, max_allowed_incorrect)
    """
    if quiz.required_pass_rate is None:
        return (False, 0, 0)

    # Count total questions in the quiz
    total_questions = (
        db_session.query(func.count(QuizQuestion.id))
        .filter(QuizQuestion.quiz_id == quiz.id, QuizQuestion.deleted_at == None)
        .scalar()
        or 0
    )

    if total_questions == 0:
        return (False, 0, 0)

    # Calculate max allowed incorrect answers
    # required_pass_rate is stored as a fraction (0.0 to 1.0)
    # If required_pass_rate is 0.8, member can have at most 20% incorrect answers
    max_allowed_incorrect = int((1 - float(quiz.required_pass_rate)) * total_questions)

    # Count distinct questions answered incorrectly in this attempt
    # Multiple incorrect answers for the same question count multiple times
    incorrect_count = (
        db_session.query(func.count(QuizAnswer.id))
        .filter(
            QuizAnswer.attempt_id == attempt_id,
            QuizAnswer.correct == False,
            QuizAnswer.deleted_at == None,
        )
        .scalar()
        or 0
    )

    failed = incorrect_count > max_allowed_incorrect
    return (failed, incorrect_count, max_allowed_incorrect)


@service.route("/quiz/<int:quiz_id>/attempt", method=GET, permission=USER)
def get_current_attempt(quiz_id: int):
    """Get the current attempt for the logged-in user on a quiz."""
    attempt = _find_current_attempt(g.user_id, quiz_id)

    if attempt is None:
        return None

    quiz = db_session.get(Quiz, quiz_id)

    # Get the timestamp of the last answer in this attempt
    last_answer = (
        db_session.query(QuizAnswer)
        .filter(
            QuizAnswer.attempt_id == attempt.id,
            QuizAnswer.deleted_at == None,
        )
        .order_by(QuizAnswer.created_at.desc())
        .first()
    )

    # Check if this attempt has failed
    failed = False
    if quiz and quiz.required_pass_rate is not None:
        failed, _, _ = check_attempt_failed(attempt.id, quiz)

    return {
        "id": attempt.id,
        "quiz_id": attempt.quiz_id,
        "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
        "last_answer_at": last_answer.created_at.isoformat() if last_answer and last_answer.created_at else None,
        "failed": failed,
    }


@service.route("/quiz/<int:quiz_id>/start_new_attempt", method=POST, permission=USER)
def start_new_attempt(quiz_id: int):
    """Start a new quiz attempt for the logged-in user. This allows retaking the quiz."""
    # Create a new attempt
    attempt = QuizAttempt(member_id=g.user_id, quiz_id=quiz_id)
    db_session.add(attempt)
    db_session.flush()

    return {
        "id": attempt.id,
        "quiz_id": attempt.quiz_id,
        "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
    }


@service.route("/question/<int:question_id>/answer", method=POST, permission=USER)
def answer_question(question_id):
    data = request.json
    option_id = int(data["option_id"])

    option = (
        db_session.query(QuizQuestionOption)
        .join(QuizQuestionOption.question)
        .filter(
            (QuizQuestion.id == question_id)
            & (QuizQuestionOption.id == option_id)
            & (QuizQuestionOption.deleted_at == None)
        )
        .one_or_none()
    )
    if option == None:
        return (400, f"Option id {option_id} is not an option for question id {question_id}")

    # Get the quiz_id for this question and ensure we have a current attempt
    question = db_session.get(QuizQuestion, question_id)
    if question is None:
        return (400, f"Question id {question_id} not found")

    quiz = db_session.get(Quiz, question.quiz_id)
    if quiz is None:
        return (400, f"Quiz not found for question id {question_id}")

    attempt = get_or_create_current_attempt(g.user_id, int(question.quiz_id))

    db_session.add(
        QuizAnswer(
            question_id=question_id,
            option_id=option_id,
            member_id=g.user_id,
            correct=option.correct,
            attempt_id=attempt.id,
        )
    )
    db_session.flush()

    json = quiz_question_entity.to_obj(question)
    json["options"] = []
    options = (
        db_session.query(QuizQuestionOption)
        .filter(QuizQuestionOption.question_id == question_id, QuizQuestionOption.deleted_at == None)
        .all()
    )
    for option in options:
        option = quiz_question_option_entity.to_obj(option)
        json["options"].append(option)

    # Check if the member has failed the quiz based on required_pass_rate
    if quiz.required_pass_rate is not None:
        failed, incorrect_count, max_allowed = check_attempt_failed(attempt.id, quiz)
        if failed:
            json["quiz_failed"] = True
            json["incorrect_count"] = incorrect_count
            json["max_allowed_incorrect"] = max_allowed

    return json


@service.route("/quiz/<int:quiz_id>/next_question", method=GET, permission=USER)
def next_question(quiz_id: int, include_correct=False):
    # Get or create the current attempt for this user
    attempt = get_or_create_current_attempt(g.user_id, quiz_id)

    # Find all questions that the user has correctly answered in the CURRENT attempt
    correct_questions = (
        db_session.query(QuizQuestion.id)
        .filter(QuizQuestion.quiz_id == quiz_id)
        .join(QuizQuestion.answers)
        .filter(QuizAnswer.member_id == g.user_id)
        .filter(QuizAnswer.attempt_id == attempt.id)
        .filter((QuizAnswer.correct) & (QuizAnswer.deleted_at == None))
    )

    # Find questions which the user has not yet answered correctly in the current attempt
    q = (
        db_session.query(QuizQuestion)
        .filter(QuizQuestion.id.notin_(correct_questions))
        .filter(QuizQuestion.quiz_id == quiz_id)
        .filter(QuizQuestion.deleted_at == None)
        .order_by(func.random())
    )

    # Pick the first one
    question = q.first()

    if question is None:
        return None

    json = quiz_question_entity.to_obj(question)
    json["options"] = []
    for option in question.options:
        option = quiz_question_option_entity.to_obj(option)
        if option["deleted_at"] is None:
            del option["correct"]
            del option["answer_description"]
            json["options"].append(option)

    del json["answer_description"]

    return json


# Converts a list of rows of IDs and values to a map from id to value
def mapify(rows):
    return {r[0]: r[1] for r in rows}


@dataclass
class MemberQuizStatistic(DataClassJsonMixin):
    quiz: Any
    # Current number of questions in the quiz
    total_questions_in_quiz: int
    # Current number of correctly answered questions, across all attempts, of the currently existing questions
    correctly_answered_questions: int
    # Maximum pass rate ever achieved (percentage from 0-100)
    max_pass_rate: float
    # Pass rate of the last attempt (percentage from 0-100), which could be in progress. 0 if no attempts.
    last_pass_rate: float
    # Whether the member has ever fully completed the quiz
    ever_completed: bool
    # Whether the last attempt has failed
    last_attempt_failed: bool


def calculate_max_pass_rates_cached(member_ids: list[int], quiz_id: int) -> list[tuple[float, bool]]:
    # This is enough to uniquely identify the state of the quizes at the time of the last answer
    # Assuming no edits to past answers, and that no answers are deleted (never done at the moment), then the cache should stay valid.
    # It's conservative, in that we check for new answers to any quiz for simplicity.
    last_answer_ids = (
        db_session.execute(
            select(QuizAnswer.member_id, func.max(QuizAnswer.id))
            .filter(
                QuizAnswer.deleted_at == None,
            )
            .group_by(QuizAnswer.member_id)
        )
        .tuples()
        .all()
    )
    last_answer_ids_map = {member_id: last_answer_id for (member_id, last_answer_id) in last_answer_ids}

    redis_keys = [
        f"quiz:max_pass_rate:{member_id}:{quiz_id}:{last_answer_ids_map.get(member_id, None)}"
        for member_id in member_ids
    ]
    results: list[tuple[float, bool]] = []
    cached_values = redis_connection.mget(redis_keys)
    for member_id, cached, redis_key in zip(member_ids, cached_values, redis_keys):
        if cached is not None:
            parts = cached.decode("utf-8").split(",")
            results.append((float(parts[0]), parts[1] == "1"))
            continue

        (max_pass_rate, ever_completed) = calculate_max_pass_rate(member_id, quiz_id)

        redis_connection.setex(redis_key, timedelta(days=7), f"{max_pass_rate},{1 if ever_completed else 0}")
        results.append((max_pass_rate, ever_completed))
    return results


def calculate_max_pass_rate(member_id: int, quiz_id: int) -> tuple[float, bool]:
    """
    Calculate the maximum pass rate a member has ever achieved on a quiz.

    This handles the case where new questions may be added after a member has completed
    the quiz. For each attempt, we calculate the pass rate based on the questions that
    existed at the time of the last answer in that attempt, and return the maximum.

    Returns (max_pass_rate_percentage, ever_completed)
    """
    # Get all attempts for this member on this quiz
    attempts = (
        db_session.query(QuizAttempt)
        .filter(
            QuizAttempt.member_id == member_id,
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.deleted_at == None,
        )
        .order_by(QuizAttempt.created_at)
        .all()
    )

    if not attempts:
        return (0.0, False)

    # Get all questions for this quiz, ordered by creation time
    questions = (
        db_session.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.created_at).all()
    )

    if not questions:
        return (0.0, False)

    max_pass_rate = 0.0
    ever_completed = False

    for attempt in attempts:
        pass_rate, completed = calculate_pass_rate_for_attempt(attempt.id, quiz_id, questions)

        if pass_rate > max_pass_rate:
            max_pass_rate = pass_rate

        if completed:
            ever_completed = True

    return (max_pass_rate, ever_completed)


def calculate_pass_rate_for_attempt(attempt_id: int, quiz: Quiz, questions: list[QuizQuestion]) -> tuple[float, bool]:
    # Get all correct answers from this attempt
    correct_answers = (
        db_session.query(QuizAnswer)
        .join(QuizAnswer.question)
        .filter(
            QuizAnswer.attempt_id == attempt_id,
            QuizAnswer.correct == True,
            QuizAnswer.deleted_at == None,
        )
        .order_by(QuizAnswer.created_at)
        .all()
    )

    if not correct_answers:
        return (0.0, False)

    # Find the timestamp of the last answer in this attempt
    last_answer_time = max(a.created_at for a in correct_answers)

    # Count questions that existed at the time of the last answer
    questions_at_time = [
        q
        for q in questions
        if q.created_at <= last_answer_time and (q.deleted_at is None or q.deleted_at > last_answer_time)
    ]
    if not questions_at_time:
        return (0.0, False)

    # Count correctly answered questions in this attempt
    correctly_answered_question_ids = set(a.question_id for a in correct_answers)
    question_ids_at_time = set(q.id for q in questions_at_time)

    correct_count = len(correctly_answered_question_ids & question_ids_at_time)
    total_count = len(question_ids_at_time)

    pass_rate = (correct_count / total_count) * 100

    completed = correct_count >= total_count

    return pass_rate, completed


def member_quiz_statistics(member_id: int) -> list[MemberQuizStatistic]:
    """Returns information about all quizzes and if the given member has completed them.

    Uses the maximum pass rate ever achieved, not just current state.
    """
    quizzes = db_session.query(Quiz).filter(Quiz.deleted_at == None).all()

    # Current count of correctly answered questions (for showing progress on current attempt)
    answered_questions_per_quiz_query = (
        db_session.query(QuizQuestion.quiz_id, func.count(func.distinct(QuizAnswer.question_id)))
        .join(QuizAnswer, QuizQuestion.id == QuizAnswer.question_id)
        .filter(QuizAnswer.member_id == member_id)
        .filter(
            ((QuizAnswer.id == None) | QuizAnswer.correct)
            & (QuizAnswer.deleted_at == None)
            & (QuizQuestion.deleted_at == None)
        )
        .group_by(QuizQuestion.quiz_id)
    )

    answered_questions_per_quiz = mapify(answered_questions_per_quiz_query.all())

    total_questions_in_quiz = mapify(
        (
            db_session.query(QuizQuestion.quiz_id, func.count(func.distinct(QuizQuestion.id)))
            .filter(QuizQuestion.deleted_at == None)
            .group_by(QuizQuestion.quiz_id)
        ).all()
    )

    result = []
    for quiz in quizzes:
        max_pass_rate, ever_completed = calculate_max_pass_rate(member_id, quiz.id)
        last_pass_rate = 0.0

        last_attempt = _find_current_attempt(member_id, quiz.id)
        failed = False
        if last_attempt:
            # Get all questions for this quiz, ordered by creation time
            questions = (
                db_session.query(QuizQuestion)
                .filter(QuizQuestion.quiz_id == quiz.id)
                .order_by(QuizQuestion.created_at)
                .all()
            )

            failed, _incorrect_count, _max_allowed_incorrect = check_attempt_failed(last_attempt.id, quiz)
            last_pass_rate, _ = calculate_pass_rate_for_attempt(last_attempt.id, quiz, questions)

        result.append(
            MemberQuizStatistic(
                quiz=quiz_entity.to_obj(quiz),
                total_questions_in_quiz=total_questions_in_quiz.get(quiz.id, 0),
                correctly_answered_questions=answered_questions_per_quiz.get(quiz.id, 0),
                max_pass_rate=max_pass_rate,
                last_pass_rate=last_pass_rate,
                ever_completed=ever_completed,
                last_attempt_failed=failed,
            )
        )

    return result


@dataclass(frozen=True)
class QuizMemberStat:
    member_id: int
    remaining_questions: int
    correctly_answered_questions: int
    ever_completed: bool = False


@service.route("/member/<int:member_id>/statistics", method=GET, permission=MEMBER_VIEW)
def member_quiz_statistics_route(member_id: int):
    return [stat.to_dict() for stat in member_quiz_statistics(member_id)]


@service.route("/unfinished/<int:quiz_id>", method=GET, permission=PUBLIC)
def quiz_member_answer_stats_route(quiz_id: int) -> List[QuizMemberStat]:
    return quiz_member_answer_stats(quiz_id)


def quiz_member_answer_stats(quiz_id: int) -> List[QuizMemberStat]:
    """Returns all members and their quiz completion status.

    Uses maximum pass rate calculation to determine if they've ever completed the quiz,
    even if new questions were added afterward.
    """
    question_count = (
        db_session.query(QuizQuestion)
        .filter((QuizQuestion.quiz_id == quiz_id) & (QuizQuestion.deleted_at == None))
        .count()
    )

    # Get all members who have any answers for this quiz
    members_with_answers = list(
        db_session.execute(
            select(Member.member_id)
            .join(QuizAnswer, Member.member_id == QuizAnswer.member_id, isouter=True)
            .join(QuizAnswer.question, isouter=True)
            .filter(Member.deleted_at == None)
            .distinct()
        )
        .scalars()
        .all()
    )

    result = []
    pass_rates = calculate_max_pass_rates_cached(members_with_answers, quiz_id)
    for member_id, (max_pass_rate, ever_completed) in zip(members_with_answers, pass_rates):
        # Count currently correctly answered questions across all attempts (unique questions)
        correctly_answered = (
            db_session.query(func.count(distinct(QuizAnswer.question_id)))
            .join(QuizAnswer.question)
            .filter(
                QuizQuestion.quiz_id == quiz_id,
                QuizAnswer.member_id == member_id,
                QuizAnswer.correct == True,
                QuizAnswer.deleted_at == None,
                QuizQuestion.deleted_at == None,
            )
            .scalar()
            or 0
        )

        result.append(
            QuizMemberStat(
                member_id=member_id,
                remaining_questions=max(0, question_count - correctly_answered),
                correctly_answered_questions=correctly_answered,
                ever_completed=ever_completed,
            )
        )

    return result


@service.route("/quiz/<int:quiz_id>/statistics", method=GET, permission=PUBLIC)
def quiz_statistics(quiz_id: int):
    # How many members have answered the quiz that should have

    # Correct percentage per question
    # Average correct percentage per member

    questions = (
        db_session.query(QuizQuestion)
        .filter(QuizQuestion.deleted_at == None, QuizQuestionOption.deleted_at == None, QuizQuestion.quiz_id == quiz_id)
        .join(QuizQuestion.options)
        .all()
    )

    # Note: counts each member at most once per question. So multiple mistakes on the same question are not counted
    incorrect_answers_by_question = mapify(
        db_session.query(QuizAnswer.question_id, func.count(distinct(QuizAnswer.member_id)))
        .join(QuizAnswer.question)
        .filter(QuizQuestion.quiz_id == quiz_id)
        .filter(QuizAnswer.correct == False)
        .group_by(QuizAnswer.question_id)
        .all()
    )
    answers_by_question = mapify(
        db_session.query(QuizAnswer.question_id, func.count(distinct(QuizAnswer.member_id)))
        .join(QuizAnswer.question)
        .filter(QuizQuestion.quiz_id)
        .filter(QuizAnswer.deleted_at == None)
        .group_by(QuizAnswer.question_id)
        .all()
    )

    first_answer_by_member = (
        db_session.query(QuizAnswer.member_id, QuizAnswer.question_id, func.min(QuizAnswer.id).label("id"))
        .filter(QuizAnswer.deleted_at == None)
        .group_by(QuizAnswer.member_id, QuizAnswer.question_id)
        .subquery()
    )

    answers_by_option = mapify(
        db_session.query(QuizAnswer.option_id, func.count(distinct(QuizAnswer.member_id)))
        .join(
            first_answer_by_member,
            (QuizAnswer.question_id == first_answer_by_member.c.question_id)
            & (QuizAnswer.member_id == first_answer_by_member.c.member_id),
        )
        .join(QuizAnswer.question)
        .filter(QuizAnswer.id == first_answer_by_member.c.id)
        .filter(QuizQuestion.quiz_id == quiz_id)
        .group_by(QuizAnswer.option_id)
        .all()
    )

    seconds_to_answer_quiz = list(
        db_session.execute(
            text(
                "select TIME_TO_SEC(TIMEDIFF(max(quiz_answers.created_at), min(quiz_answers.created_at))) as t from quiz_answers JOIN quiz_questions ON question_id=quiz_questions.id where quiz_questions.quiz_id=:quiz_id group by member_id order by t asc;"
            ),
            {"quiz_id": quiz_id},
        )
    )
    median_seconds_to_answer_quiz = (
        seconds_to_answer_quiz[len(seconds_to_answer_quiz) // 2][0] if len(seconds_to_answer_quiz) > 0 else 0
    )

    return {
        "median_seconds_to_answer_quiz": median_seconds_to_answer_quiz,
        # Maximum number members that have answered any question.
        # This ensures we also account for questions added later (which may not have as many answers)
        # We iterate through the questions list to ensure we dont count deleted questions
        "answered_quiz_member_count": max(
            [answers_by_question.get(question.id, 0) for question in questions], default=0
        ),
        "questions": [
            {
                "question": quiz_question_entity.to_obj(question),
                "options": [
                    {
                        "answer_count": answers_by_option.get(option.id, 0),
                        "option": quiz_question_option_entity.to_obj(option),
                    }
                    for option in question.options
                ],
                # Number of unique members that have answered this question
                "member_answer_count": answers_by_question.get(question.id, 0),
                "incorrect_answer_fraction": sum(
                    answers_by_option.get(option.id, 0) for option in question.options if not option.correct
                )
                / answers_by_question.get(question.id, 1),
            }
            for question in questions
        ],
    }
