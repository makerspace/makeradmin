import { useState } from "react";
import AsyncSelect from "react-select/async";
import { Product } from "Statistics/types";
import Icon from "../Components/icons";
import { get, post } from "../gateway";
import { showError, showSuccess } from "../message";

type ProductOption = {
    value: number;
    label: string;
    product: Product;
};

type MemberOption = {
    id: number;
    value: string;
    label: string;
    member: {
        member_id: number;
        firstname: string;
        lastname?: string;
        member_number: number;
    };
};

const GiftProduct = () => {
    const [selectedProduct, setSelectedProduct] =
        useState<ProductOption | null>(null);
    const [giftCount, setGiftCount] = useState<string>("");
    const [selectedMembers, setSelectedMembers] = useState<MemberOption[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const loadProductOptions = (
        inputValue: string,
        callback: (options: ProductOption[]) => void,
    ) => {
        if (inputValue.length < 2) {
            callback([]);
            return;
        }

        get({
            url: "/webshop/product",
            params: {
                search: inputValue,
                sort_by: "name",
                sort_order: "asc",
                page_size: 50,
            },
        })
            .then(({ data: products }) => {
                const options: ProductOption[] = products.map(
                    (product: any) => ({
                        value: product.id,
                        label: `${product.name} - ${product.price} SEK/${product.unit}`,
                        product: product,
                    }),
                );
                callback(options);
            })
            .catch((error: any) => {
                console.error("Error loading products:", error);
                callback([]);
            });
    };

    const loadMemberOptions = (
        inputValue: string,
        callback: (options: MemberOption[]) => void,
    ) => {
        if (inputValue.length < 2) {
            callback([]);
            return;
        }

        // Check if input looks like member numbers (comma/space separated numbers)
        const intListMatch = inputValue.match(/^\s*(\d\d\d\d+[\s,]*)+\s*$/);
        if (intListMatch) {
            const ids = inputValue
                .split(/[\s,]+/)
                .map((v) => parseInt(v, 10))
                .filter((v) => !isNaN(v));

            if (ids.length > 0) {
                get({
                    url: "/membership/member",
                    params: {
                        search: ids.join("|"),
                        search_column: "member_number",
                        sort_by: "member_number",
                        sort_order: "asc",
                        page_size: 1000,
                        regex: true,
                    },
                })
                    .then(({ data: members }) => {
                        const options: MemberOption[] = members
                            .filter(
                                (m: any) =>
                                    !selectedMembers.some(
                                        (sm) => sm.id === m.member_id,
                                    ),
                            )
                            .map((member: any) => ({
                                id: member.member_id,
                                value: `member${member.member_id}`,
                                label: `${member.firstname} ${member.lastname || ""} (#${member.member_number})`,
                                member: member,
                            }));
                        callback(options);
                    })
                    .catch((error: any) => {
                        console.error("Error loading members:", error);
                        callback([]);
                    });
                return;
            }
        }

        // Search by name
        get({
            url: "/membership/member",
            params: {
                search: inputValue,
                sort_by: "firstname",
                sort_order: "asc",
                page_size: 50,
            },
        })
            .then(({ data: members }) => {
                const options: MemberOption[] = members
                    .filter(
                        (m: any) =>
                            !selectedMembers.some(
                                (sm) => sm.id === m.member_id,
                            ),
                    )
                    .map((member: any) => ({
                        id: member.member_id,
                        value: `member${member.member_id}`,
                        label: `${member.firstname} ${member.lastname || ""} (#${member.member_number})`,
                        member: member,
                    }));
                callback(options);
            })
            .catch((error: any) => {
                console.error("Error loading members:", error);
                callback([]);
            });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!selectedProduct) {
            showError("Please select a product to gift.");
            return;
        }

        if (!giftCount || parseInt(giftCount) <= 0) {
            showError("Please enter a valid gift count.");
            return;
        }

        if (selectedMembers.length === 0) {
            showError("Please select at least one member to gift to.");
            return;
        }

        setIsSubmitting(true);

        try {
            const giftData = {
                product_id: selectedProduct.value,
                count: giftCount,
                member_ids: selectedMembers.map((member) => member.id),
            };

            await post({
                url: "/webshop/gift-product",
                data: giftData,
                expectedDataStatus: "ok",
            });

            showSuccess(
                `Successfully gifted ${giftCount}x ${selectedProduct.label} to ${selectedMembers.length} member(s) with a total donation value of ${parseInt(giftCount) * parseFloat(selectedProduct.product.price)} SEK.`,
            );

            // Reset form
            setSelectedProduct(null);
            setGiftCount("");
            setSelectedMembers([]);
        } catch (error: any) {
            showError("Failed to process gift transaction. Please try again.");
            console.error("Gift transaction error:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const isFormValid =
        selectedProduct &&
        giftCount &&
        parseFloat(giftCount) > 0 &&
        selectedMembers.length > 0;

    return (
        <div>
            <h2>Gift Product to Members</h2>
            <p className="uk-text-muted">
                The recipients will receive the product with no payment
                required.
            </p>

            <form className="uk-form-horizontal" onSubmit={handleSubmit}>
                <div className="form-row">
                    <label className="uk-form-label" htmlFor="product">
                        Product
                    </label>
                    <div className="uk-form-controls">
                        <AsyncSelect
                            name="product"
                            placeholder="Search for product to gift..."
                            getOptionValue={(option: ProductOption) =>
                                option.value.toString()
                            }
                            getOptionLabel={(option: ProductOption) =>
                                option.label
                            }
                            loadOptions={loadProductOptions}
                            value={selectedProduct}
                            onChange={setSelectedProduct}
                            isClearable
                        />
                    </div>
                </div>

                <div className="form-row uk-margin-top">
                    <label className="uk-form-label" htmlFor="gift-count">
                        Product Count
                    </label>
                    <div className="uk-form-controls">
                        <input
                            type="number"
                            className="uk-input"
                            id="gift-count"
                            value={giftCount}
                            onChange={(e) => setGiftCount(e.target.value)}
                            placeholder="Enter product count..."
                            min="1"
                        />
                    </div>
                </div>

                <div className="form-row uk-margin-top">
                    <label className="uk-form-label" htmlFor="recipients">
                        Recipients
                    </label>
                    <div className="uk-form-controls">
                        <AsyncSelect
                            name="recipients"
                            isMulti
                            placeholder="Search for members by name or member number..."
                            getOptionValue={(option: MemberOption) =>
                                option.value
                            }
                            getOptionLabel={(option: MemberOption) =>
                                option.label
                            }
                            loadOptions={loadMemberOptions}
                            value={selectedMembers}
                            onChange={(v) => setSelectedMembers(v.slice())}
                        />
                    </div>
                </div>

                <div className="form-row uk-margin-top">
                    <div className="uk-form-controls">
                        <button
                            className="uk-button uk-button-primary"
                            disabled={!isFormValid || isSubmitting}
                            type="submit"
                        >
                            <Icon icon="birthdaycake" />
                            {isSubmitting ? "Processing..." : "Gift Product"}
                        </button>
                    </div>
                </div>

                {selectedProduct && selectedMembers.length > 0 && giftCount && (
                    <div className="uk-alert uk-alert-primary">
                        <h4>Gift Summary:</h4>
                        <p>
                            <strong>Product:</strong> {selectedProduct.label}
                            <br />
                            <strong>Recipients:</strong>{" "}
                            {selectedMembers.length} member(s)
                            <br />
                            <strong>Gift count:</strong> {giftCount}{" "}
                            {selectedProduct.product.unit}
                            <br />
                            <strong>Gift value per member:</strong>{" "}
                            {selectedProduct.product
                                ? parseInt(giftCount) *
                                  parseFloat(selectedProduct.product.price)
                                : "N/A"}{" "}
                            SEK
                        </p>
                    </div>
                )}
            </form>
        </div>
    );
};

export default GiftProduct;
