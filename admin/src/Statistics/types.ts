export type ProductCategory = {
    id: number;
    name: string;
    items: Product[];
};

export type PriceLevel = "normal" | "low_income_discount";
export type SubscriptionType = "membership" | "labaccess";

export type Product = {
    category_id: number;
    created_at: string;
    deleted_at: string | null;
    updated_at: string;
    description: string;
    display_order: number;
    filter: string;
    id: number;
    image_id: number | null;
    product_metadata: {
        subscription_type?: SubscriptionType;
        special_product_id?: string;
        allowed_price_levels?: PriceLevel[];
    };
    name: string;
    price: string;
    show: boolean;
    smallest_multiple: number;
    unit: string;
};

export type SalesByDate = {
    date: string;
    amount: number;
    count: number;
};

export type SalesResponse = {
    id: number;
    total_amount: number;
    total_count: number;
    by_date: SalesByDate[];
    start_time: string | null;
    end_time: string | null;
    amount_unit: string;
};
