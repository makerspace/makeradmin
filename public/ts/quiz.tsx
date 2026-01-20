import markdown from "markdown-it";
import { Component, render } from "preact";
import * as common from "./common";
import { ServerResponse, url } from "./common";
import { Login } from "./login";
import { URL_FACEBOOK_GROUP, URL_SLACK_HELP } from "./urls";

declare var UIkit: any;

const markdown_engine = markdown({
    linkify: true,
    html: true,
});

/**
 * Process HTML content to convert relative image URLs to absolute URLs.
 * Replaces /storage/image/* with full API URL.
 */
function processImageUrls(html: string): string {
    if (!html) return html;

    // Replace relative /storage/image/ URLs with absolute API URLs
    // Matches <img src="/storage/image/..." in the rendered HTML
    return html.replace(
        /(<img[^>]+src=["'])\/storage\/image\//g,
        `$1${window.apiBasePath}/storage/image/`,
    );
}

/**
 * Render markdown and process image URLs to be absolute.
 */
function renderMarkdown(content: string): string {
    const html = markdown_engine.render(content);
    return processImageUrls(html);
}

interface Question {
    id: number;
    question: string;
    answer_description?: string;
    options: {
        id: number;
        description: string;
        answer_description?: string;
        correct?: boolean;
    }[];
    quiz_failed?: boolean;
    incorrect_count?: number;
    max_allowed_incorrect?: number;
}

export interface Quiz {
    id: number;
    name: string;
    description: string;
    deleted_at: string | null;
}

interface Attempt {
    id: number;
    quiz_id: number;
    created_at: string | null;
    last_answer_at: string | null;
    failed: boolean;
}

interface State {
    question: Question | null;
    state: "intro" | "started" | "done";
    answerInProgress: boolean;
    loginState: "pending" | "logged in" | "logged out";
    answer: null | {
        correct: boolean;
        selected: number;
    };
    quiz: Quiz | null;
    currentAttempt: Attempt | null;
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
            currentAttempt: null,
        };
    }

    override componentDidMount() {
        this.checkLogin();
        this.loadQuiz();
    }

    async loadQuiz() {
        const quiz: ServerResponse<Quiz> = await common.ajax(
            "GET",
            `${window.apiBasePath}/quiz/quiz/${this.props.quiz_id}`,
        );
        this.setState({ quiz: quiz.data });
    }

    async checkLogin() {
        try {
            await common.ajax(
                "GET",
                `${window.apiBasePath}/member/current`,
                null,
            );
            this.setState({ loginState: "logged in" });
            // Load current attempt after confirming login
            await this.loadCurrentAttempt();
        } catch (error: any) {
            if (error.status == "unauthorized") {
                this.setState({ loginState: "logged out" });
            }
        }
    }

    async loadCurrentAttempt() {
        try {
            const attempt: ServerResponse<Attempt | null> = await common.ajax(
                "GET",
                `${window.apiBasePath}/quiz/quiz/${this.props.quiz_id}/attempt`,
            );
            this.setState({ currentAttempt: attempt.data });
        } catch (error) {
            // No attempt yet, that's fine
        }
    }

    async start() {
        this.setState({ state: "started" });
        try {
            const data: ServerResponse<Question> = await common.ajax(
                "GET",
                `${window.apiBasePath}/quiz/quiz/${
                    this.state.quiz!.id
                }/next_question`,
            );
            if (data.data == null) {
                this.setState({ state: "done" });
            } else {
                this.setState({ question: data.data, answer: null });
            }
        } catch (data: any) {
            if (data.status == "unauthorized") {
                window.location.href = url("/member");
            }
        }
    }

    async startNewAttempt() {
        try {
            // Create a new attempt
            const attempt: ServerResponse<Attempt> = await common.ajax(
                "POST",
                `${window.apiBasePath}/quiz/quiz/${this.props.quiz_id}/start_new_attempt`,
            );
            this.setState({ currentAttempt: attempt.data, state: "intro" });
            // Then start the quiz
            await this.start();
        } catch (data: any) {
            if (data.status == "unauthorized") {
                window.location.href = url("/member");
            }
        }
    }

    isAttemptStale(): boolean {
        const attempt = this.state.currentAttempt;
        if (!attempt || !attempt.last_answer_at) {
            return false;
        }
        const lastAnswerDate = new Date(attempt.last_answer_at);
        const sixtyDaysAgo = new Date();
        sixtyDaysAgo.setDate(sixtyDaysAgo.getDate() - 60);
        return lastAnswerDate < sixtyDaysAgo;
    }

    getStartButtonText(): string {
        const attempt = this.state.currentAttempt;
        if (!attempt) {
            return "Start quiz";
        }
        if (attempt.failed) {
            return "Retake quiz";
        }
        if (this.isAttemptStale()) {
            return "Start new quiz";
        }
        return "Continue quiz";
    }

    shouldStartNewAttempt(): boolean {
        const attempt = this.state.currentAttempt;
        if (!attempt) {
            return false;
        }
        return attempt.failed || this.isAttemptStale();
    }

    async handleStartClick() {
        if (this.shouldStartNewAttempt()) {
            await this.startNewAttempt();
        } else {
            await this.start();
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
            return (
                <div id="content" className="quizpage quiz-complete">
                    <h2>
                        Congratulations!
                        <br />
                        You have correctly answered all questions in the quiz!
                    </h2>
                    <p>
                        We hope that you learned something from it and we wish
                        you good luck with all your exciting projects at
                        Stockholm Makerspace!
                    </p>
                    <div
                        className="quiz-actions uk-flex uk-flex-wrap"
                        style={{ gap: "10px" }}
                    >
                        <a
                            className="uk-button uk-button-primary"
                            href={url("/shop/member/courses")}
                        >
                            Check out more online courses
                        </a>
                        <a
                            className="uk-button uk-button-secondary"
                            onClick={() => this.startNewAttempt()}
                        >
                            Retake Quiz
                        </a>
                    </div>
                    {/* Vi hoppas att det var lärorikt och önskar dig lycka till med alla spännande projekt på Stockholm Makerspace */}
                    <div className="quiz-more-questions">
                        <span>
                            Do you have more questions? Join us on Slack or
                            Facebook and ask away!
                        </span>
                        <ul>
                            <li>
                                <a href={URL_SLACK_HELP}>
                                    <img
                                        src={`${window.staticBasePath}/images/slack_logo_transparent.png`}
                                    ></img>
                                </a>
                            </li>
                            <li>
                                <a href={URL_FACEBOOK_GROUP}>
                                    <img
                                        src={`${window.staticBasePath}/images/facebook_logo_transparent.png`}
                                    ></img>
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            );
        } else if (this.state.state == "intro" || this.state.question == null) {
            return (
                <div id="content" className="quizpage">
                    <h1>{this.state.quiz.name}</h1>
                    <span
                        dangerouslySetInnerHTML={{
                            __html: renderMarkdown(this.state.quiz.description),
                        }}
                    ></span>
                    <p>
                        The quiz will save your progress automatically so you
                        can close this window and return here at any time to
                        continue with the quiz.
                    </p>
                    {this.state.loginState == "logged out" ? (
                        <>
                            <p>
                                You need to be logged in to take the quiz.
                                Please log in and then return to this quiz.
                            </p>
                            <div className="quiz-login">
                                <div className="uk-width-medium">
                                    <Login redirect={window.location.href} />
                                </div>
                            </div>
                        </>
                    ) : this.state.loginState == "pending" ? (
                        <p>Checking if you are logged in...</p>
                    ) : (
                        <>
                            <p>Alright, are you ready to get started?</p>
                            <a
                                className="uk-button uk-button-primary quiz-button-start"
                                onClick={() => this.handleStartClick()}
                            >
                                {this.getStartButtonText()}
                            </a>
                        </>
                    )}
                </div>
            );
        } else {
            const quizFailed = this.state.question.quiz_failed;
            return (
                <div
                    id="content"
                    className={`quizpage ${quizFailed ? "quiz-failed" : ""}`}
                >
                    <h1>{this.state.quiz.name}</h1>
                    <div className="question-text">
                        <div
                            dangerouslySetInnerHTML={{
                                __html: renderMarkdown(
                                    this.state.question.question,
                                ),
                            }}
                        ></div>
                    </div>
                    <ul className="question-options">
                        {this.state.question.options.map((option) => (
                            <li
                                key={option.id}
                                onClick={() => this.select(option.id)}
                                className={
                                    (this.state.answer !== null &&
                                    this.state.answer.selected == option.id
                                        ? "question-option-selected "
                                        : " ") +
                                    (option.correct !== undefined
                                        ? option.correct
                                            ? "question-option-correct"
                                            : "question-option-incorrect"
                                        : "")
                                }
                            >
                                {option.description}
                            </li>
                        ))}
                    </ul>
                    {this.state.answer === null ? null : (
                        <>
                            {this.state.answer.correct ? (
                                <div className="question-answer-info question-answer-info-correct">
                                    Great! You answered correctly!
                                </div>
                            ) : this.state.question.quiz_failed ? (
                                <div className="question-answer-info question-answer-info-incorrect">
                                    Unfortunately you answered incorrectly and
                                    have exceeded the maximum number of allowed
                                    incorrect answers. Please review the
                                    material and try again.
                                </div>
                            ) : (
                                // : <div className="question-answer-info question-answer-info-incorrect">Du svarade tyvärr fel. Men oroa dig inte, den här frågan kommer komma igen senare så att du kan svara rätt nu när du vet vad rätt svar är.</div>
                                <div className="question-answer-info question-answer-info-incorrect">
                                    Unfortunately you answered incorrectly. But
                                    don't worry, this question will repeat later
                                    so you will have an opportunity to answer it
                                    correctly now that you know what the correct
                                    answer is.
                                </div>
                            )}
                            <div
                                className="question-answer-description"
                                dangerouslySetInnerHTML={{
                                    __html: renderMarkdown(
                                        this.state.question.answer_description!,
                                    ),
                                }}
                            ></div>
                            {this.state.question.quiz_failed ? (
                                <a
                                    className="uk-button uk-button-danger question-submit"
                                    href={url(
                                        `/member/quiz/${this.state.quiz!.id}`,
                                    )}
                                >
                                    Back to Course Page
                                </a>
                            ) : (
                                <a
                                    className="uk-button uk-button-primary question-submit"
                                    onClick={() => this.start()}
                                >
                                    Next Question
                                </a>
                            )}
                        </>
                    )}
                </div>
            );
        }
    }

    async select(option_id: number) {
        if (
            this.state.answerInProgress ||
            this.state.answer !== null ||
            this.state.question === null
        )
            return;

        this.setState({ answerInProgress: true });
        const data = await common.ajax(
            "POST",
            `${window.apiBasePath}/quiz/question/${this.state.question.id}/answer`,
            { option_id },
        );
        const fullQuestion = data.data as Question;
        const correct = fullQuestion.options.find(
            (x) => x.id == option_id,
        )!.correct!;

        this.setState({
            question: fullQuestion,
            answer: { selected: option_id, correct },
            answerInProgress: false,
        });
    }

    async submit() {}
}

common.documentLoaded().then(() => {
    const root = document.getElementById("root");
    if (root != null) {
        const splits = document.location.href.split("/");
        let quiz_id = parseInt(splits[splits.length - 1]!);
        if (isNaN(quiz_id)) {
            // Backwards compatibility in case someone has an old link
            quiz_id = 1;
        }
        render(<QuizManager quiz_id={quiz_id} />, root);
    }
});
