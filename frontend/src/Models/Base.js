import * as _ from "underscore";
import {del} from "../gateway";


export default class Base {
    constructor(data=null) {
        const model = this.constructor.model;
        
        if (data) {
            this.unsaved = {};
            this.saved = Object.assign({}, model.attributes, data);
        }
        else {
            this.unsaved = {};
            this.saved   = Object.assign({}, model.attributes);
        }

        _.keys(model.attributes).forEach(key => {
            Object.defineProperty(this, key, {
                get: () => {
                    let v;
                    
                    v = this.unsaved[key];
                    if (!_.isUndefined(v)) {
                        return v;
                    }
                    
                    v = this.saved[key];
                    if (!_.isUndefined(v)) {
                        return v;
                    }
                    
                    return model.attributes[v];
                },
                set: (v) => {
                    if (v === this.saved[key]) {
                        delete this.unsaved[key];
                    }
                    else {
                        this.unsaved[key] = v;
                    }
                }
                
            });
        });

        Object.defineProperty(this, 'id', {get: () => this.saved[model.id]});
    }
    
    reset() {
        this.unsaved = Object.assign({}, this.saved);
    }
    
    remove() {
        if (!this.id) {
            return Promise.resolve(null);
        }
        
        return del({url: this.constructor.model.root + '/' + this.id});
    }
    
    isUnsaved() {
        return !this.id || this.isDirty();
    }
    
    isDirty(key) {
        if (!key) {
            return !_.isEmpty(this.unsaved);
        }
        return !_.isUndefined(this.unsaved[key]);
    }
    
    removeConfirmMessage() {
        throw new Error(`removeConfirmMessage not implemented in ${this.constructor.name}`);
    }
}
