import React from "react";
import Textarea from "../Components/Textarea";
import QuizQuestion from "../Models/QuizQuestion";
import QuestionOptionList from "./QuestionOptionList";

interface Props {
    question: QuizQuestion | null;
    onSave: () => void;
    onDelete: () => void;
    onNew: () => void;
    onChanged: () => void;
}

const mode_names = {
    single_choice: "Single Choice: User must select one of the correct options",
    multiple_choice: "Multiple Choice: User must select all correct options",
}

const modes = ["single_choice", "multiple_choice"] as const;

export default (props: Props) => {
    const { question } = props;
    const { onSave, onDelete, onNew } = props;
    console.log(question);

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
                            <div className="uk-form-row">
                                <label className="uk-form-label">
                                    Mode
                                </label>
                                <div className="uk-form-controls">
                                    <div
                                        data-uk-dropdown="{mode:'click'}"
                                        className="uk-button-dropdown"
                                    >
                                        <button className="uk-button uk-button">
                                            {mode_names[question.mode]}
                                            <i className="uk-icon-angle-down" />
                                        </button>
                                        <div className="uk-dropdown uk-dropdown-scrollable uk-dropdown-small">
                                            <ul className="uk-nav uk-nav-dropdown">
                                                {modes.map((mode) => (
                                                    <li key={mode}>
                                                        <a
                                                            onClick={(e) => {
                                                                question.mode = mode;
                                                                props.onChanged();
                                                            }}
                                                            className="uk-dropdown-close"
                                                        >
                                                            {mode_names[mode]}
                                                        </a>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
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
