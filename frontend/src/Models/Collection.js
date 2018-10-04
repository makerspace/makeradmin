import {get, post} from "../gateway";
import * as _ from "underscore";


// Handle collection of a model class. Support stateful interaction with server.
//
// type: type of model that this is a collection of
// pageSize: size of pages when pagination is enabled (0 = infinite = pagination turned off).
// url: override url, useful for collection of grops on member for example
// expand: expand to include related model in request
// idListName: used for add and remove if collection supports it by pushing id list to to <url>/remove or <url>/add,
//             this could be simpler if server handled removes in a better way
export default class Collection {
    constructor({type, pageSize = 25, expand = null, filter = {}, sort = {}, url=null, idListName=null}) {
        this.type = type;
        this.pageSize = pageSize;
        this.url = url || type.model.root;
        this.idListName = idListName;
        
        this.items = null;
        this.page = {index: 1, count: 1};
        this.sort = sort;
        this.filter = filter;
        this.expand = expand;

        this.subscribers = {};
        this.subscriberId = 0;
        
        this.fetch();
    }
    
    // Subscribe to data from server {items, page}, returns function for unsubscribing.
    subscribe(callback) {
        const id = this.subscriberId++;
        this.subscribers[id] = callback;
        if (this.items) {
            callback({items: this.items, page: this.page});
        }
        return () => delete this.subscribers[id];
    }

    // Update sort order, key is one of model attributes, order is up/asc or down/desc.
    updateSort({key, order = 'down'}) {
        this.sort = {key, order: {up: 'asc', asc: 'asc', down: 'desc', desc: 'desc'}[order]};
        this.fetch();
    }
    
    // Update filter, filter keys are model attributes, values are substrings.
    updateFilter(filter) {
        this.filter = filter;
        this.fetch();
    }
    
    // Change current page index (1-indexed).
    updatePage(index) {
        this.page.index = Math.min(index, this.page.count);
        this.fetch();
    }
    
    // Remove an item from this collection.
    remove(item) {
        if (!this.idListName) {
            throw new Error(`Container for ${this.type.constructor.name} does not support remove.`);
        }
        
        return post({url: this.url + "/remove", data: {[this.idListName]: [item.id]}, expectedDataStatus: null})
            .then(() => this.fetch());
    }

    // Add an item to this collection.
    add(item) {
        if (!this.idListName) {
            throw new Error(`Container for ${this.type.constructor.name} does not support add.`);
        }

        return post({url: this.url + "/add", data: {[this.idListName]: [item.id]}, expectedDataStatus: null})
            .then(() => this.fetch());
    }

    fetch() {
        let params = {};
        
        if (this.pageSize !== 0) {
            params.page = this.page.index;
            params.per_page = this.pageSize;
        }
        
        if (!_.isEmpty(this.sort)) {
            params.sort_by = this.sort.key || '';
            params.sort_order = this.sort.order || '';
        }
        
        if (this.expand) {
            params.expand = this.expand;
        }
        
        _.each(this.filter, (v, k) => {
            params[k] = v;
        });
        
        return get({url: this.url, params}).then(data => {
            if (!data) return;
            this.page.count = data.last_page;
            this.page.index = Math.min(this.page.count, this.page.index || 1);
            this.items = data.data.map(m => new this.type(m));
            _.values(this.subscribers).forEach(s => s({items: this.items, page: this.page}));
        });
    }
}