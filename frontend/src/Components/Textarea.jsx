import React from "react";
import classNames from 'classnames/bind';

export default class Textarea extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            value: '',
            selected: false,
            isDirty: false,
        };
    }

    componentDidMount() {
        const {model, name} = this.props;
        this.unsubscribe = model.subscribe(() => this.setState({value: model[name] === null ? '' : model[name], isDirty: model.isDirty(name)}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {value, selected, isDirty} = this.state;
        const {model, name, title, icon, disabled, placeholder, formrow, tabIndex, rows} = this.props;
        
        const classes = classNames(name,
                                   {
                                       "uk-form-row": formrow,
                                       "selected": selected,
                                       "changed": isDirty,
                                   });
        
        const textarea = <textarea id={name} name={name} placeholder={placeholder} className="uk-width-1-1"
                                   value={value} disabled={disabled}
                                   tabIndex={tabIndex}
                                   rows={rows || 8}
                                   onChange={(e) => model[name] = e.target.value}
                                   onFocus={() => this.setState({selected: true})}
                                   onBlur={() => this.setState({selected: false})}/>;
        
        return (
            <div className={classes}>
                <label className="uk-form-label" htmlFor={name}>{title}</label>
                <div className="uk-form-controls">
                    {icon ? <div className="uk-form-icon"><i className={"uk-icon-" + icon}/>{textarea}</div> : textarea}
                </div>
            </div>
        );
    }
}

Textarea.defaultProps = {
    formrow: true,
};

