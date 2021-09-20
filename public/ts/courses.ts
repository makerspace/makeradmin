import * as common from "./common"
import * as login from "./login"
import Cart from "./cart"
import { ServerResponse, UNAUTHORIZED } from "./common";
import { Quiz } from "./quiz";
declare var UIkit: any;

interface QuizInfo {
    quiz: Quiz,
    total_questions_in_quiz: number,
    correctly_answered_questions: number,
}

common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const apiBasePath = window.apiBasePath;

    const future1 = common.ajax("GET", apiBasePath + "/member/current/quizzes", null);

    const rootElement = <HTMLElement>document.querySelector("#courses-contents");
    rootElement.innerHTML = "";

    future1.then((quizzesJson: ServerResponse<QuizInfo[]>) => {
        let content = "";

        for (const quizInfo of quizzesJson.data) {
            const completed = quizInfo.correctly_answered_questions >= quizInfo.total_questions_in_quiz;

            let actionBtn;
            if (completed) {
                actionBtn = `<div class="course-completed">Genomförd <span uk-icon="icon: check; ratio: 1.5"></div>`;
            } else if (quizInfo.correctly_answered_questions > 0) {
                const completed_fraction = quizInfo.correctly_answered_questions / quizInfo.total_questions_in_quiz;
                actionBtn = `<div class="course-not-completed">Fortsätt (${Math.round(completed_fraction * 100)}%) <span uk-icon="icon: chevron-right; ratio: 1.5"></span></div>`;
            } else {
                actionBtn = `<div class="course-not-completed">Ta kursen <span uk-icon="icon: chevron-right; ratio: 1.5"></span></div>`;
            }
            let item = `<a href="/member/quiz/${quizInfo.quiz.id}" class="course-item ${completed ? "course-item-completed" : ""}">
                <span>${quizInfo.quiz.name}</span>
                ${actionBtn}
            </a>
            `;

            content += item + "\n";
        }

        rootElement.innerHTML = content;
    })
        .catch(json => {
            // Probably Unauthorized, redirect to login page.
            if (json.status === UNAUTHORIZED) {
                // Render login
                login.render_login(rootElement, null, null);
            } else {
                UIkit.modal.alert("<h2>Misslyckades med att hämta quiz-info</h2>" + common.get_error(json));
            }
        });
});