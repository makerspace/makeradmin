import React from "react";
import QuizQuestion from "../Models/QuizQuestion";
import { browserHistory } from "../browser_history";
import { confirmModal } from "../message";
import QuestionEditForm from "./QuestionEditForm";

interface State {
    question: null | QuizQuestion;
}

interface Props {
    match: { params: { id: string } };
}

class QuestionShow extends React.Component<Props, State> {
    unsubscribe: () => void;
    question: QuizQuestion;

    constructor(props: any) {
        super(props);
        const { id } = this.props.match.params;
        this.question = QuizQuestion.get(id) as QuizQuestion;
        this.state = { question: null };
    }

    componentDidMount() {
        this.unsubscribe = this.question.subscribe(() =>
            this.setState({ question: this.question }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    save() {
        this.question.save();
    }

    async delete() {
        try {
            await confirmModal(this.question.deleteConfirmMessage());
            await this.question.del();
            browserHistory.push(`/quiz/${this.question.quiz_id}`);
        } catch {}
    }

    render() {
        return (
            <QuestionEditForm
                question={this.state.question}
                onSave={() => this.save()}
                onDelete={() => this.delete()}
                onNew={() => {
                    browserHistory.push(
                        `/quiz/${this.question.quiz_id}/question/add`,
                    );
                }}
            />
        );
    }
}

export default QuestionShow;
