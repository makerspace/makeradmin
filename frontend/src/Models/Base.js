import * as _ from "underscore";
import {del, get, put, post} from "../gateway";
import {deepcopy} from "../utils";


export default class Base {
    constructor(data=null) {
        this.subscribers = {};
        this.subscriberId = 0;
        
        this.reset(data);

        const model = this.constructor.model;
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
                    if (_.isEqual(v, this.saved[key])) {
                        delete this.unsaved[key];
                    }
                    else {
                        this.unsaved[key] = v;
                    }
                    this.notify();
                }
                
            });
        });

        Object.defineProperty(this, 'id', {get: () => this.saved[model.id]});
    }
    
    // Subscribe to changes, returns function for unsubscribing.
    subscribe(callback) {
        const id = this.subscriberId++;
        this.subscribers[id] = callback;
        callback();
        return () => delete this.subscribers[id];
    }
    
    // Notify subscribers that something changed.
    notify() {
        _.values(this.subscribers).forEach(s => s());
    }

    // Reset to empty/data state.
    reset(data) {
        const model = this.constructor.model;
        if (data) {
            this.unsaved = {};
            this.saved = Object.assign(deepcopy(model.attributes), data);
        }
        else {
            this.unsaved = {};
            this.saved   = deepcopy(model.attributes);
        }
        this.notify();
    }
    
    // Delete this entity, returns promise.
    del() {
        if (!this.id) {
            return Promise.resolve(null);
        }
        
        return del({url: this.constructor.model.root + '/' + this.id});
    }

    // Refresh data from server, requires id in data, returns promise.
    refresh() {
        if (!this.id) {
            throw new Error("Refresh requires id.");
        }
        
        return get({url: this.constructor.model.root + '/' + this.id}).then(d => {
            this.saved = d.data;
            this.unsaved = {};
            this.notify();
        });
    }
    
    // Save or create, returns promise.
    save() {
        const data = Object.assign({}, this.saved, this.unsaved);

        if (this.id) {
            return put({url: this.constructor.model.root + '/' + this.id, data}).then(d => {
                this.saved = d.data;
                this.unsaved = {};
                this.notify();
            });
        }
    
        return post({url: this.constructor.model.root, data}).then(d => {
            this.saved = d.data;
            this.unsaved = {};
            this.notify();
        });
    }
    
    // Return a new shallow copy of object with id property set to 0.
    copy() {
        const copy = new this.constructor();
        copy.unsaved = Object.assign({}, this.saved, this.unsaved, {[this.constructor.model.id]: 0});
        return copy;
    }
    
    // Returns true if unsaved.
    isUnsaved() {
        return !this.id || this.isDirty();
    }
    
    // Returns true if any field changed.
    isDirty(key) {
        if (!key) {
            return !_.isEmpty(this.unsaved);
        }
        return !_.isUndefined(this.unsaved[key]);
    }
    
    // Return true if save is a good idea given the internal state.
    canSave() {
        return this.isDirty();
    }
    
    // Return message for delete confirmation.
    deleteConfirmMessage() {
        throw new Error(`deleteConfirmMessage not implemented in ${this.constructor.name}`);
    }
    
    // Create and empty model with known id and refresh it, returns model.
    static get(id) {
        const model = new this({[this.model.id]: id});
        model.refresh();
        return model;
    }
}
