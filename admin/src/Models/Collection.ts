import * as _ from "underscore";
import { get, post } from "../gateway";

// Handle collection of a model class. Support stateful interaction with server.
//
// type: type of model that this is a collection of
// pageSize: size of pages when pagination is enabled (0 = infinite = pagination turned off).
// url: override url, useful for collection of grops on member for example
// expand: expand to include related model in request
// idListName: used for add and remove if collection supports it by pushing id list to to <url>/remove or <url>/add,
//             this could be simpler if server handled removes in a better way
export default class Collection<T extends { saved: { [key: string]: any } }> {
    type: { new (data?: T | null): T; model: { root: string } };
    pageSize: number;
    url: string;
    idListName: string | null;

    items: T[] | null;
    page: { index: number; count: number };
    sort: { key?: string; order?: string };
    search: string | null;
    expand: string | null;

    subscribers: {
        [key: number]: (data: {
            items: any[];
            page: { index: number; count: number };
        }) => void;
    };
    subscriberId: number;

    filter_out_key: string | null;
    filter_out_value: string | null;

    includeDeleted: boolean;

    constructor({
        type,
        pageSize = 25,
        expand = null,
        sort = {},
        url = null,
        idListName = null,
        search = null,
        page = 1,
        filter_out_key = null,
        filter_out_value = null,
        includeDeleted = false,
    }: {
        type: { new (data?: T | null): T; model: { root: string } };
        pageSize?: number;
        expand?: string | null;
        sort?: { key?: string; order?: string };
        url?: string | null;
        idListName?: string | null;
        search?: string | null;
        page?: number;
        filter_out_key?: string | null;
        filter_out_value?: string | null;
        includeDeleted?: boolean;
    }) {
        this.type = type;
        this.pageSize = pageSize;
        this.url = url || type.model.root;
        this.idListName = idListName;

        this.items = null;
        this.page = { index: page, count: 1 };
        this.sort = sort;
        this.search = search;
        this.expand = expand;

        this.subscribers = {};
        this.subscriberId = 0;

        this.filter_out_key = filter_out_key;
        this.filter_out_value = filter_out_value;

        this.includeDeleted = !!includeDeleted;

        this.fetch();
    }

    // Subscribe to data from server {items, page}, returns function for unsubscribing.
    subscribe(
        callback: (data: {
            items: any[];
            page: { index: number; count: number };
        }) => void,
    ) {
        const id = this.subscriberId++;
        this.subscribers[id] = callback;
        if (this.items) {
            callback({ items: this.items, page: this.page });
        }
        return () => delete this.subscribers[id];
    }

    // Update sort order, key is one of model attributes, order is up/asc or down/desc.
    updateSort({
        key,
        order = "down",
    }: {
        key: string;
        order: "up" | "asc" | "down" | "desc";
    }) {
        this.sort = {
            key,
            order: { up: "asc", asc: "asc", down: "desc", desc: "desc" }[order],
        };
        this.fetch();
    }

    // Update filter, filter keys are model attributes, values are strings.
    updateSearch(terms: string) {
        this.search = terms;
        this.fetch();
    }

    // Change current page index (1-indexed).
    updatePage(index: number) {
        this.page.index = Math.min(index, this.page.count) || 1;
        this.fetch();
    }

    // Remove an item from this collection.
    remove(item: { id: number }) {
        if (!this.idListName) {
            throw new Error(
                `Container for ${this.type.constructor.name} does not support remove.`,
            );
        }

        return post({
            url: this.url + "/remove",
            data: { [this.idListName]: [item.id] },
            expectedDataStatus: null,
        }).then(() => this.fetch());
    }

    // Add an item to this collection.
    add(item: { id: number }) {
        if (!this.idListName) {
            throw new Error(
                `Container for ${this.type.constructor.name} does not support add.`,
            );
        }

        return post({
            url: this.url + "/add",
            data: { [this.idListName]: [item.id] },
            expectedDataStatus: null,
        }).then(() => this.fetch());
    }

    create_fetch_parameters() {
        let params: {
            page?: number;
            page_size?: number;
            include_deleted?: boolean;
            sort_by?: string;
            sort_order?: string;
            expand?: string;
            search?: string;
        } = {};

        if (this.pageSize !== 0) {
            params.page = this.page.index;
        }
        params.page_size = this.pageSize;
        if (this.includeDeleted) {
            params.include_deleted = this.includeDeleted;
        }

        if (!_.isEmpty(this.sort)) {
            params.sort_by = this.sort.key || "";
            params.sort_order = this.sort.order || "";
        }

        if (this.expand) {
            params.expand = this.expand;
        }

        if (this.search) {
            params.search = this.search.trim();
        }
        return params;
    }

    fetch() {
        return get({
            url: this.url,
            params: this.create_fetch_parameters(),
        }).then((data) => {
            if (!data) return;
            this.page.count = data.last_page;
            this.page.index = Math.min(this.page.count, this.page.index) || 1;
            this.items = data.data.map((m: any) => new this.type(m));
            if (this.filter_out_value && this.filter_out_key) {
                this.items = this.items!.filter(
                    (p) =>
                        p.saved[this.filter_out_key!] !== this.filter_out_value,
                );
            }
            _.values(this.subscribers).forEach((s) =>
                s({ items: this.items!, page: this.page }),
            );
        });
    }
}
