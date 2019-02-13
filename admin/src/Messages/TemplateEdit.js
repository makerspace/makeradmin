import React from 'react';
import Template from "../Models/Template";
import {withRouter} from "react-router";
import TemplateForm from "../Components/TemplateForm";
import {confirmModal} from "../message";


class TemplateEdit extends React.Component {

    constructor(props) {
        super(props);
        this.template = Template.get(this.props.params.id);
    }
    
    render() {
        return (
            <div className="uk-margin-top">
                <h2>Redigera mall</h2>
                <TemplateForm
                    template={this.template}
                    onSave={() => this.template.save()}
                    onDelete={() => {
                        return confirmModal(this.template.deleteConfirmMessage())
                            .then(() => this.template.del())
                            .then(() => {
                                this.props.router.push("/messages/templates/");
                            })
                            .catch(() => null);
                    }}
                    
                />
            </div>
        );
    }
}

export default withRouter(TemplateEdit);
