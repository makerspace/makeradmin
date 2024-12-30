/**
 * @jest-environment jsdom
 */

/* eslint-env jest */
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
