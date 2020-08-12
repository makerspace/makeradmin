import React from 'react';
import Collection from "../Models/Collection";
import { RouteComponentProps } from 'react-router'
import { Link } from "react-router-dom";
import CollectionTable from "../Components/CollectionTable";
import Key from "../Models/Key";
import {confirmModal} from "../message";
import TextInput from "../Components/TextInput";
import DateTimeShow from "../Components/DateTimeShow";
import QuizQuestionOption from '../Models/QuizQuestionOption'
import _ from 'underscore';

// Save functions for each item. Debounced to avoid a ton of unnecessary saves
const debouncedSaves = new Map<QuizQuestionOption, ()=>void>();

const Row = (collection: Collection, onChanged: ()=>void) => ({ item } : { item: QuizQuestionOption }) => {
    
    const deleteItem = () => {
        return confirmModal(item.deleteConfirmMessage()).then(() => item.del()).then(() => collection.fetch(), () => null);
    };

    if (!debouncedSaves.has(item)) debouncedSaves.set(item, _.debounce(() => item.save(), 300));
    
    return (
        <tr key={item.id}>
            <td><input className="uk-input uk-width-1-1" type="text" value={item.description} onChange={v => { item.description=v.target.value, onChanged(); debouncedSaves.get(item)(); }} /></td>
            <td><input className="uk-input" type="checkbox" checked={item.correct} onChange={v => { item.correct=v.target.checked, onChanged(); debouncedSaves.get(item)(); }} /></td>
            <td><a onClick={deleteItem} className="removebutton"><i className="uk-icon-trash"/></a></td>
        </tr>
    );
};

interface State {
    saveEnabled: boolean;
}

interface Props {
    question_id: number,
}

class QuestionOptionList extends React.Component<Props, State> {
    unsubscribe: ()=>void;
    collection: Collection;
    option: QuizQuestionOption;

    constructor(props: Props) {
        super(props);
        const id = props.question_id;
        this.collection = new Collection({type: QuizQuestionOption, url: `/quiz/question/${id}/options`, idListName: 'options', pageSize: 0});
        this.option = new QuizQuestionOption({question_id: id});
        this.state = {saveEnabled: false};
    }
    
    componentDidMount() {
    }
    
    componentWillUnmount() {
    }

    createOption() {
        this.option.description = "Nytt svarsalternativ!";
        this.option
            .save()
            .then(() => {
                      this.option.reset({question_id: this.props.question_id});
                      this.collection.fetch();
                  });
    }
    
    render() {
        const columns = [
            {title: "Svarsalternativ"},
            {title: "Korrekt"},
        ];

        const id = this.props.question_id;
        const {saveEnabled} = this.state;

        return (
            <div>
                <div className="uk-margin-top">
                    <CollectionTable emptyMessage="Inga svarsalternativ finns" rowComponent={Row(this.collection, () => this.setState({}))} collection={this.collection} columns={columns} />
                </div>
                <button onClick={()=>this.createOption()} className="uk-button uk-button-success uk-float-right"><i className="uk-icon-save"/> Lägg till svarsalternativ</button>
            </div>
        );
    }
}


export default QuestionOptionList;
