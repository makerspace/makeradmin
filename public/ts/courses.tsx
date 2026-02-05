import { render } from "preact";
import * as common from "./common";
import { ServerResponse, UNAUTHORIZED } from "./common";
import { useTranslation } from "./i18n";
import * as login from "./login";
import { Quiz } from "./quiz";
import { Sidebar } from "./sidebar";
declare var UIkit: any;

interface QuizInfo {
    quiz: Quiz;
    total_questions_in_quiz: number;
    correctly_answered_questions: number;
    max_pass_rate: number;
    last_pass_rate: number;
    ever_completed: boolean;
    last_attempt_failed: boolean;
}

const CourseButton = ({ quizInfo }: { quizInfo: QuizInfo }) => {
    const { t } = useTranslation("courses");
    const currentlyComplete =
        quizInfo.correctly_answered_questions >=
        quizInfo.total_questions_in_quiz;
    const hasNewVersion = quizInfo.ever_completed && !currentlyComplete;

    let actionBtn;
    if (currentlyComplete) {
        actionBtn = (
            <div class="course-completed">
                {t("course_completed")}{" "}
                <span uk-icon="icon: check; ratio: 1.5" />
            </div>
        );
    } else if (quizInfo.ever_completed) {
        actionBtn = (
            <div class="course-completed">
                {t("course_retake")}{" "}
                <span uk-icon="icon: chevron-right; ratio: 1.5"></span>
            </div>
        );
    } else if (quizInfo.last_attempt_failed) {
        actionBtn = (
            <div class="course-failed">
                {t("course_retry")}{" "}
                <span uk-icon="icon: chevron-right; ratio: 1.5"></span>
            </div>
        );
    } else if (quizInfo.last_pass_rate > 0) {
        actionBtn = (
            <div class="course-not-completed">
                {t("course_continue")} ({Math.round(quizInfo.last_pass_rate)}%){" "}
                <span uk-icon="icon: chevron-right; ratio: 1.5"></span>
            </div>
        );
    } else {
        actionBtn = (
            <div class="course-not-completed">
                {t("course_take")}{" "}
                <span uk-icon="icon: chevron-right; ratio: 1.5"></span>
            </div>
        );
    }

    if (hasNewVersion) {
        return (
            <div class="course-item-wrapper course-item-wrapper-new-version">
                <a
                    href={common.url(`/member/quiz/${quizInfo.quiz.id}`)}
                    className="course-item"
                >
                    <span>{quizInfo.quiz.name}</span>
                    {actionBtn}
                </a>
                <div class="course-new-version-message">
                    {t("course_new_version_description")}
                </div>
            </div>
        );
    }

    return (
        <a
            href={common.url(`/member/quiz/${quizInfo.quiz.id}`)}
            className={`course-item ${
                currentlyComplete ? "course-item-completed" : ""
            }`}
        >
            <span>{quizInfo.quiz.name}</span>
            {actionBtn}
        </a>
    );
};

const CoursesPage = ({ courses }: { courses: QuizInfo[] }) => {
    const { t } = useTranslation("courses");
    return (
        <>
            <Sidebar cart={null} />
            <div id="content">
                <div class="content-centering courses-page">
                    <h2>{t("title")}</h2>
                    <p>{t("description")}</p>
                    <div>
                        {courses.map((quizInfo) => (
                            <CourseButton quizInfo={quizInfo} />
                        ))}
                    </div>
                </div>
            </div>
        </>
    );
};

common.documentLoaded().then(() => {
    common.addSidebarListeners();

    const apiBasePath = window.apiBasePath;

    const future1 = common.ajax(
        "GET",
        apiBasePath + "/member/current/quizzes",
        null,
    );

    const rootElement = document.querySelector("#root") as HTMLElement;
    rootElement.innerHTML = "";

    future1
        .then((quizzesJson: ServerResponse<QuizInfo[]>) => {
            rootElement.innerHTML = "";
            // Filter out invisible quizzes
            const visibleCourses = quizzesJson.data.filter(
                (quizInfo) => quizInfo.quiz.visible !== false,
            );
            render(<CoursesPage courses={visibleCourses} />, rootElement);
        })
        .catch((json) => {
            // Probably Unauthorized, redirect to login page.
            if (json.status === UNAUTHORIZED) {
                // Render login
                login.render_login(rootElement, null, null);
            } else {
                UIkit.modal.alert(
                    "<h2>Misslyckades med att hämta quiz-info</h2>" +
                        common.get_error(json),
                );
            }
        });
});
