import React from 'react';
import classNames from 'classnames/bind';
import * as _ from "underscore";

// TODO Second time used, reuse.
const dateToStr = date => {
    if (!_.isEmpty(date)) {
        const options = {
            year: 'numeric', month: 'numeric', day: 'numeric',
            hour: 'numeric', minute: 'numeric', second: 'numeric',
            hour12: false
        };
        
        const parsed_date = Date.parse(date);
        
        // If the date was parsed successfully we should update the string
        if (!isNaN(parsed_date)) {
            return new Intl.DateTimeFormat("sv-SE", options).format(parsed_date);
        }
    }
    return "";
};
    

// TODO Rename to Date when Date is no longer used, if dates are ever edited, then implement edit.
export default class Date2 extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: "",
        };
    }
    
    componentDidMount() {
        const {model, name} = this.props;
        this.unsubscribe = model.subscribe(
            () => this.setState({value: dateToStr(model[name])}));
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
