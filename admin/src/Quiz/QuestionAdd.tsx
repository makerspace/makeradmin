import React from 'react';
import {withRouter} from "react-router";
import QuizQuestion from "../Models/QuizQuestion";
import { browserHistory } from '../browser_history';
import QuestionEditForm from './QuestionEditForm';

interface State {
    question: null|QuizQuestion;
}

interface Props {
    match: { params: { id: string }}
}

class QuestionAdd extends React.Component<Props, State> {
    question: QuizQuestion;

    constructor(props: any) {
        super(props);
        this.question = new QuizQuestion();
    }

    async save() {
        await this.question.save();
        browserHistory.replace('/quiz/question/' + this.question.id);
    }
    
    delete() {
        browserHistory.push("/quiz/question/");
    }

    render() {
        return (
            <QuestionEditForm
                question={this.question}
                onSave={() => this.save()}
                onDelete={() => this.delete()}
            />
        );
    }
}
    
export default QuestionAdd;
