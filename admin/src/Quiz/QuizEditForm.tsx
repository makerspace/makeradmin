import { useEffect, useState } from "react";
import Icon from "../Components/icons";
import Textarea from "../Components/Textarea";
import TextInput from "../Components/TextInput";
import Quiz from "../Models/Quiz";

interface Props {
    quiz: Quiz | null;
    onSave: () => void;
    onDelete: () => void;
}

export default (props: Props) => {
    const { quiz } = props;
    const { onSave, onDelete } = props;
    const [version, setVersion] = useState(0);

    if (quiz == null) return null;

    useEffect(() => {
        const unsub = quiz.subscribe(() => setVersion((v) => v + 1));
        return () => {
            unsub();
        };
    }, [quiz]);

    return (
        <div className="uk-margin-top">
            <form
                className="uk-form-stacked"
                onSubmit={(e) => {
                    e.preventDefault();
                    onSave();
                    return false;
                }}
            >
                <fieldset className="uk-margin-top">
                    <legend>Quiz</legend>
                    {quiz && (
                        <>
                            <TextInput model={quiz} name="name" title="Namn" />
                            <Textarea
                                model={quiz}
                                name="description"
                                title="Beskrivning"
                                rows="14"
                            />
                            <i>
                                Du kan använda markdown eller html för att lägga
                                extra funktionalitet och bilder
                            </i>
                            <TextInput
                                model={quiz}
                                name="required_pass_rate"
                                title="Krav på godkänd andel (0-1)"
                                type="number"
                                placeholder="0.8"
                            />
                            <i>
                                Quizzet mislyckas om medlemmen svarar fel på
                                fler än {100 - 100 * quiz.required_pass_rate}%
                                av frågorna.
                            </i>
                            <div className="uk-margin-top">
                                <label>
                                    <input
                                        type="checkbox"
                                        className="uk-checkbox uk-margin-small-right"
                                        checked={quiz.send_help_notifications}
                                        onChange={(e) => {
                                            quiz.send_help_notifications =
                                                e.target.checked;
                                        }}
                                    />
                                    Skicka hjälpmeddelanden vid slutförande
                                </label>
                                <span
                                    className="uk-margin-small-left"
                                    uk-icon="icon: info"
                                    uk-tooltip="Skickar ett meddelande till medlemmar när de har slutfört quizet, med info om vilka andra medlemmar i lokalen de kan fråga om hjälp"
                                />
                            </div>
                        </>
                    )}
                </fieldset>
                <div className="form-row uk-margin-top">
                    {quiz.id ? (
                        <a
                            className="uk-button uk-button-danger uk-float-left"
                            onClick={onDelete}
                        >
                            <Icon icon="trash" /> Radera quiz
                        </a>
                    ) : (
                        ""
                    )}
                    <button className="uk-button uk-button-primary uk-float-right">
                        <Icon icon="save" /> {quiz.id ? "Spara" : "Skapa"}
                    </button>
                </div>
            </form>
        </div>
    );
};
