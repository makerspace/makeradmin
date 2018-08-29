import { get } from "../gateway";
import * as _ from "underscore";


// Handle collection of a model class. Support stateful interaction with server.
//
// type: type of model that this is a collection of
// onUpdate: callback data is received from server
// pageSize: size of pages when pagination is enabled (0 = infinite = pagination turned off).
export default class Collection {
    constructor({type, onUpdate, pageSize = 25}) {
        this.type = type;
        this.onUpdate = onUpdate;
        this.pageSize = pageSize;
        this.pageIndex = 0;
        this.pageCount = 1;
        
        this.sort = {};
        this.filter = {};
        
        this.fetch();
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
    
    fetch() {
        let params = {
        };
        
        if (this.pageSize !== 0) {
            params.page = this.pageIndex;
            params.per_page = this.pageSize;
        }
        
        if (!_.isEmpty(this.sort)) {
            params.sort_by = this.sort.key || '';
            params.sort_order = this.sort.order || '';
        }
        
        _.each(this.filter, (v, k) => {
            params[k] = v;
        });
        
        get({
            url: this.type.model.root,
            params,
            success: data => {
                if (!data) {
                    this.onUpdate([]);
                }
                else {
                    // TODO this.onUpdate(data.data.map(item => new this.type(item)));
                    this.onUpdate(data.data);
                }
            }
        });
    }
}