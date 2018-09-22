import React from 'react';
import Template from "../Models/Template";
import {withRouter} from "react-router";
import TemplateForm from "../Components/TemplateForm";


class TemplateAdd extends React.Component {

    constructor(props) {
        super(props);
        this.template = new Template();
    }
    
    render() {
        return (
            <div className="uk-margin-top">
                <h2>Skapa mall</h2>
                <TemplateForm
                    template={this.template}
                    onSave={() => this.template.save().then(() => this.props.router.push("/messages/templates"))}
                />
            </div>
        );
    }
}

export default withRouter(TemplateAdd);
