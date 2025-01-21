import React from "react";
import Quiz from "../Models/Quiz";
import { QuizGraph } from "../Statistics/Graphs/QuizGraph";
import { browserHistory } from "../browser_history";
import { confirmModal } from "../message";
import QuestionListRouter from "./QuestionList";
import QuizEditForm from "./QuizEditForm";

interface State {
    quiz: Quiz;
    loaded: boolean;
}

interface Props {
    match: { params: { id: string } };
}

class QuizShow extends React.Component<Props, State> {
    unsubscribe: () => void = () => {};

    constructor(props: any) {
        super(props);
        const { id } = this.props.match.params;
        const quiz = Quiz.get(parseInt(id)) as Quiz;
        this.state = { quiz, loaded: false };
    }

    override componentDidMount() {
        this.unsubscribe = this.state.quiz.subscribe(() =>
            this.setState({ loaded: true }),
        );
    }

    override componentWillUnmount() {
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

    async restore() {
        this.state.quiz.deleted_at = null;
        await this.state.quiz.save();
        await this.state.quiz.refresh();
    }

    override render() {
        if (this.state.quiz.deleted_at !== null) {
            return (
                <>
                    <h1>{this.state.quiz.name}</h1>
                    <p>Det här quizzet har blivit raderat :(</p>
                </>
            );
        }

        const quiz_id = this.state.quiz.id;
        return (
            <>
                <QuizEditForm
                    quiz={this.state.quiz}
                    onSave={() => this.save()}
                    onDelete={() => this.delete()}
                />
                {quiz_id != null && (
                    <>
                        <QuestionListRouter quiz_id={quiz_id} />
                        <h2>Statistics</h2>
                        <QuizGraph quiz_id={quiz_id} />
                    </>
                )}
            </>
        );
    }
}

export default QuizShow;
