import { ComponentChildren } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";
import Cart from "./cart";
import { logout } from "./common";
import { useTranslation } from "./i18n";
import { ProductData } from "./payment_common";

const NavItem = ({
    url,
    icon,
    children,
}: {
    url: string;
    icon: string;
    children: ComponentChildren;
}) => {
    let path = location.pathname.trim();
    if (path.endsWith("/")) {
        path = path.substring(0, path.length - 1);
    }

    return (
        <li className={url === path ? "active" : ""}>
            <a href={url}>
                <span uk-icon={icon}></span> {children}
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
                    <NavItem url="/member" icon="user">
                        {t("member")}
                    </NavItem>
                    <NavItem url="/shop" icon="cart">
                        {t("shop")}
                    </NavItem>
                    {(path === "/shop" || path === "/shop/cart") &&
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
                                                href={`/shop/#category${category.id}`}
                                                uk-scroll={path === "/shop"}
                                            >
                                                <span uk-icon="tag"></span>{" "}
                                                {category.name}
                                            </a>
                                        </li>
                                    ))}
                                <NavItem url="/shop/cart" icon="cart">
                                    {t("cart")} (
                                    {Cart.formatCurrency(
                                        cart.cart.sum(cart.productData.id2item),
                                    )}
                                    )
                                </NavItem>
                            </ul>
                        )}
                    <NavItem url="/shop/member/history" icon="history">
                        {t("purchase_history")}
                    </NavItem>
                    <NavItem url="/shop/member/courses" icon="star">
                        {t("courses")}
                    </NavItem>
                    <NavItem url="http://wiki.makerspace.se" icon="world">
                        {t("wiki")}
                    </NavItem>
                    <NavItem url="/shop/member/licenses" icon="tag">
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
                            <a href="/shop/cart">
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
