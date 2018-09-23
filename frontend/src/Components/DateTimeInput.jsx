import React from 'react';
import classNames from 'classnames/bind';
import {dateTimeToStr} from "../utils";

export default class DateTimeInput extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: "",
        };
    }
    
    componentDidMount() {
        const {model, name} = this.props;
        this.unsubscribe = model.subscribe(
            () => this.setState({value: dateTimeToStr(model[name])}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }

    render() {
        const {name, title, icon, placeholder} = this.props;
        const {value} = this.state;

        const classes = classNames(name,
                                   {
                                     "uk-form-row": true,
                                     "selected":    this.state.selected,
                                     "changed":     this.state.isDirty,
                                   });
        
        const input = <input type="text"
                             name={name}
                             id={name}
                             disabled={true}
                             value={value}
                             placeholder={placeholder}
                             className="uk-form-width-large"
        />;
        
        return (
            <div className={classes}>
                <label htmlFor={name} className="uk-form-label">{title}</label>
                <div className="uk-form-controls">
                    {icon ? <div className="uk-form-icon"><i className={"uk-icon-" + icon}/>{input}</div> : input}
                </div>
            </div>
        );
    }
}
