import React from "react";
import CollectionTable from "../Components/CollectionTable";
import TextInput from "../Components/TextInput";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import Category from "../Models/ProductCategory";

class CategoryList extends CollectionNavigation {
    constructor(props) {
        super(props);
        const { search, page } = this.state;
        this.collection = new Collection({ type: Category, search, page });
        this.state = { saveEnabled: false };
        this.category = new Category();
    }

    componentDidMount() {
        const category = this.category;
        this.unsubscribe = category.subscribe(() =>
            this.setState({ saveEnabled: category.canSave() }),
        );
    }

    componentWillUnmount() {
        this.unsubscribe();
    }

    createCategory() {
        this.category.save().then(() => {
            this.category.reset();
            this.collection.fetch();
        });
    }

    render() {
        const { saveEnabled } = this.state;

        return (
            <div>
                <div className="uk-margin-top">
                    <h2>Kategorier</h2>
                    <p>
                        På denna sida ser du en lista på samtliga
                        produktkategorier som finns.
                    </p>
                </div>

                <div className="uk-margin-top uk-form">
                    <div className="meep">
                        <form
                            className="uk-form"
                            onSubmit={(e) => {
                                e.preventDefault();
                                this.createCategory();
                                return false;
                            }}
                        >
                            <div className="uk-grid">
                                <div className="uk-width-1-1">
                                    <TextInput
                                        model={this.category}
                                        tabIndex="1"
                                        name="name"
                                        title="Namn"
                                        placeholder="Namn för ny kategori"
                                    />

                                    <div className="form-row uk-margin-top">
                                        <div className="uk-form-controls">
                                            <button
                                                className="uk-button uk-button-primary uk-float-right"
                                                disabled={!saveEnabled}
                                            >
                                                <i className="uk-icon-save" />{" "}
                                                Skapa kategori
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>

                <div className="uk-margin-top">
                    <CollectionTable
                        className="uk-margin-top"
                        collection={this.collection}
                        emptyMessage="Inga produktkategorier"
                        columns={[{ title: "Namn" }, { title: "" }]}
                        rowComponent={({ item, deleteItem }) => (
                            <tr>
                                <td>{item.name}</td>
                                <td>
                                    <a
                                        onClick={() => deleteItem(item)}
                                        className="removebutton"
                                    >
                                        <i className="uk-icon-trash" />
                                    </a>
                                </td>
                            </tr>
                        )}
                        onPageNav={this.onPageNav}
                    />
                </div>
            </div>
        );
    }
}

export default CategoryList;
