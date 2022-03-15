from service.entity import Entity, ExpandField
from quiz.models import QuizQuestion, QuizQuestionOption, Quiz

quiz_entity = Entity(
    Quiz,
    default_sort_column=None,
)

quiz_question_entity = Entity(
    QuizQuestion,
    default_sort_column=None,
)

quiz_question_option_entity = Entity(
    QuizQuestionOption,
    default_sort_column=None,
)
