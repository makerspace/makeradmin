import React from "react";
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import Quiz from "../Models/Quiz";

class QuizList extends CollectionNavigation {
    collection: Collection;

    constructor(props: any) {
        super(props);
        const { search, page } = this.state;
        this.collection = new Collection({ type: Quiz, search, page });
    }

    render() {
        return (
            <div className="uk-margin-top">
                <h2>Quizzes</h2>
                <p className="uk-float-left">
                    På denna sida ser du en lista med samtliga quiz.
                </p>
                <Link
                    className="uk-button uk-button-primary uk-margin-bottom uk-float-right"
                    to="/quiz/add"
                >
                    <i className="uk-icon-plus-circle" /> Skapa nytt quiz
                </Link>
                <CollectionTable
                    className="uk-margin-top"
                    collection={this.collection}
                    emptyMessage="Inga quiz"
                    columns={[{ title: "Namn" }, { title: "" }]}
                    onPageNav={this.onPageNav}
                    rowComponent={({
                        item,
                        deleteItem,
                    }: {
                        item: Quiz;
                        deleteItem: any;
                    }) => (
                        <tr>
                            <td>
                                <Link to={"/quiz/" + item.id}>{item.name}</Link>
                            </td>
                            <td>
                                <a
                                    onClick={() => deleteItem(item)}
                                    className="removebutton"
                                >
                                    <i className="uk-icon-trash" />
                                </a>
                            </td>
                        </tr>
                    )}
                />
            </div>
        );
    }
}

export default QuizList;
