import React from 'react';
import QuizQuestion from "../Models/QuizQuestion";
import Quiz from "../Models/Quiz";
import { browserHistory } from '../browser_history';
import { confirmModal } from '../message';
import QuestionEditForm from './QuestionEditForm';
import QuestionList from './QuestionList';
import QuizEditForm from './QuizEditForm';

interface State {
    quiz: Quiz;
    loaded: boolean,
}

interface Props {
    match: { params: { id: string }}
}

class QuestionShow extends React.Component<Props, State> {
    unsubscribe: ()=>void;
    quiz: Quiz;

    constructor(props: any) {
        super(props);
        const {id} = this.props.match.params;
        const quiz = Quiz.get(id) as Quiz;
        this.state = {quiz, loaded: false};
    }
    
    componentDidMount() {
        this.unsubscribe = this.state.quiz.subscribe(() => this.setState({loaded: true}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }

    save() {
        this.state.quiz.save();
    }
    
    async delete() {
        try {
            await confirmModal(this.state.quiz.deleteConfirmMessage());
            await this.state.quiz.del();
            browserHistory.push("/quiz/");
        } catch {}
    }

    render() {
        return (
            <>
                <QuizEditForm
                    quiz={this.state.quiz}
                    onSave={()=>this.save()}
                    onDelete={()=>this.delete()}
                />
                <QuestionList quiz_id={this.state.quiz.id}
                />
            </>
        );
    }
}
    
export default QuestionShow;
