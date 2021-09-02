import React from 'react';
import {withRouter} from "react-router";
import Quiz from "../Models/Quiz";
import Textarea from "../Components/Textarea";
import TextInput from '../Components/TextInput';

interface Props {
    quiz: Quiz|null,
    onSave: ()=>void,
    onDelete: ()=>void,
}

export default (props: Props) => {
    const {quiz} = props;
    const {onSave, onDelete} = props;

    if (quiz == null) return null;

    return (
        <div className="uk-margin-top">
            <form className="uk-form uk-form-stacked" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                <fieldset className="uk-margin-top">
                    <legend>Quiz</legend>
                    { quiz && (
                        <>
                            <TextInput model={quiz} name="name" title="Namn" />
                            <Textarea model={quiz} name="description" title="Beskrivning" rows="14"/>
                        </>)
                    }
                </fieldset>
                <div className="uk-form-row uk-margin-top">
                    {quiz.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onDelete}><i className="uk-icon-trash"/> Radera quiz</a> : ""}
                    <button className="uk-button uk-button-success uk-float-right"><i className="uk-icon-save"/> {quiz.id ? 'Spara' : 'Skapa'}</button>
                </div>
            </form>
        </div>
    );
};