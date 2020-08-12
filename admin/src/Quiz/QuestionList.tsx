import React from 'react';
import { Link } from "react-router-dom";
import Collection from "../Models/Collection";
import CollectionTable from "../Components/CollectionTable";
import QuizQuestion from '../Models/QuizQuestion';


class QuestionList extends React.Component {
    collection = new Collection({type: QuizQuestion});
    
    render() {
        return (
            <div className="uk-margin-top">
                <h2>Quizfrågor</h2>
                <p className="uk-float-left">På denna sida ser du en lista på samtliga frågor som finns i quizzet.</p>
                <Link className="uk-button uk-button-primary uk-margin-bottom uk-float-right" to="/quiz/question/add"><i className="uk-icon-plus-circle"/> Skapa ny fråga</Link>
                <CollectionTable
                    className="uk-margin-top"
                    collection={this.collection}
                    emptyMessage="Inga frågor"
                    columns={[
                        {title: "Fråga"},
                        {title: ""},
                    ]}
                    rowComponent={({item, deleteItem}: {item: QuizQuestion, deleteItem: any}) =>
                        <tr>
                            <td><Link to={"/quiz/question/" + item.id}>{item.question.slice(0, Math.min(item.question.length, 100))}</Link></td>
                            <td><a onClick={() => deleteItem(item)} className="removebutton"><i className="uk-icon-trash"/></a></td>
                        </tr>
                    }
                />
            </div>
        );
    }
}


export default QuestionList;
