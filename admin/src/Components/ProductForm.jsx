import React from 'react';
import TextInput from "./TextInput";
import Textarea from "./Textarea";
import DateTimeInput from "./DateTimeInput";
import * as _ from "underscore";
import SelectInput from "./SelectInput";
import ReactSelect from "react-select";
import ProductAction, {ACTION_TYPES} from "../Models/ProductAction";


// Return list of available actions types based on selected ones
const filterAvailableActions = actions => {
      return ACTION_TYPES.filter(type => -1 === _.findIndex(actions, action => type === action.action_type));
};


const filterSelectedActionType = (selectedActionType, availableActionTypes) => {
    if (_.isEmpty(availableActionTypes)) {
        return null;
    }
    if (selectedActionType && -1 !== _.findIndex(availableActionTypes, type => type === selectedActionType)) {
        return selectedActionType;
    }
    return availableActionTypes[0];
};


const productChanged = (prevState, props) => {
    const actions = props.product.actions;
    const availableActionTypes = filterAvailableActions(actions);
    const selectedActionType = filterSelectedActionType(prevState.selectedActionType, availableActionTypes);
    return {
        actions,
        availableActionTypes,
        selectedActionType,
        saveDisabled: !props.product.canSave(),
    };
};


class ProductForm extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            actions: [],
            availableActionTypes: [],
            selectedActionType: null,
            saveDisabled: true,
        };
    }

    componentDidMount() {
        const {product} = this.props;
        this.unsubscribe = product.subscribe(() => this.setState(productChanged));
    }
    
    componentWillUnmount() {
        this.unsubscribe();
    }
    
    render() {
        const {product, onDelete, onSave} = this.props;
        const {actions, availableActionTypes, selectedActionType, saveDisabled} = this.state;
        
        const renderAction = action => (
            <div key={action.action_type} className="form-row uk-grid">
                <div className="uk-with-1-6">{action.action_type}</div>
                <div className="uk-with-1-6"><strong>Värde</strong></div>
                <div className="uk-with-3-6"><TextInput model={action} label={false} formrow={false} name={"value"}/></div>
                <div className="uk-with-1-6">
                    <a className="uk-button uk-button-danger" onClick={() => product.removeAction(action)}><i className="uk-icon-trash-o"/></a>
                </div>
            </div>
        );
        
        return (
            <div className="uk-margin-top">
                <form className="uk-form uk-form-stacked" onSubmit={(e) => {e.preventDefault(); onSave(); return false;}}>
                    <fieldset className="uk-margin-top">
                        <legend><i className="uk-icon-shopping-cart"/> Produkt</legend>
                        <TextInput model={product} name="name" title="Produktnamn" />
                        <SelectInput model={product} name="category_id" title="Kategori" getLabel={o => o.name} getValue={o => o.id} dataSource={"/webshop/category"} />
                        <Textarea model={product} name="description" title="Beskrivning" rows="4"/>
                        <TextInput model={product} name="unit" title="Enhet" />
                        <TextInput model={product} name="price" title="Pris (SEK)" type="number"/>
                        <TextInput model={product} name="smallest_multiple" title="Multipel " type="number"/>
                    </fieldset>
                    <fieldset className="uk-margin-top">
                        <legend><i className="uk-icon-magic"/> Åtgärder</legend>
                        <div>
                            {actions.map(renderAction)}
                        </div>
                        {
                            _.isEmpty(availableActionTypes)
                            ?
                            ""
                            :
                            <div>
                                 <ReactSelect className="uk-width-3-5 uk-float-left"
                                             value={{value: selectedActionType, label: selectedActionType}}
                                             options={availableActionTypes.map(a => ({value: a, label: a}))}
                                             onChange={o => this.setState({selectedActionType: o.value})}
                                />
                                <button type="button" className="uk-button uk-button-success uk-float-right" onClick={() => product.addAction(new ProductAction({action_type: selectedActionType}))}><i className="uk-icon-plus"/> Lägg till åtgärd</button>
                            </div>
                        }
                    </fieldset>
                    <fieldset className="uk-margin-top">
                        <legend><i className="uk-icon-filter"/> Filter</legend>
                        <SelectInput model={product} name="filter" title="Filter" getLabel={o => o.name} getValue={o => o.id} options={[{id: "", name: "No filter"}, {id: "start_package", name: "Startpaket"}]}/>
                    </fieldset>
                    {
                        product.id
                        ?
                        <fieldset className="uk-margin-top">
                            <legend><i className="uk-icon-tag"/> Metadata</legend>
                            <DateTimeInput model={product} name="created_at" title="Skapad"/>
                            <DateTimeInput model={product} name="updated_at" title="Uppdaterad"/>
                        </fieldset>
                        :
                        ""
                    }
                    <fieldset className="uk-margin-top">
                        {product.id ? <a className="uk-button uk-button-danger uk-float-left" onClick={onDelete}><i className="uk-icon-trash"/> Ta bort produkt</a> : ""}
                        <button disabled={saveDisabled} className="uk-button uk-button-success uk-float-right"><i className="uk-icon-save"/> {product.id ? 'Spara' : 'Skapa'}</button>
                    </fieldset>
                </form>
            </div>
        );
        // Image upload not yet supported.
    }
}



export default ProductForm;
