import React from "react";
import Icon from "../Components/icons";
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
            className="uk-button uk-button-danger"
            onClick={onDelete}
        >
            <Icon icon="trash" /> Radera fråga
        </a>
    );
    const save_button = (
        <a
            className="uk-button uk-button-primary uk-margin-left"
            onClick={onSave}
        >
            <Icon icon="save" /> {question.id ? "Spara" : "Skapa"}
        </a>
    );
    const new_button = !question.id ? null : (
        <a
            className="uk-button uk-button-primary"
            onClick={onNew}
        >
            <Icon icon="save" /> New question
        </a>
    );

    return (
        <div className="uk-margin-top">
            <form className="uk-form-stacked">
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
                <div className="form-row uk-margin-top uk-flex">
                    {delete_button}
                    <div className="uk-flex-1"/>
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
