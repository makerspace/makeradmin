/* eslint-env jest */
import { describe, expect, test } from "@jest/globals";
import { get } from "../../gateway";
import Collection from "../Collection";
jest.mock("../../gateway");

class Group {
    constructor(name) {
        this.name = name;
    }
}

class MockCollection extends Collection {
    constructor(props) {
        super({ type: Group, url: "fakeurl", ...props });
    }
}

beforeEach(() => {
    jest.restoreAllMocks();
});

describe("Collection constructor", () => {
    test("calls fetch when instantiated", () => {
        const fetchMock = jest
            .spyOn(MockCollection.prototype, "fetch")
            .mockImplementation(() => {
                return Promise.resolve({ data: null });
            });

        new MockCollection();

        expect(fetchMock).toHaveBeenCalled();
        fetchMock.mockRestore();
    });
});

describe("Fetch", () => {
    test("uses filtering parameters, if set", () => {
        jest.spyOn(MockCollection.prototype, "fetch").mockImplementation(() => {
            return Promise.resolve({ data: null });
        });

        const collection = new MockCollection({
            pageSize: 10,
            includeDeleted: true,
            sort: { key: "name", order: "desc" },
            expand: "expand",
            search: "search",
        });

        expect(collection.create_fetch_parameters()).toEqual({
            page: 1,
            page_size: 10,
            include_deleted: true,
            sort_by: "name",
            sort_order: "desc",
            expand: "expand",
            search: "search",
        });
    });
});

class FakeDatabase {
    constructor() {
        this.items = [];

        get.mockImplementation(
            (...v) => new Promise((resolve) => resolve(this.getResponse(...v))),
        );
    }

    addItem(item) {
        this.items.push(item);
    }

    getResponse({ url = "", params = {} }) {
        const page_size = params.page_size || 10;
        return {
            data: this.items,
            page: params.page || 1,
            page_size: page_size,
            last_page: Math.ceil(this.items.length / page_size),
        };
    }
}

describe("Subscription", () => {
    test("each function gets notified", async () => {
        const db = new FakeDatabase();
        db.addItem("Group1");

        const collection = new MockCollection();
        collection.fetch();
        const callback1 = jest.fn();

        collection.subscribe(callback1);

        await collection.fetch();

        expect(callback1).toHaveBeenCalled();
    });
});
