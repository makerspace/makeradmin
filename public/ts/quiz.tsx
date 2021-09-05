import * as common from "./common"
import { Component, render } from 'preact';
import { useState } from 'preact/hooks';
import { login_via_single_use_link } from './login'
import { ServerResponse } from "./common";

declare var UIkit: any;

const Login = ({ redirect }: { redirect: string }) => {
    let [tag, setTag] = useState("");

    return (
        <div className="uk-width-medium">
            <form className="uk-form" onSubmit={e => {
                e.preventDefault();
                if (tag) {
                    login_via_single_use_link(tag, redirect);
                } else {
                    UIkit.modal.alert("You need to enter your email");
                }
            }}>
                <div className="uk-form-row" style={{ margin: "16px 0" }}>
                    <input autoFocus className="uk-form-large uk-width-1-1" type="text" placeholder="Email/Member number" value={tag} onChange={(v) => setTag(v.currentTarget.value)} />
                </div>

                <div className="uk-form-row" style={{ margin: "16px 0" }}>
                    <button className="uk-width-1-1 uk-button uk-button-primary uk-button-large"><span className="uk-icon-check" />
                        Continue
                    </button>
                </div>
            </form>
            <p style={{ textAlign: "center" }}><a href="/shop/register">Become a member</a></p>
        </div>
    );
}

interface Question {
    id: number,
    question: string,
    answer_description?: string,
    options: {
        id: number,
        description: string,
        answer_description?: string,
        correct?: boolean,
    }[]
}

export interface Quiz {
    id: number,
    name: string,
    description: string,
    deleted_at: string | null,
}

interface State {
    question: Question | null;
    state: "intro" | "started" | "done",
    answerInProgress: boolean,
    loginState: "pending" | "logged in" | "logged out";
    answer: null | {
        correct: boolean,
        selected: number,
    },
    quiz: Quiz | null,
}

interface QuizManagerProps {
    quiz_id: number;
}

class QuizManager extends Component<QuizManagerProps, State> {
    page: HTMLDivElement = document.querySelector<HTMLDivElement>(".quizpage")!;

    constructor(props: any) {
        super(props);
        this.state = {
            answerInProgress: false,
            question: null,
            answer: null,
            loginState: "pending",
            state: "intro",
            quiz: null,
        }
    }

    componentDidMount() {
        this.checkLogin();
        this.loadQuiz();
    }

    async loadQuiz() {
        const quiz: ServerResponse<Quiz> = await common.ajax("GET", `${window.apiBasePath}/quiz/quiz/${this.props.quiz_id}`);
        this.setState({ quiz: quiz.data });
    }

    async checkLogin() {
        try {
            await common.ajax("GET", `${window.apiBasePath}/member/current`, null);
            this.setState({ loginState: "logged in" });
        } catch (error) {
            if (error.status == "unauthorized") {
                this.setState({ loginState: "logged out" });
            }
        }
    }

    async start() {
        this.setState({ state: "started" });
        try {
            const data: ServerResponse<Question> = await common.ajax("GET", `${window.apiBasePath}/quiz/quiz/${this.state.quiz!.id}/next_question`);
            if (data.data == null) {
                this.setState({ state: "done" });
            } else {
                this.setState({ question: data.data, answer: null });
            }
        } catch (data) {
            if (data.status == "unauthorized") {
                window.location.href = "/member";
            }
        }
    }

