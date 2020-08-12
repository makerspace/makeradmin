import * as common from "./common"
import React from 'react'
import ReactDOM from 'react-dom';

declare var UIkit: any;

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

interface State {
    question: Question|null;
    state: "intro"|"started"|"done",
    answer: null|{
        correct: boolean,
        selected: number,
    },
}

class QuizManager extends React.Component<{}, State> {
    page: HTMLDivElement = document.querySelector(".quizpage");

    constructor(props: any) {
        super(props);
        this.state = {
            question: null,
            answer: null,
            state: "intro",
        }
    }

    async start() {
        this.setState({ state: "started" });
        const data = await common.ajax("GET", `${window.apiBasePath}/quiz/next_question`);
        if (data.data == null) {
            this.setState({ state: "done" });
        } else {
            this.setState({ question: data.data, answer: null });
        }
    }

    render() {
        if (this.state.state == "done") {
            return <div id="content" className="quizpage quiz-complete">
                    <h2>Grattis! Du har svarat rätt på alla frågor i quizzet!</h2>
                    <p>Vi hoppas att det var lärorikt och önskar dig lycka till med alla spännande projekt på Stockholm Makerspace!</p>
                </div>;
        } else if (this.state.state == "intro" || this.state.question == null) {
            return (
                <div id="content" className="quizpage">
                    <h1>Stockholm Makerspace Get Started Quiz!</h1>
                    <p>Hello and welcome as a member of Stockholm Makerspace! We are sure you are excited to get started on a project at the makerspace!</p>
                    <p>To help you get started we have put together this quiz as a learning tool. It will go through many common questions you might have
                        and also many things that you might not have thought about but that are important for you to know in order to make Stockholm Makerspace work well.</p>
                    <p>Note that this is not intended as test of your knowledge, it is a way for new members to learn how things work without having to read through a long and boring document. Don't worry if you pick an incorrect answer, the questions you answered incorrectly
                    will repeat until you have answered all of them correctly and are thus familiar with the basics of how things work at Stockholm Makerspace.
                    Completing this quiz is however a mandatory part of being a member. You will receive nagging emails every few days or so until you complete the quiz.
                    </p>
                    <p>The quiz will save your progress automatically so you close this window and return here at any time to continue with the quiz.</p>
                    <p>Alright, are you ready to get started?</p>
                    <a className="uk-button uk-button-primary quiz-button-start" onClick={()=>this.start()}>Start!</a>
                </div>
            );
        } else {
            return (
                <div id="content" className="quizpage">
                    <h1>Stockholm Makerspace Get Started Quiz!</h1>
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
                    { this.state.answer === null
                        ? null
                        : (
                            <>
                                { this.state.answer.correct
                                    ? <div className="question-answer-info question-answer-info-correct">Snyggt! Du svarade rätt!</div>
                                    : <div className="question-answer-info question-answer-info-incorrect">Du svarade tyvärr fel. Men oroa dig inte, den här frågan kommer komma igen senare så att du kan svara rätt nu när du vet vad rätt svar är.</div>
                                }
                                <div className="question-answer-description">
                                    {
                                        // Split description into paragraphs. Ensure that trailing whitespace on any line doesn't matter.
                                        this.state.question.answer_description.split("\n").map(x => x.trim()).join("\n").split("\n\n").map(x => <p>{x}</p>)
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
        const data = await common.ajax("POST", `${window.apiBasePath}/quiz/question/${this.state.question.id}/answer`, { option_id });
        const fullQuestion = data.data as Question;
        const correct = fullQuestion.options.find(x => x.id == option_id).correct;
        this.setState({ question: fullQuestion, answer: { selected: option_id, correct } });
    }

    async submit() {

    }
}

common.documentLoaded().then(() => {
    ReactDOM.render(
        <React.StrictMode>
            <QuizManager />
        </React.StrictMode>,
        document.getElementById('root')
    );
});
