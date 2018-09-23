import React from "react";
import classNames from 'classnames/bind';
import {get} from "../gateway";
import Select from "react-select";


export default class SelectInput extends React.Component {

    constructor(props) {
        super(props);
        this.state = {
            options: props.options || [],
            isDirty: false,
            value: null,
        };
        if (props.dataSource) {
            get({url: props.dataSource}).then(data => this.setState({options: data.data}), () => null);
        }
    }

    componentDidMount() {
        const {model, name} = this.props;
        this.unsubscribe = model.subscribe(() => this.setState({value: model[name] === null ? '' : model[name], isDirty: model.isDirty(name)}));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {value, options, isDirty} = this.state;
        const {model, name, title, icon, getValue, getLabel} = this.props;

        const classes = classNames(name,
                                   {
                                       "changed": isDirty,
                                   });

        const select = <Select id={name}
                               name={name}
                               className="uk-width-1-1"
                               options={options}
                               value={options.filter(o => o.id === value)[0]}
                               getOptionValue={getValue}
                               getOptionLabel={getLabel}
                               onChange={o => model[name] = getValue(o)}
                               isDisabled={!options.length}
                        />;
        
        return (
            <div className={classes}>
                <label className="uk-form-label" htmlFor={name}>{title}</label>
                <div className="uk-form-controls">
                    {icon ? <div className="uk-form-icon"><i className={"uk-icon-" + icon}/>{select}</div> : select}
                </div>
            </div>
        );
    }
}
