import React from "react";
import Quiz from "../Models/Quiz";
import { browserHistory } from "../browser_history";
import QuizEditForm from "./QuizEditForm";

interface State {
    quiz: null | Quiz;
}

class QuizAdd extends React.Component<{}, State> {
    quiz: Quiz;

    constructor(props: any) {
        super(props);
        this.quiz = new Quiz();
    }

    async save() {
        await this.quiz.save();
        browserHistory.replace("/quiz/" + this.quiz.id);
    }

    delete() {
        browserHistory.push(`/quiz`);
    }

    render() {
        return (
            <>
                <QuizEditForm
                    quiz={this.quiz}
                    onSave={() => this.save()}
                    onDelete={() => this.delete()}
                />
                <div className="uk-margin-top">
                    <h2>Quizfrågor</h2>
                    <p className="uk-float-left">
                        Du kan lägga till frågor efter att du har skapat quizet
                    </p>
                </div>
            </>
        );
    }
}

export default QuizAdd;
