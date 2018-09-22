import Base from './Base';
import ProductAction from "./ProductAction";
import {get} from "../gateway";

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
        return `Are you sure you want to product ${this.name}?`;
    }
    
    del() {
        return Promise.all(this.savedActions.map(a => a.del())).then(super.del());
    }
    
    save() {
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
        this.notify();
    }
    
    removeAction(action) {
        if (!this.unsavedActions) {
            this.unsavedActions = this.savedActions.map(a => a.copy());
        }
        this.unsavedActions = this.unsavedActions.filter(a => a.action_id !== action.action_id);
        this.notify();
    }
    
    refreshRelated() {
        return get({url: ProductAction.model.root, params: {product_id: this.id}})
            .then(({data}) => {
                this.savedActions = data.map(d => new ProductAction(d));
                this.unsavedActions = null;
                this.notify();
            });
    }
    
    static getWithRelated(id) {
        const model = this.get(id);
        model.refreshRelated();
        return model;
    }
}


Product.model = {
    id: "id",
    root: "/webshop/product",
    attributes: {
        created_at: null,
        updated_at: null,
        name: "",
        description: "",
        category_id: 0,
        price: 0,
        unit: "",
        smallest_multiple: 1,
        filter: null,
    },
};
