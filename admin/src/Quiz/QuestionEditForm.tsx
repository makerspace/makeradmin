import React, { useRef } from "react";
import Icon from "../Components/icons";
import Textarea from "../Components/Textarea";
import QuizQuestion from "../Models/QuizQuestion";
import QuestionOptionList from "./QuestionOptionList";
import { PasteImageHandler } from "../Components/PasteImageHandler";
import { notifyError } from "../message";

interface Props {
    question: QuizQuestion | null;
    onSave: () => void;
    onDelete: () => void;
    onNew: () => void;
}

export default (props: Props) => {
    const { question } = props;
    const { onSave, onDelete, onNew } = props;
    const questionRef = useRef<HTMLTextAreaElement>(null);
    const answerDescriptionRef = useRef<HTMLTextAreaElement>(null);

    if (question == null) return null;

    const delete_button = !question.id ? null : (
        <a className="uk-button uk-button-danger" onClick={onDelete}>
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
        <a className="uk-button uk-button-primary" onClick={onNew}>
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
                                ref={questionRef}
                                model={question}
                                name="question"
                                title="Fråga"
                                rows={4}
                            />
                            <PasteImageHandler
                                textAreaRef={questionRef}
                                model={question}
                                fieldName="question"
                                onUploadComplete={() => {}}
                                onUploadError={(error) => {
                                    notifyError(error);
                                }}
                            />
                            <Textarea
                                ref={answerDescriptionRef}
                                model={question}
                                name="answer_description"
                                title="Lösningsbeskrivning"
                                rows={14}
                            />
                            <PasteImageHandler
                                textAreaRef={answerDescriptionRef}
                                model={question}
                                fieldName="answer_description"
                                onUploadComplete={() => {}}
                                onUploadError={(error) => {
                                    notifyError(error);
                                }}
                            />
                            <i>
                                Du kan använda markdown eller html för att lägga
                                extra funktionalitet och bilder. Klistra in
                                eller dra en bild direkt i textfältet för att
                                lägga till den.
                            </i>
                        </>
                    )}
                </fieldset>
                <div className="form-row uk-margin-top uk-flex">
                    {delete_button}
                    <div className="uk-flex-1" />
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
