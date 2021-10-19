import React from "react";
import CollectionNavigation from "../Models/CollectionNavigation";
import ProductImage from "../Models/ProductImage";
import Collection from "../Models/Collection";

class ImageList extends CollectionNavigation {

    constructor(props) {
        super(props);
        
        const {page, search} = this.state;
        this.collection = new Collection({type: ProductImage, search, page});
    }
    
    upload(event) {
        const {files} = event.target;
        const file = files[0];
        const image = new ProductImage();
        image.name = file.name;
    
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            const [prefix, data] = reader.result.split(",", 2);
            const expected = `data:${file.type};base64`;
            if (prefix !== expected) {
                throw Error(`bad data prefix '${prefix}' expected '${expected}', maybe try another browser or image`);
            }
            image.type = file.type;
            image.data = data;
            image.save();
        };
        console.info(file);
    }
    
    render() {
        
        return (
            <div className="uk-margin-top">
                <h2>Bilder</h2>
                <p className="uk-float-left">På denna sida ser du en lista på samtliga produkter som finns för försäljning.</p>
                <form onSubmit={e => {e.preventDefault(); this.onSubmit();}}>
                    <input type="file" id="avatar" name="avatar" accept="image/png, image/jpeg, image/gif" onChange={e => this.upload(e)}/>
                </form>
                
             </div>
        );
    }
}

export default ImageList;

// <Link className="uk-button uk-button-primary uk-margin-bottom uk-float-right" to="/sales/product/add"><i className="uk-icon-plus-circle"/> Ladda upp bild</Link>
