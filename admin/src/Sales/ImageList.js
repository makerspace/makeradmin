import React from "react";
import CollectionTable from "../Components/CollectionTable";
import Icon from "../Components/icons";
import SearchBox from "../Components/SearchBox";
import Collection from "../Models/Collection";
import CollectionNavigation from "../Models/CollectionNavigation";
import ProductImage from "../Models/ProductImage";

class ImageList extends CollectionNavigation {
    constructor(props) {
        super(props);

        const { page, search } = this.state;
        this.collection = new Collection({ type: ProductImage, search, page });
    }

    upload(event) {
        const { files } = event.target;
        const file = files[0];
        const image = new ProductImage();
        image.name = file.name;

        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            const [prefix, data] = reader.result.split(",", 2);
            const expected = `data:${file.type};base64`;
            if (prefix !== expected) {
                throw Error(
                    `bad data prefix '${prefix}' expected '${expected}', maybe try another browser or image`,
                );
            }
            image.type = file.type;
            image.data = data;
            image.save().then(() => this.collection.fetch());
        };
    }

    render() {
        return (
            <div className="uk-margin-top">
                <h2>Bilder</h2>
                <p className="uk-float-left">
                    På denna sida ser du en lista på samtliga produkter som
                    finns för försäljning.
                </p>
                <form
                    onSubmit={(e) => {
                        e.preventDefault();
                        this.onSubmit();
                    }}
                >
                    <input
                        type="file"
                        id="avatar"
                        name="avatar"
                        accept="image/png, image/jpeg, image/gif"
                        onChange={(e) => this.upload(e)}
                    />
                </form>
                <SearchBox handleChange={this.onSearch} />
                <div className="uk-margin-top">
                    <CollectionTable
                        className="uk-margin-top"
                        collection={this.collection}
                        emptyMessage="Inga bilder"
                        onPageNav={this.onPageNav}
                        columns={[
                            { title: "Namn" },
                            { title: "Typ" },
                            { title: "Bild" },
                            { title: "" },
                        ]}
                        rowComponent={({ item, deleteItem }) => {
                            const src =
                                `data:${item.type};base64, ` + item.data;
                            return (
                                <tr>
                                    <td>{item.name}</td>
                                    <td>{item.type}</td>
                                    <td>
                                        <div
                                            style={{
                                                height: "40px",
                                                width: "40px",
                                            }}
                                        >
                                            <img
                                                src={src}
                                                style={{
                                                    verticalAlign: "middle",
                                                    height: "100%",
                                                }}
                                                alt={item.name}
                                            />
                                        </div>
                                    </td>
                                    <td>
                                        <a
                                            onClick={() => deleteItem(item)}
                                            className="removebutton"
                                        >
                                            <Icon icon="trash" />
                                        </a>
                                    </td>
                                </tr>
                            );
                        }}
                    />
                </div>
            </div>
        );
    }
}

export default ImageList;
