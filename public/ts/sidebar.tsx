import { labelExpiredRecently, labelExpiresSoon, UploadedLabel } from "frontend_common";
import { ComponentChildren } from "preact";
import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import Cart from "./cart";
import { logout, UNAUTHORIZED, url } from "./common";
import { useTranslation } from "./i18n";
import { LoadCurrentLabels } from "./member_common";
import { ProductData } from "./payment_common";

const NavItem = ({
    url,
    icon,
    children,
    dot = null,
}: {
    url: string;
    icon: string;
    children: ComponentChildren;
    dot?: "warning" | "danger" | null;
}) => {
    let path = location.pathname.trim();
    if (path.endsWith("/")) {
        path = path.substring(0, path.length - 1);
    }

    return (
        <li className={url === path ? "active" : ""}>
            <a href={url}>
                <span uk-icon={icon}></span> {children}
                {dot !== null && (
                    <span className={`sidebar-dot sidebar-dot-${dot}`}></span>
                )}
            </a>
        </li>
    );
};

export const Sidebar = ({
    cart,
    className = "",
}: {
    cart: { cart: Cart; productData: ProductData } | null;
    className?: string;
}) => {
    const sidebarRef = useRef<HTMLDivElement>(null);
    const [isSidebarScrollable, setIsSidebarScrollable] = useState(false);
    const { t } = useTranslation("sidebar");

    useEffect((): (() => void) => {
        const checkSidebarHeight = () => {
            if (sidebarRef.current) {
                setIsSidebarScrollable(
                    sidebarRef.current.scrollHeight >
                        sidebarRef.current.clientHeight,
                );
            }
        };
        checkSidebarHeight();
        window.addEventListener("resize", checkSidebarHeight);

        return () => {
            window.removeEventListener("resize", checkSidebarHeight);
        };
    }, []);

    const [labels, setLabels] = useState<UploadedLabel[]>([]);

    useEffect(() => {
        LoadCurrentLabels()
            .then(setLabels)
            .catch((e) => {
                if (e.status === UNAUTHORIZED) {
                    // User is just not logged in, ignore
                } else {
                    console.error("Failed to load labels for sidebar", e);
                }
            });
    }, []);

    const labelDot = useMemo(() => {
        if (
            labels.some((label) =>
                labelExpiredRecently(new Date(), label.label, null),
            )
        ) {
            return "danger";
        } else if (
            labels.some((label) => labelExpiresSoon(new Date(), label.label, null))
        ) {
            return "warning";
        } else {
            return null;
        }
    }, [labels]);

    let path = location.pathname.trim();
    if (path.endsWith("/")) {
        path = path.substring(0, path.length - 1);
    }
    return (
        <div
            id="left-sidebar"
            ref={sidebarRef}
            className={isSidebarScrollable ? "scrollable" : ""}
        >
            <div className={`sidebar-fixed-content ${className}`}>
                <img
                    className="makerspace-logo"
                    src={`${window.staticBasePath}/images/logo-transparent-500px-300x210.png`}
                />
                <ul className="uk-nav uk-nav-default">
                    <NavItem url={url("/member")} icon="user">
                        {t("member")}
                    </NavItem>
                    <NavItem url={url("/shop")} icon="cart">
                        {t("shop")}
                    </NavItem>
                    {(path === url("/shop") || path === url("/shop/cart")) &&
                        cart !== null && (
                            <ul id="categories" className="uk-nav-sub">
                                {cart.productData.categories
                                    .filter(
                                        (category) =>
                                            category.items.filter(
                                                (item) => item.show,
                                            ).length > 0,
                                    )
                                    .map((category) => (
                                        <li>
                                            <a
                                                href={url(
                                                    `/shop/#category${category.id}`,
                                                )}
                                                uk-scroll={path === "/shop"}
                                            >
                                                <span uk-icon="tag"></span>{" "}
                                                {category.name}
                                            </a>
                                        </li>
                                    ))}
                                <NavItem url={url("/shop/cart")} icon="cart">
                                    {t("cart")} (
                                    {Cart.formatCurrency(
                                        cart.cart.sum(cart.productData.id2item),
                                    )}
                                    )
                                </NavItem>
                            </ul>
                        )}
                    <NavItem url={url("/shop/member/history")} icon="history">
                        {t("purchase_history")}
                    </NavItem>
                    <NavItem url={url("/member/courses")} icon="star">
                        {t("courses")}
                    </NavItem>
                    <NavItem
                        url={url("/member/labels")}
                        icon="tag"
                        dot={labelDot}
                    >
                        {t("labels")}
                    </NavItem>
                    <NavItem url="http://wiki.makerspace.se" icon="world">
                        {t("wiki")}
                    </NavItem>
                    <NavItem url={url("/member/licenses")} icon="tag">
                        {t("licenses")}
                    </NavItem>
                    <li>
                        <a
                            onClick={(e) => {
                                e.preventDefault();
                                logout();
                            }}
                        >
                            <span uk-icon="sign-out"></span>{" "}
                            {t("common:logOut")}
                        </a>
                    </li>

                    {cart !== null && (
                        <li
                            className={`uk-button uk-button-primary sidebar-buy-btn ${
                                cart.cart.items.length === 0 ? "cart-empty" : ""
                            }`}
                        >
                            <a href={url("/shop/cart")}>
                                <span uk-icon="cart"></span> {t("pay")}
                                <span id="cart-sum">
                                    {Cart.formatCurrency(
                                        cart.cart.sum(cart.productData.id2item),
                                    )}
                                </span>
                            </a>
                        </li>
                    )}
                </ul>
            </div>
        </div>
    );
};
