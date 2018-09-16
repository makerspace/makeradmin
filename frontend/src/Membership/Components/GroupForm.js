import React from 'react';
import Input2 from "../../Components/Form/Input2";
import {withRouter} from "react-router";
import Textarea2 from "../../Components/Form/Textarea2";


// TODO Maybe not really a reusable component, check usages later (and move it to better place).
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
                    <Input2    model={group} name="name"        title="Namn" />
                    <Input2    model={group} name="title"       title="Titel" icon="tag" />
                    <Textarea2 model={group} name="description" title="Beskrivning" />
                    
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