import React from 'react';
import TextInput from "./TextInput";
import {withRouter} from "react-router";
import Textarea from "./Textarea";


class GroupForm extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            saveDisabled: true,
        };
    }
    
    componentDidMount() {
        const {group} = this.props;
        this.unsubscribe = group.subscribe(() => this.setState({saveDisabled: !group.canSave()}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const {group, onSave, onDelete} = this.props;
        const {saveDisabled} = this.state;
        
        return (
            <div className="meep">
                <form className="uk-form uk-margin-bottom" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                    <TextInput model={group} name="name" title="Namn" />
                    <TextInput model={group} name="title" title="Titel" icon="tag" />
                    <Textarea model={group} name="description" title="Beskrivning" />
                    
                    <div className="uk-form-row uk-margin-top">
                        <div className="uk-form-controls">
                            {group.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onDelete}><i className="uk-icon-trash"/> Ta bort grupp</a> : ""}
                            <button className="uk-button uk-button-success uk-float-right" disabled={saveDisabled}><i className="uk-icon-save"/> {group.id ? 'Spara' : 'Skapa'}</button>
                        </div>
                    </div>
                </form>
            </div>
            
        );
    }
}


export default withRouter(GroupForm);