import * as React from "react";
import classNames from 'classnames/bind';


// TODO Remove local meep stying, use uk.
// TODO Rename to Input when Input is no longer used.
export default class Input2 extends React.Component {

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
        const {model, name, title, icon, disabled, placeholder, formrow, tabIndex, type} = this.props;
        
        const classes = classNames(name,
                                   {
                                       "uk-form-row": formrow,
                                       "selected": selected,
                                       "changed": isDirty,
                                   });
        
        const input = <input id={name} name={name} placeholder={placeholder} className="uk-width-1-1"
                             value={value}
                             disabled={disabled}
                             type={type || "text"}
                             tabIndex={tabIndex}
                             onChange={(event) => model[name] = event.target.value}
                             onFocus={() => this.setState({selected: true})}
                             onBlur={() => this.setState({selected: false})}/>;
        
        return (
            <div className={classes}>
                <label className="uk-form-label" htmlFor={name}>{title}</label>
                <div className="uk-form-controls">
                    {icon ? <div className="uk-form-icon"><i className={"uk-icon-" + icon}/>{input}</div> : input}
                </div>
            </div>
        );
    }
}

Input2.defaultProps = {
    formrow: true,
};

