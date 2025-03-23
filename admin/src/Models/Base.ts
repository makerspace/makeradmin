import * as _ from "underscore";
import { del, get, post, put } from "../gateway";
import { deepcopy } from "../utils";

export default class Base<T extends object> {
    id: number | null = null;
    subscribers: { [key: number]: () => void } = {};
    subscriberId: number = 0;
    initializers: { [key: number]: () => void } = {};
    initializerId: number = 0;
    unsaved: { [key: string]: any } = {};
    saved: { [key: string]: any } = {};

    constructor(data: Partial<T> | null = null) {
        this.reset(data);

        const model = (this.constructor as any).model;
        _.keys(model.attributes).forEach((key) => {
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

                    return model.attributes[v as any];
                },
                set: (v) => {
                    if (_.isEqual(v, this.saved[key])) {
                        delete this.unsaved[key];
                    } else {
                        this.unsaved[key] = v;
                    }
                    this.notify();
                },
            });
        });

        Object.defineProperty(this, "id", { get: () => this.saved[model.id] });
    }

    // Subscribe to changes, returns function for unsubscribing.
    subscribe(callback: () => void) {
        const id = this.subscriberId++;
        this.subscribers[id] = callback;
        callback();
        return () => delete this.subscribers[id];
    }

    // Subscribe to initialization when data has been fetched (run only once, then unsubscribed)
    initialization(callback: () => void) {
        const id = this.initializerId++;
        this.initializers[id] = () => {
            callback();
            delete this.initializers[id];
        };
        callback();
    }

    // Notify subscribers that something changed.
    notify() {
        _.values(this.subscribers).forEach((s) => s());
        _.values(this.initializers).forEach((s) => s());
    }

    // Reset to empty/data state.
    reset(raw_data: Partial<T> | null) {
        const model = (this.constructor as any).model;
        if (raw_data) {
            const data = this.deserialize(raw_data as T);
            this.unsaved = {};
            this.saved = Object.assign(deepcopy(model.attributes), data);
        } else {
            this.unsaved = {};
            this.saved = deepcopy(model.attributes);
        }
        this.notify();
    }

    // Delete this entity, returns promise.
    del() {
        if (!this.id) {
            return Promise.resolve(null);
        }

        return del({
            url: (this.constructor as any).model.root + "/" + this.id,
        });
    }

    // Refresh data from server, requires id in data, returns promise.
    refresh() {
        if (!this.id) {
            throw new Error("Refresh requires id.");
        }

        return get({
            url: (this.constructor as any).model.root + "/" + this.id,
        }).then((d) => {
            this.saved = this.deserialize(d.data);
            this.unsaved = {};
            this.notify();
        });
    }

    deserialize(x: any): T {
        return x;
    }

    serialize(x: T) {
        return x;
    }

    // Save or create, returns promise.
    save() {
        const data = this.serialize(
            Object.assign({}, this.saved, this.unsaved) as T,
        );

        if (this.id) {
            return put({
                url: (this.constructor as any).model.root + "/" + this.id,
                data,
            }).then((d) => {
                this.saved = this.deserialize(d.data);
                this.unsaved = {};
                this.notify();
            });
        }

        return post({ url: (this.constructor as any).model.root, data }).then(
            (d) => {
                this.saved = this.deserialize(d.data);
                this.unsaved = {};
                this.notify();
            },
        );
    }

    // Return a new shallow copy of object with id property set to 0.
    copy() {
        const copy = new (this as any).constructor();
        copy.unsaved = Object.assign({}, this.saved, this.unsaved, {
            [(this.constructor as any).model.id]: 0,
        });
        return copy;
    }

    // Returns true if unsaved.
    isUnsaved() {
        return !this.id || this.isDirty();
    }

    // Returns true if any field changed.
    isDirty(key?: string): boolean {
        if (!key) {
            return !_.isEmpty(this.unsaved);
        }
        return !_.isUndefined(this.unsaved[key]);
    }

    // Return true if save is a good idea given the internal state.
    canSave(): boolean {
        return this.isDirty();
    }

    // Return message for delete confirmation.
    deleteConfirmMessage() {
        throw new Error(
            `deleteConfirmMessage not implemented in ${this.constructor.name}`,
        );
    }

    // Create and empty model with known id and refresh it, returns model.
    static get<U extends object>(id: number): Base<U> {
        const model = new this({ [(this as any).model.id]: id });
        model.refresh();
        return model as Base<U>;
    }
}
