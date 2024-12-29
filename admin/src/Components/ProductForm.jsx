import React, { useEffect, useState } from "react";
import ReactSelect from "react-select";
import ProductAction, { ACTION_TYPES } from "../Models/ProductAction";
import CheckboxInput from "./CheckboxInput";
import DateTimeInput from "./DateTimeInput";
import SelectInput from "./SelectInput";
import TextInput from "./TextInput";
import Textarea from "./Textarea";

// Return list of available actions types based on selected ones
const filterAvailableActions = (actions) => {
    return ACTION_TYPES.filter(
        (type) => !actions.some((action) => type === action.action_type),
    );
};

const filterSelectedActionType = (selectedActionType, availableActionTypes) => {
    if (availableActionTypes.length === 0) return null;
    if (selectedActionType && availableActionTypes.includes(selectedActionType))
        return selectedActionType;
    return availableActionTypes[0];
};

const ProductForm = ({ product, onDelete, onSave }) => {
    const [actions, setActions] = useState([]);
    const [availableActionTypes, setAvailableActionTypes] = useState([]);
    const [selectedActionType, setSelectedActionType] = useState(null);
    const [saveDisabled, setSaveDisabled] = useState(true);

    useEffect(() => {
        const handleProductChange = () => {
            const newActions = product.actions;
            const newAvailableActionTypes = filterAvailableActions(newActions);
            const action = filterSelectedActionType(
                selectedActionType,
                newAvailableActionTypes,
            );

            setActions(newActions);
            setAvailableActionTypes(newAvailableActionTypes);
            setSelectedActionType(action);
            setSaveDisabled(!product.canSave());
        };

        const unsubscribe = product.subscribe(handleProductChange);
        handleProductChange();

        return () => {
            unsubscribe();
        };
    }, [product, selectedActionType]);

    const handleAddAction = () => {
        if (selectedActionType) {
            product.addAction(
                new ProductAction({ action_type: selectedActionType }),
            );
        }
    };

    const handleRemoveAction = (action) => {
        product.removeAction(action);
    };

    const renderAction = (action) => (
        <div key={action.action_type} className="form-row uk-grid">
            <div className="uk-with-1-6">{action.action_type}</div>
            <div className="uk-with-1-6">
                <strong>Värde</strong>
            </div>
            <div className="uk-with-3-6">
                <TextInput
                    model={action}
                    label={false}
                    formrow={false}
                    name={"value"}
                />
            </div>
            <div className="uk-with-1-6">
                <a
                    className="uk-button uk-button-danger"
                    onClick={() => handleRemoveAction(action)}
                >
                    <i className="uk-icon-trash-o" />
                </a>
            </div>
        </div>
    );

    const imageSrc = (o) => `data:${o.type};base64, ` + o.data;

    return (
        <div className="uk-margin-top">
            <form
                className="uk-form uk-form-stacked"
                onSubmit={() => {
                    onSave();
                    return false;
                }}
            >
                <fieldset className="uk-margin-top">
                    <legend>
                        <i className="uk-icon-shopping-cart" /> Produkt
                    </legend>
                    <TextInput
                        model={product}
                        name="name"
                        title="Produktnamn"
                    />
                    <TextInput
                        model={product}
                        name="product_metadata"
                        title="Metadata"
                    />
                    <SelectInput
                        model={product}
                        name="category_id"
                        title="Kategori"
                        getLabel={(o) => o.name}
                        getValue={(o) => o.id}
                        dataSource={"/webshop/category"}
                    />
                    <Textarea
                        model={product}
                        name="description"
                        title="Beskrivning"
                        rows="4"
                    />
                    <TextInput model={product} name="unit" title="Enhet" />
                    <TextInput
                        model={product}
                        name="price"
                        title="Pris (SEK)"
                        type="number"
                    />
                    <TextInput
                        model={product}
                        name="smallest_multiple"
                        title="Multipel "
                        type="number"
                    />
                    <SelectInput
                        nullOption={{ id: 0 }}
                        model={product}
                        name="image_id"
                        title="Bild"
                        getLabel={(o) => (
                            <div style={{ height: "40px", width: "40px" }}>
                                {o.id ? (
                                    <img
                                        src={imageSrc(o)}
                                        style={{
                                            verticalAlign: "middle",
                                            height: "100%",
                                        }}
                                        alt={o.name}
                                    />
                                ) : (
                                    ""
                                )}
                            </div>
                        )}
                        getValue={(o) => o.id}
                        dataSource={"/webshop/product_image"}
                    />
                </fieldset>
                <fieldset className="uk-margin-top">
                    <legend>
                        <i className="uk-icon-magic" /> Åtgärder
                    </legend>
                    <div>{actions.map(renderAction)}</div>
                    {availableActionTypes.length > 0 && (
                        <div>
                            <ReactSelect
                                className="uk-width-3-5 uk-float-left"
                                value={{
                                    value: selectedActionType,
                                    label: selectedActionType,
                                }}
                                options={availableActionTypes.map((a) => ({
                                    value: a,
                                    label: a,
                                }))}
                                onChange={(o) => setSelectedActionType(o.value)}
                            />
                            <button
                                type="button"
                                className="uk-button uk-button-success uk-float-right"
                                onClick={handleAddAction}
                            >
                                <i className="uk-icon-plus" /> Lägg till åtgärd
                            </button>
                        </div>
                    )}
                </fieldset>
                <fieldset className="uk-margin-top">
                    <legend>
                        <i className="uk-icon-filter" /> Filter
                    </legend>
                    <SelectInput
                        model={product}
                        name="filter"
                        title="Filter"
                        getLabel={(o) => o.name}
                        getValue={(o) => o.id}
                        options={[
                            { id: "", name: "No filter" },
                            {
                                id: "start_package",
                                name: "Purchasable only for new/inactive members (starter pack)",
                            },
                            {
                                id: "labaccess_non_subscription_purchase",
                                name: "Purchasable only if makerspace access subscription is inactive",
                            },
                            {
                                id: "membership_non_subscription_purchase",
                                name: "Purchasable only if base membership subscription is inactive",
                            },
                        ]}
                    />
                </fieldset>
                <fieldset className="uk-margin-top">
                    <legend>
                        <i className="uk-icon-tag" /> Metadata
                    </legend>
                    <CheckboxInput model={product} name="show" title="Synlig" />
                    {product.id && (
                        <>
                            <DateTimeInput
                                model={product}
                                name="created_at"
                                title="Skapad"
                            />
                            <DateTimeInput
                                model={product}
                                name="updated_at"
                                title="Uppdaterad"
                            />
                        </>
                    )}
                </fieldset>
                <fieldset className="uk-margin-top">
                    {product.id && (
                        <a
                            className="uk-button uk-button-danger uk-float-left"
                            onClick={onDelete}
                        >
                            <i className="uk-icon-trash" /> Ta bort produkt
                        </a>
                    )}
                    <button
                        disabled={saveDisabled}
                        className="uk-button uk-button-success uk-float-right"
                    >
                        <i className="uk-icon-save" />{" "}
                        {product.id ? "Spara" : "Skapa"}
                    </button>
                </fieldset>
            </form>
        </div>
    );
};

export default ProductForm;
