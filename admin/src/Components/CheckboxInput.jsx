import React from "react";
import classNames from 'classnames/bind';
import * as _ from "underscore";


export default class CheckboxInput extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            value: null,
            selected: false,
            isDirty: false,
        };
    }

    componentDidMount() {
        const {model, name} = this.props;
        this.unsubscribe = model.subscribe(() => this.setState({value: model[name] === '' ? null : model[name], isDirty: model.isDirty(name)}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {value, isDirty} = this.state;
        const {model, name, title, icon, disabled, formrow, tabIndex, label} = this.props;
        
        const classes = classNames(name,
                                   {
                                       "uk-form-row": formrow,
                                       "changed": isDirty,
                                   });
        
        const input = <input id={name} name={name} className=""
                             checked={value}
                             disabled={disabled}
                             type="checkbox"
                             tabIndex={tabIndex}
                             onChange={() => model[name] = !model[name]}
        />;
        
        return (
            <div className={classes}>
                {
                    label
                    ?
                    <label className="uk-form-label" htmlFor={name}>{title}</label>
                    :
                    null
                }
                <div className="uk-form-controls">
                    {icon ? <div className="uk-form-icon"><i className={"uk-icon-" + icon}/>{input}</div> : input}
                </div>
            </div>
        );
    }
}

CheckboxInput.defaultProps = {
    formrow: true,
    label: true,
};

