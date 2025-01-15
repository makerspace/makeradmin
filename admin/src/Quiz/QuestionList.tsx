import React from "react";
import { Link, withRouter } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Icon from "../Components/icons";
import Collection from "../Models/Collection";
import CollectionNavigation, {
    CollectionNavigationProps,
} from "../Models/CollectionNavigation";
import QuizQuestion from "../Models/QuizQuestion";

interface QuestionListProps extends CollectionNavigationProps {
    quiz_id: number;
}

export class QuestionList extends CollectionNavigation<QuestionListProps> {
    collection: Collection<QuizQuestion>;

    constructor(props: QuestionListProps) {
        super(props);
        const { search, page } = this.state;
        const url = `/quiz/quiz/${props.quiz_id}/questions`;
        this.collection = new Collection<QuizQuestion>({
            type: QuizQuestion,
            url,
            search,
            page,
        });
    }

    override render() {
        return (
            <div className="uk-margin-top">
                <h2>Quizfrågor</h2>
                <Link
                    className="uk-button uk-button-primary uk-margin-bottom uk-float-right"
                    to={`/quiz/${this.props["quiz_id"]}/question/add`}
                >
                    <Icon icon="plus-circle" /> Skapa ny fråga
                </Link>
                <CollectionTable
                    className="uk-margin-top"
                    collection={this.collection}
                    emptyMessage="Inga frågor"
                    columns={[{ title: "Fråga" }, { title: "" }]}
                    onPageNav={this.onPageNav}
                    rowComponent={({
                        item,
                        deleteItem,
                    }: {
                        item: QuizQuestion;
                        deleteItem: any;
                    }) => (
                        <tr>
                            <td>
                                <Link to={"/quiz/question/" + item.id}>
                                    {item.question.slice(
                                        0,
                                        Math.min(item.question.length, 100),
                                    )}
                                </Link>
                            </td>
                            <td>
                                <a
                                    onClick={() => deleteItem(item)}
                                    className="removebutton"
                                >
                                    <Icon icon="trash" />
                                </a>
                            </td>
                        </tr>
                    )}
                />
            </div>
        );
    }
}

const QuestionListRouter = withRouter(QuestionList);
export default QuestionListRouter;