    render() {
        if (this.state.quiz == null) {
            return (
                <div id="content" className="quizpage">
                    <h1>...</h1>
                </div>
            );
        } else if (this.state.quiz.deleted_at !== null) {
            return (
                <div id="content" className="quizpage">
                    <h1>{this.state.quiz.name}</h1>
                    <p>This quiz has been deleted :(</p>
                </div>
            );
        }

        if (this.state.state == "done") {
            return <div id="content" className="quizpage quiz-complete">
                <h2>Congratulations!<br />You have correctly answered all questions in the quiz!</h2>
                <p>We hope that you learned something from it and we wish you good luck with all your exciting projects at Stockholm Makerspace!</p>
                {/* Vi hoppas att det var lärorikt och önskar dig lycka till med alla spännande projekt på Stockholm Makerspace */}
                <div className="quiz-more-questions">
                    <span>Do you have more questions? Join us on Slack or Facebook and ask away!</span>
                    <ul>
                        <li><a href="https://wiki.makerspace.se/Slack"><img src={`${window.staticBasePath}/images/slack_logo_transparent.png`}></img></a></li>
                        <li><a href="https://www.facebook.com/groups/makerspace.se"><img src={`${window.staticBasePath}/images/facebook_logo_transparent.png`}></img></a></li>
                    </ul>
                </div>
            </div>;
        } else if (this.state.state == "intro" || this.state.question == null) {
            return (
                <div id="content" className="quizpage">
                    <h1>{this.state.quiz.name}</h1>
                    {
                        this.state.quiz.description.split("\n\n").map(paragraph => (<p>{paragraph}</p>))
                    }
                    <p>The quiz will save your progress automatically so you can close this window and return here at any time to continue with the quiz.</p>
                    {this.state.loginState == "logged out"
                        ?
                        <>
                            <p>You need to be logged in to take the quiz. Please log in and then return to this quiz.</p>
                            <div className="quiz-login">
                                <Login redirect={window.location.href} />
                            </div>
                        </>
                        : (
                            this.state.loginState == "pending"
                            ? <p>Checking if you are logged in...</p>
                            :
                            <>
                                <p>Alright, are you ready to get started?</p>
                                <a className="uk-button uk-button-primary quiz-button-start" onClick={() => this.start()}>Start!</a>
                            </>
                        )
                    }
                </div>
            );
        } else {
            return (
                <div id="content" className="quizpage">
                    <h1>{this.state.quiz.name}</h1>
                    <div className="question-text">{this.state.question.question}</div>
                    <ul className="question-options">
                        {
                            this.state.question.options.map(option => (
                                <li
                                    key={option.id}
                                    onClick={() => this.select(option.id)}
                                    className={
                                        (this.state.answer !== null && this.state.answer.selected == option.id ? "question-option-selected " : " ") +
                                        (option.correct !== undefined ? (option.correct ? "question-option-correct" : "question-option-incorrect") : "")
                                    }
                                >
                                    {option.description}
                                </li>
                            )
                            )
                        }
                    </ul>
                    {this.state.answer === null
                        ? null
                        : (
                            <>
                                {this.state.answer.correct
                                    ? <div className="question-answer-info question-answer-info-correct">Great! You answered correctly!</div>
                                    // : <div className="question-answer-info question-answer-info-incorrect">Du svarade tyvärr fel. Men oroa dig inte, den här frågan kommer komma igen senare så att du kan svara rätt nu när du vet vad rätt svar är.</div>
                                    : <div className="question-answer-info question-answer-info-incorrect">Unfortunately you answered incorrectly. But don't worry, this question will repeat later so you will have an opportunity to answer it correctly now that you know what the correct answer is.</div>
                                }
                                <div className="question-answer-description">
                                    {
                                        // Split description into paragraphs. Ensure that trailing whitespace on any line doesn't matter.
                                        this.state.question.answer_description!.split("\n").map(x => x.trim()).join("\n").split("\n\n").map(x => <p>{x}</p>)
                                    }
                                </div>
                                <a className="uk-button uk-button-primary question-submit" onClick={() => this.start()}>Next Question</a>
                            </>
                        )
                    }

                </div>
            );
        }
    }

    async select(option_id: number) {
        if (this.state.answerInProgress || this.state.answer !== null || this.state.question === null) return;

        this.setState({ answerInProgress: true });
        const data = await common.ajax("POST", `${window.apiBasePath}/quiz/question/${this.state.question.id}/answer`, { option_id });
        const fullQuestion = data.data as Question;
        const correct = fullQuestion.options.find(x => x.id == option_id)!.correct!;
        this.setState({ question: fullQuestion, answer: { selected: option_id, correct }, answerInProgress: false });
    }

    async submit() {

    }
}

common.documentLoaded().then(() => {
    const root = document.getElementById('root');
    if (root != null) {
        const splits = document.location.href.split("/");
        let quiz_id = parseInt(splits[splits.length-1]);
        if (isNaN(quiz_id)) {
            // Backwards compatibility in case someone has an old link
            quiz_id = 1;
        }
        render(
            <QuizManager quiz_id={quiz_id}/>,
            root
        );
    }
});
