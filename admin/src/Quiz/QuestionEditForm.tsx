import React from "react";
import Textarea from "../Components/Textarea";
import QuizQuestion from "../Models/QuizQuestion";
import QuestionOptionList from "./QuestionOptionList";

interface Props {
    question: QuizQuestion | null;
    onSave: () => void;
    onDelete: () => void;
    onNew: () => void;
}

export default (props: Props) => {
    const { question } = props;
    const { onSave, onDelete, onNew } = props;

    if (question == null) return null;

    const delete_button = !question.id ? null : (
        <a
            className="uk-button uk-button-danger uk-float-left"
            onClick={onDelete}
        >
            <i className="uk-icon-trash" /> Radera fråga
        </a>
    );
    const save_button = (
        <a
            className="uk-button uk-button-success uk-float-right"
            onClick={onSave}
        >
            <i className="uk-icon-save" /> {question.id ? "Spara" : "Skapa"}
        </a>
    );
    const new_button = !question.id ? null : (
        <a
            className="uk-button uk-button-success uk-float-right"
            onClick={onNew}
        >
            <i className="uk-icon-save" /> New question
        </a>
    );

    return (
        <div className="uk-margin-top">
            <form className="uk-form uk-form-stacked">
                <fieldset className="uk-margin-top">
                    <legend>Quizfråga</legend>
                    {question && (
                        <>
                            <Textarea
                                model={question}
                                name="question"
                                title="Fråga"
                                rows="4"
                            />
                            <Textarea
                                model={question}
                                name="answer_description"
                                title="Lösningsbeskrivning"
                                rows="14"
                            />
                            <i>
                                Du kan använda markdown eller html för att lägga
                                extra funktionalitet och bilder
                            </i>
                        </>
                    )}
                </fieldset>
                <div className="uk-form-row uk-margin-top">
                    {delete_button}
                    {new_button}
                    {save_button}
                </div>
            </form>
            {question.id ? (
                <QuestionOptionList question_id={question.id} />
            ) : (
                <p>
                    Du kan ändra svarsalternativ efter att du har skapat frågan
                </p>
            )}
        </div>
    );
};
