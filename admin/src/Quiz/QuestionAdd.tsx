import React from "react";
import QuizQuestion from "../Models/QuizQuestion";
import { browserHistory } from "../browser_history";
import QuestionEditForm from "./QuestionEditForm";

interface State {
    question: null | QuizQuestion;
}

interface Props {
    match: { params: { quiz_id: string } };
}

class QuestionAdd extends React.Component<Props, State> {
    question: QuizQuestion;

    constructor(props: any) {
        super(props);
        this.question = new QuizQuestion();
    }

    async save() {
        this.question.quiz_id = parseInt(this.props.match.params.quiz_id);
        await this.question.save();
        browserHistory.replace("/quiz/question/" + this.question.id);
    }

    delete() {
        browserHistory.push(`/quiz/${this.props.match.params.quiz_id}`);
    }

    override render() {
        return (
            <QuestionEditForm
                question={this.question}
                onSave={() => this.save()}
                onDelete={() => this.delete()}
                onNew={() => {
                    browserHistory.push(
                        `/quiz/${this.props.match.params.quiz_id}/question/add`,
                    );
                }}
            />
        );
    }
}

export default QuestionAdd;
