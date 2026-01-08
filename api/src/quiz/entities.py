from service.entity import Entity, not_empty

from quiz.models import Quiz, QuizAttempt, QuizQuestion, QuizQuestionOption

quiz_entity = Entity(
    Quiz,
    default_sort_column=None,
    validation=dict(name=not_empty),
)

quiz_attempt_entity = Entity(
    QuizAttempt,
    default_sort_column=None,
    validation=dict(),
)

quiz_question_entity = Entity(
    QuizQuestion,
    default_sort_column=None,
    validation=dict(question=not_empty),
)

quiz_question_option_entity = Entity(
    QuizQuestionOption,
    default_sort_column=None,
    validation=dict(description=not_empty),
)
