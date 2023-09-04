import Base from './Base';
import ProductAction from "./ProductAction";
import {get} from "../gateway";
import UIkit from 'uikit';

export default class Product extends Base {
    
    constructor(data) {
        super(data);
        this.savedActions = [];
        this.unsavedActions = null;
        
        Object.defineProperty(this, 'actions', {get: () => this.unsavedActions || this.savedActions});
    }

    isDirty(key) {
        if (key) {
            return super.isDirty(key);
        }
        
        return super.isDirty() || this.unsavedActions || this.savedActions.some(a => a.isDirty());
    }
    
    canSave() {
        return this.isDirty()
               && this.category_id
               && this.name.length
               && this.price;
    }
    
    deleteConfirmMessage() {
        return `Are you sure you want to delete product ${this.name}?`;
    }
    
    del() {
        return Promise.all(this.savedActions.map(a => a.del())).then(super.del());
    }
    
    save() {
        if (this.image_id === 0) {
            this.image_id = null;
        }
        return super.save()
                    .then(() => {
                        const promises = [];
                        if (this.unsavedActions) {
                            this.unsavedActions.forEach(a => a.product_id = this.id);
                            promises.push(...this.unsavedActions.map(a => a.save()));
                            promises.push(...this.savedActions.map(a => a.del()));
                        }
                        else {
                            promises.push(...this.savedActions.map(a => a.save()));
                        }
                        return Promise.all(promises);
                    })
                    // If something goes wrong here, we will likely end up in an inconsistent state, so just refresh and
                    // hope for the best.
                    .catch(e => this.refreshRelated().then(() => {throw e;}))
                    // Since there are possible race conditions here as well, just refresh in the end.
                    .then(() => this.refreshRelated());
    }
    
    addAction(action) {
        if (action.id) {
            throw new Error("Adding of saved ProductAction is unsupported.");
        }
        if (!this.unsavedActions) {
            this.unsavedActions = this.savedActions.map(a => a.copy());
        }
        this.unsavedActions.push(action);
        action.subscribe(() => this.notify());
        this.notify();
    }
    
    removeAction(action) {
        if (!this.unsavedActions) {
            this.unsavedActions = this.savedActions.map(a => a.copy());
        }
        this.unsavedActions = this.unsavedActions.filter(a => a.action_type !== action.action_type);
        this.notify();
    }
    
    refreshRelated() {
        return get({url: `/webshop/product/${this.id}/actions`})
            .then(({data}) => {
                this.savedActions = data.map(d => new ProductAction(d));
                this.savedActions.forEach(action => action.subscribe(() => this.notify()));
                this.unsavedActions = null;
                this.notify();
            });
    }
    
    static getWithRelated(id) {
        const model = this.get(id);
        model.refreshRelated();
        return model;
    }
    
    deserialize(x) {
        // We store the product metadata as a json object in the database,
        // but we want to edit it as a string in the UI.
        // This is perhaps not the prettiest solution, but it works.
        x['product_metadata'] = JSON.stringify(x['product_metadata']);
        return x;
    }

    serialize(x) {
        try {
            x['product_metadata'] = JSON.parse(x['product_metadata']);
        } catch (e) {
            // In case the user supplied invalid json, we ignore the update.
            UIkit.modal.alert("Invalid product metadata json.");
            x['product_metadata'] = JSON.parse(this.saved['product_metadata']);
        }
        return x;
    }
}


Product.model = {
    id: "id",
    root: "/webshop/product",
    attributes: {
        created_at: null,
        updated_at: null,
        product_metadata: "{}",
        name: "",
        description: "",
        category_id: 0,
        price: 0,
        unit: "",
        smallest_multiple: 1,
        filter: null,
        show: true,
        image_id: null,
    },
};
